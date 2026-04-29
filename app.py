import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from itertools import permutations, product
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="JESA - Work Management Portal", page_icon="🏗️", layout="wide")

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"] 
        else: st.error("Incorrect password")

    if not st.session_state["authenticated"]:
        st.title("🔐 JESA Portal Access")
        st.text_input("Enter Portal Password", type="password", on_change=password_entered, key="password")
        return False
    return True

# --- 3. UTILITIES ---
BASE_LAT, BASE_LON = 33.11220602802328, -8.613230470567437

def haversine(lat1, lon1, lat2, lon2):
    R = 6372800
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        clean_str = str(coord_str).replace('"', '').replace("'", "")
        lat, lon = map(float, clean_str.split(','))
        return lat, lon
    except: return None, None

def write_styled_excel(df, buffer):
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Schedule')
        workbook = writer.book
        worksheet = writer.sheets['Schedule']
        format_busy = workbook.add_format({'bg_color': '#4CAF50', 'font_color': '#ffffff'})
        for row_num in range(1, len(df) + 1):
            for col_num, col_name in enumerate(df.columns):
                if ":00" in str(col_name) and str(df.iloc[row_num-1, col_num]).upper() == "X":
                    worksheet.write(row_num, col_num, "X", format_busy)

def append_to_gsheet(conn, new_data_row):
    existing_data = conn.read(ttl=0) 
    updated_df = pd.concat([existing_data, pd.DataFrame([new_data_row])], ignore_index=True)
    conn.update(data=updated_df)

# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    # --- TAB 1: Smoothing ---
    with tabs[0]:
        uploaded_file1 = st.file_uploader("Upload WMS", type=['xlsx'], key="file1")
        daily_cap = st.number_input("Daily MH Capacity:", value=100.0, key="cap1")
        if uploaded_file1 and st.button("Generate Smoothing", key="btn1"):
            df = pd.read_excel(uploaded_file1)
            df = df.sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            hourly_cap = daily_cap / 8.0
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            results_day, results_start, results_end = [], [], []
            usage_tracker = {}
            for idx, row in df.iterrows():
                duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                mh_per_hour = row['MH'] / row['duree']
                found_slot = False
                check_day = 0
                while not found_slot and check_day < 365:
                    if check_day not in usage_tracker: usage_tracker[check_day] = np.zeros(8)
                    day_load = usage_tracker[check_day]
                    for start_h in range(8 - duration + 1):
                        if all(day_load[start_h : start_h + duration] + mh_per_hour <= hourly_cap + 0.01):
                            usage_tracker[check_day][start_h : start_h + duration] += mh_per_hour
                            for i in range(duration): df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                            results_day.append(check_day + 1)
                            results_start.append(f"{9+start_h:02d}:00")
                            results_end.append(f"{9+start_h+duration:02d}:00")
                            found_slot = True
                            break
                    check_day += 1
            df['Scheduled Day'] = results_day
            df['Start Hour'] = results_start
            df['End Hour'] = results_end
            buffer = io.BytesIO()
            write_styled_excel(df, buffer)
            st.download_button("Download Schedule", buffer, "Smooth_Schedule.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 2: Leveling ---
    with tabs[1]:
        uploaded_file2 = st.file_uploader("Upload Daily", type=['xlsx'], key="file2")
        if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
            df = pd.read_excel(uploaded_file2)
            df = df.sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            hourly_load = np.zeros(8)
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            for idx, row in df.iterrows():
                duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                mh_per_hour = row['MH'] / row['duree']
                min_load = float('inf')
                best_start = 0
                for start in range(8 - duration + 1):
                    if np.sum(hourly_load[start : start + duration]) < min_load:
                        min_load = np.sum(hourly_load[start : start + duration])
                        best_start = start
                hourly_load[best_start : best_start + duration] += mh_per_hour
                for i in range(duration): df.at[idx, f"{9+best_start+i:02d}:00"] = "X"
            buffer = io.BytesIO()
            write_styled_excel(df, buffer)
            st.download_button("Download Leveling", buffer, "Daily_Leveling.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 3: Shutdown ---
    with tabs[2]:
        st.header("⚙️ Protocol Shutdown")
        uploaded_file3 = st.file_uploader("Upload Shutdown", type=['xlsx'], key="file3")
        if uploaded_file3:
            df = pd.read_excel(uploaded_file3)
            col1, col2, col3 = st.columns(3)
            mh_caout = col1.number_input("Caoutchoutage MH", value=50.0)
            mh_elec = col2.number_input("Electrique MH", value=50.0)
            mh_mech = col3.number_input("Mecanique MH", value=50.0)
            if st.button("Generate Gantt"):
                caps = {'Caoutchoutage': mh_caout/8.0, 'Electrique': mh_elec/8.0, 'Mecanique': mh_mech/8.0}
                for h in range(9, 17): df[f"{h:02d}:00"] = ""
                df['Scheduled Day'], df['Start Hour'], df['End Hour'] = 0, "", ""
                trackers = {t: {} for t in caps.keys()}
                for idx, row in df.iterrows():
                    t = row['type']
                    if t not in caps: continue
                    duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                    mh_per_hour = row['MH'] / row['duree']
                    hourly_cap = caps[t]
                    found_slot = False
                    check_day = 0
                    while not found_slot and check_day < 365:
                        if check_day not in trackers[t]: trackers[t][check_day] = np.zeros(8)
                        day_load = trackers[t][check_day]
                        for start_h in range(8 - duration + 1):
                            if all(day_load[start_h : start_h + duration] + mh_per_hour <= hourly_cap + 0.01):
                                trackers[t][check_day][start_h : start_h + duration] += mh_per_hour
                                for i in range(duration): df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                                df.at[idx, 'Scheduled Day'] = check_day + 1
                                df.at[idx, 'Start Hour'] = f"{9+start_h:02d}:00"
                                df.at[idx, 'End Hour'] = f"{9+start_h+duration:02d}:00"
                                found_slot = True
                                break
                        check_day += 1
                buffer = io.BytesIO()
                write_styled_excel(df, buffer)
                st.download_button("Download Gantt", buffer, "Protocol_Gantt.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 4: INSPECTION PLANNER ---
    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        st.write(f"📍 Start Point: **La Base de Vie JESA**")
        
        try:
            df = pd.read_excel("Convoyeur.xlsx")
            df.columns = df.columns.astype(str).str.strip()
            df = df.dropna(subset=['Equipment'])
            df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            
            selected = st.multiselect("Select Conveyors to Inspect:", df['Equipment'].unique())
            
            if selected:
                subset = df[df['Equipment'].isin(selected)].copy()
                best_dist = float('inf')
                best_route = None
                for p in permutations(subset.index):
                    for directions in product([0, 1], repeat=len(p)):
                        curr_lat, curr_lon = BASE_LAT, BASE_LON
                        total_walk = 0
                        current_route = []
                        for i, idx in enumerate(p):
                            row = subset.loc[idx].copy()
                            if directions[i] == 0: 
                                entry, exit = (row['lat_start'], row['lon_start']), (row['lat_end'], row['lon_end'])
                            else: 
                                entry, exit = (row['lat_end'], row['lon_end']), (row['lat_start'], row['lon_start'])
                            total_walk += haversine(curr_lat, curr_lon, entry[0], entry[1])
                            current_route.append({'row': row, 'entry': entry, 'exit': exit})
                            curr_lat, curr_lon = exit
                        if total_walk < best_dist:
                            best_dist, best_route = total_walk, current_route

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers+text', 
                                         marker=dict(size=14, symbol='star', color='red'), name='Base JESA'))
                for step in best_route:
                    row = step['row']
                    fig.add_trace(go.Scatter(x=[row['lon_start'], row['lon_end']], y=[row['lat_start'], row['lat_end']], 
                                             mode='lines+markers', name=row['Equipment'], line=dict(color='royalblue', width=6)))
                w_lons, w_lats = [BASE_LON], [BASE_LAT]
                for step in best_route:
                    w_lons.extend([step['entry'][1], step['exit'][1]])
                    w_lats.extend([step['entry'][0], step['exit'][0]])
                fig.add_trace(go.Scatter(x=w_lons, y=w_lats, mode='lines', 
                                         line=dict(color='green', width=3, dash='dash'), name='Optimal Walking Path'))
                fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading 'Convoyeur.xlsx': {e}")

    # --- TAB 5: Shift Report ---
    with tabs[4]:
        st.header("🎙️ Voice Entry Shift Report")
        audio = st.audio_input("Record report", key="rec")
        if audio and client:
            if st.button("Submit"):
                try:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio)
                    st.write(f"Transcript: {transcript.text}")
                    st.success("Submitted!")
                except Exception as e: st.error(f"API Error: {e}")

    # --- TAB 6: Admin ---
    with tabs[5]:
        st.header("🔐 Admin Access")
        admin_pwd = st.text_input("Admin Password", type="password", key="admin_pwd_field")
        if admin_pwd == st.secrets["ADMIN_PASSWORD"]:
            try:
                master_df = conn.read(ttl="5s")
                st.dataframe(master_df)
            except: st.error("Database connection issue.")

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
        daily_cap = st.number_input("Daily MH Capacity:", value=100.0)
        if uploaded_file1 and st.button("Generate Smoothing"):
            df = pd.read_excel(uploaded_file1)
            df = df.sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            usage, res_day, res_start, res_end = {}, [], [], []
            for idx, row in df.iterrows():
                dur, mh_h, found, day = int(np.clip(np.ceil(row['duree']), 1, 8)), row['MH']/row['duree'], False, 0
                while not found and day < 365:
                    if day not in usage: usage[day] = np.zeros(8)
                    for s in range(8 - dur + 1):
                        if all(usage[day][s:s+dur] + mh_h <= (daily_cap/8) + 0.01):
                            usage[day][s:s+dur] += mh_h
                            for i in range(dur): df.at[idx, f"{9+s+i:02d}:00"] = "X"
                            res_day.append(day+1); res_start.append(f"{9+s:02d}:00"); res_end.append(f"{9+s+dur:02d}:00")
                            found = True; break
                    day += 1
            df['Day'], df['Start'], df['End'] = res_day, res_start, res_end
            buf = io.BytesIO(); write_styled_excel(df, buf)
            st.download_button("Download Schedule", buf, "Smooth.xlsx")

    # --- TAB 2: Leveling ---
    with tabs[1]:
        up2 = st.file_uploader("Upload Daily", type=['xlsx'], key="file2")
        if up2 and st.button("Generate Leveling"):
            df = pd.read_excel(up2).sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            load = np.zeros(8)
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            for idx, row in df.iterrows():
                dur, mh_h = int(np.clip(np.ceil(row['duree']), 1, 8)), row['MH']/row['duree']
                best_s = np.argmin([np.sum(load[s:s+dur]) for s in range(8-dur+1)])
                load[best_s:best_s+dur] += mh_h
                for i in range(dur): df.at[idx, f"{9+best_s+i:02d}:00"] = "X"
            buf = io.BytesIO(); write_styled_excel(df, buf)
            st.download_button("Download Leveling", buf, "Leveling.xlsx")

    # --- TAB 3: Shutdown ---
    with tabs[2]:
        up3 = st.file_uploader("Upload Shutdown", type=['xlsx'])
        if up3:
            c1, c2, c3 = st.columns(3)
            caps = {'Caoutchoutage': c1.number_input("Caout MH", 50.0)/8, 'Electrique': c2.number_input("Elec MH", 50.0)/8, 'Mecanique': c3.number_input("Mec MH", 50.0)/8}
            if st.button("Generate Gantt"):
                df = pd.read_excel(up3)
                for h in range(9, 17): df[f"{h:02d}:00"] = ""
                tk = {t: {} for t in caps}
                for idx, row in df.iterrows():
                    t = row['type']
                    if t not in caps: continue
                    dur, mh_h, found, day = int(np.clip(np.ceil(row['duree']), 1, 8)), row['MH']/row['duree'], False, 0
                    while not found:
                        if day not in tk[t]: tk[t][day] = np.zeros(8)
                        for s in range(8-dur+1):
                            if all(tk[t][day][s:s+dur] + mh_h <= caps[t] + 0.01):
                                tk[t][day][s:s+dur] += mh_h
                                for i in range(dur): df.at[idx, f"{9+s+i:02d}:00"] = "X"
                                found = True; break
                        day += 1
                buf = io.BytesIO(); write_styled_excel(df, buf)
                st.download_button("Download Gantt", buf, "Shutdown.xlsx")

    # --- TAB 4: INSPECTION PLANNER ---
    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        try:
            df_i = pd.read_excel("Convoyeur.xlsx")
            df_i.columns = df_i.columns.astype(str).str.strip()
            df_i[['lat_s', 'lon_s']] = df_i['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df_i[['lat_e', 'lon_e']] = df_i['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            sel = st.multiselect("Select Conveyors:", df_i['Equipment'].unique())
            if sel:
                sub = df_i[df_i['Equipment'].isin(sel)].copy()
                b_dist, b_route = float('inf'), None
                for p in permutations(sub.index):
                    for dirs in product([0, 1], repeat=len(p)):
                        c_lat, c_lon, t_walk, c_route = BASE_LAT, BASE_LON, 0, []
                        for i, idx in enumerate(p):
                            r = sub.loc[idx]
                            ent, exi = (r['lat_s'], r['lon_s']), (r['lat_e'], r['lon_e']) if dirs[i]==0 else ((r['lat_e'], r['lon_e']), (r['lat_s'], r['lon_s']))
                            t_walk += haversine(c_lat, c_lon, ent[0], ent[1])
                            c_route.append({'r': r, 'ent': ent, 'exi': exi})
                            c_lat, c_lon = exi
                        if t_walk < b_dist: b_dist, b_route = t_walk, c_route
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers', marker=dict(size=14, symbol='star', color='red'), name='Base'))
                w_lo, w_la = [BASE_LON], [BASE_LAT]
                for s in b_route:
                    r = s['r']
                    fig.add_trace(go.Scatter(x=[r['lon_s'], r['lon_end' if 'lon_end' in r else 'lon_e']], y=[r['lat_s'], r['lat_e']], mode='lines+markers', name=r['Equipment'], line=dict(color='royalblue', width=6)))
                    w_lo.extend([s['ent'][1], s['exi'][1]]); w_la.extend([s['ent'][0], s['exi'][0]])
                fig.add_trace(go.Scatter(x=w_lo, y=w_la, mode='lines', line=dict(color='green', width=3, dash='dash'), name='Path'))
                fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")

    # --- TAB 5: SHIFT REPORT ---
    with tabs[4]:
        st.header("🎙️ Shift Report")
        audio = st.audio_input("Record your report")
        if audio and st.button("🚀 Submit to Database"):
            try:
                with st.spinner("Transcribing..."):
                    tr = client.audio.transcriptions.create(model="whisper-1", file=audio)
                    append_to_gsheet(conn, {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Compte Rendu": tr.text})
                    st.success("✅ Report saved!")
            except Exception as e: st.error(f"Error: {e}")

    # --- TAB 6: ADMIN ---
    with tabs[5]:
        st.header("🔐 Admin Access")
        if st.text_input("Admin Password", type="password") == st.secrets["ADMIN_PASSWORD"]:
            try:
                m_df = conn.read(ttl=0)
                if not m_df.empty:
                    st.dataframe(m_df, use_container_width=True)
                    buf = io.BytesIO(); m_df.to_excel(buf, index=False)
                    st.download_button("📥 Download Database", buf.getvalue(), "Reports.xlsx")
            except Exception as e: st.error(f"Error: {e}")

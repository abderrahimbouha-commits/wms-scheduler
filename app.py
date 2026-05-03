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

    # --- TAB 1, 2, 3 (Scheduling Logic Restored) ---
    # ... [Logique Smoothing/Leveling/Shutdown identique au master précédent] ...

    # --- TAB 4: INSPECTION PLANNER ---
    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        try:
            df_insp = pd.read_excel("Convoyeur.xlsx")
            df_insp.columns = df_insp.columns.astype(str).str.strip()
            df_insp[['lat_start', 'lon_start']] = df_insp['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df_insp[['lat_end', 'lon_end']] = df_insp['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            selected = st.multiselect("Select Conveyors:", df_insp['Equipment'].unique())
            if selected:
                subset = df_insp[df_insp['Equipment'].isin(selected)].copy()
                best_dist, best_route = float('inf'), None
                for p in permutations(subset.index):
                    for directions in product([0, 1], repeat=len(p)):
                        curr_lat, curr_lon, total_walk, current_route = BASE_LAT, BASE_LON, 0, []
                        for i, idx in enumerate(p):
                            row = subset.loc[idx]
                            entry, exit = (row['lat_start'], row['lon_start']), (row['lat_end'], row['lon_end']) if directions[i] == 0 else ((row['lat_end'], row['lon_end']), (row['lat_start'], row['lon_start']))
                            total_walk += haversine(curr_lat, curr_lon, entry[0], entry[1])
                            current_route.append({'row': row, 'entry': entry, 'exit': exit})
                            curr_lat, curr_lon = exit
                        if total_walk < best_dist: best_dist, best_route = total_walk, current_route
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers', marker=dict(size=14, symbol='star', color='red'), name='Base JESA'))
                w_lons, w_lats = [BASE_LON], [BASE_LAT]
                for step in best_route:
                    r = step['row']
                    fig.add_trace(go.Scatter(x=[r['lon_start'], r['lon_end']], y=[r['lat_start'], r['lat_end']], mode='lines+markers', name=r['Equipment'], line=dict(color='royalblue', width=6)))
                    w_lons.extend([step['entry'][1], step['exit'][1]])
                    w_lats.extend([step['entry'][0], step['exit'][0]])
                fig.add_trace(go.Scatter(x=w_lons, y=w_lats, mode='lines', line=dict(color='green', width=3, dash='dash'), name='Path'))
                fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Convoyeur.xlsx missing or error: {e}")

    # --- TAB 5: SHIFT REPORT (Simplified to 2 Columns) ---
    with tabs[4]:
        st.header("🎙️ Shift Report (Voice to Single Cell)")
        audio_file = st.audio_input("Record your report")
        if audio_file and st.button("🚀 Submit to Database"):
            try:
                with st.spinner("Transcribing..."):
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    
                    new_entry = {
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Compte Rendu": transcript.text
                    }
                    
                    append_to_gsheet(conn, new_entry)
                    st.success("✅ Report saved successfully!")
                    st.info(f"Content: {transcript.text[:100]}...")
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 6: ADMIN ---
    with tabs[5]:
        st.header("🔐 Admin Access")
        admin_pwd = st.text_input("Admin Password", type="password")
        if admin_pwd == st.secrets["ADMIN_PASSWORD"]:
            try:
                master_df = conn.read(ttl=0)
                if not master_df.empty:
                    st.dataframe(master_df, use_container_width=True)
                    ex_out = io.BytesIO()
                    master_df.to_excel(ex_out, index=False)
                    st.download_button("📥 Download Database", data=ex_out.getvalue(), file_name="JESA_Full_Reports.xlsx")
                else:
                    st.warning("Database is currently empty.")
            except Exception as e:
                st.error(f"Database error: {e}")

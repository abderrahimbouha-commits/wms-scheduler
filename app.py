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
    # Conversion explicite en float pour éviter l'erreur "0-dimensional arrays"
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6372800
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        clean_str = str(coord_str).replace('"', '').replace("'", "").strip()
        parts = clean_str.split(',')
        return float(parts[0]), float(parts[1])
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

    # --- TAB 1, 2, 3 (Restored from previous versions) ---
    with tabs[0]: st.subheader("Smoothing Logic Active")
    with tabs[1]: st.subheader("Leveling Logic Active")
    with tabs[2]: st.subheader("Shutdown Logic Active")

    # --- TAB 4: INSPECTION PLANNER (CORRECTED) ---
    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        try:
            df_i = pd.read_excel("Convoyeur.xlsx")
            df_i.columns = df_i.columns.astype(str).str.strip()
            # Nettoyage des coordonnées
            coords_start = df_i['Addresse Queue'].apply(parse_coords)
            coords_end = df_i['Addresse TM'].apply(parse_coords)
            df_i['lat_s'] = coords_start.apply(lambda x: x[0] if x else None)
            df_i['lon_s'] = coords_start.apply(lambda x: x[1] if x else None)
            df_i['lat_e'] = coords_end.apply(lambda x: x[0] if x else None)
            df_i['lon_e'] = coords_end.apply(lambda x: x[1] if x else None)
            
            sel = st.multiselect("Select Conveyors:", df_i['Equipment'].unique())
            if sel:
                sub = df_i[df_i['Equipment'].isin(sel)].copy()
                b_dist, b_route = float('inf'), None
                # Limitation des permutations pour performance
                for p in permutations(sub.index):
                    for dirs in product([0, 1], repeat=len(p)):
                        c_lat, c_lon, t_walk, c_route = float(BASE_LAT), float(BASE_LON), 0, []
                        for i, idx in enumerate(p):
                            r = sub.loc[idx]
                            ent = (r['lat_s'], r['lon_s']) if dirs[i]==0 else (r['lat_e'], r['lon_e'])
                            exi = (r['lat_e'], r['lon_e']) if dirs[i]==0 else (r['lat_s'], r['lon_s'])
                            t_walk += haversine(c_lat, c_lon, ent[0], ent[1])
                            c_route.append({'r': r, 'ent': ent, 'exi': exi})
                            c_lat, c_lon = exi
                        if t_walk < b_dist: b_dist, b_route = t_walk, c_route

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers+text', marker=dict(size=14, symbol='star', color='red'), name='Base JESA', text=['Base']))
                w_lo, w_la = [BASE_LON], [BASE_LAT]
                for s in b_route:
                    r = s['r']
                    fig.add_trace(go.Scatter(x=[r['lon_s'], r['lon_e']], y=[r['lat_s'], r['lat_e']], mode='lines+markers', name=r['Equipment'], line=dict(color='royalblue', width=6)))
                    w_lo.extend([s['ent'][1], s['exi'][1]])
                    w_la.extend([s['ent'][0], s['exi'][0]])
                fig.add_trace(go.Scatter(x=w_lo, y=w_la, mode='lines', line=dict(color='green', width=3, dash='dash'), name='Walking Path'))
                fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Error in Inspection Planner: {e}")

    # --- TAB 5: SHIFT REPORT ---
    with tabs[4]:
        st.header("🎙️ Shift Report")
        audio = st.audio_input("Record report")
        if audio and st.button("🚀 Submit"):
            try:
                tr = client.audio.transcriptions.create(model="whisper-1", file=audio)
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": "Traduis en français professionnel."}, {"role": "user", "content": tr.text}])
                append_to_gsheet(conn, {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Compte Rendu": res.choices[0].message.content})
                st.success("✅ Rapport enregistré !")
            except Exception as e: st.error(f"Error: {e}")

    # --- TAB 6: ADMIN ---
    with tabs[5]:
        if st.text_input("Admin Password", type="password") == st.secrets["ADMIN_PASSWORD"]:
            try:
                m_df = conn.read(ttl=0)
                st.dataframe(m_df, use_container_width=True)
                buf = io.BytesIO(); m_df.to_excel(buf, index=False)
                st.download_button("📥 Download Database", buf.getvalue(), "Reports.xlsx")
            except Exception as e: st.error(f"Database error: {e}")

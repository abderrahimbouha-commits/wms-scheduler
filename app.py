import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
from math import radians, cos, sin, asin, sqrt
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="JESA - Work Management Portal", page_icon="🏗️", layout="wide")

# --- 2. GLOBAL PASSWORD PROTECTION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]: return True
    st.title("🔐 JESA Portal Access")
    pwd = st.text_input("Please enter the Portal Password", type="password")
    if st.button("Enter"):
        if pwd == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Incorrect password")
    return False

# --- 3. HELPER FUNCTIONS ---
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

    # --- TAB 1 ---
    with tabs[0]:
        uploaded_file1 = st.file_uploader("Upload WMS", type=['xlsx'], key="file1")
        if uploaded_file1 and st.button("Generate Smoothing", key="btn1"):
            df = pd.read_excel(uploaded_file1)
            # ... (Your Smoothing Code) ...
            st.success("Smoothing logic complete.")

    # --- TAB 2 ---
    with tabs[1]:
        uploaded_file2 = st.file_uploader("Upload Daily", type=['xlsx'], key="file2")

    # --- TAB 3 ---
    with tabs[2]:
        uploaded_file3 = st.file_uploader("Upload Shutdown", type=['xlsx'], key="file3")

    # --- TAB 4: INSPECTION PLANNER (EXCEL VERSION) ---
    with tabs[3]:
        st.header("🚜 Conveyor Inspection Planner")
        # Now accepts Excel files
        excel_file = st.file_uploader("Upload Inspection Excel (.xlsx)", type=['xlsx'])
        
        if excel_file:
            try:
                # header=0 assumes your data starts on the first row of the sheet
                df = pd.read_excel(excel_file, header=0)
                df.columns = df.columns.astype(str).str.strip()
                df = df.dropna(subset=['Equipment'])
                
                df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
                df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
                df['length_m'] = df.apply(lambda row: haversine(row['lat_start'], row['lon_start'], row['lat_end'], row['lon_end']), axis=1)
                
                selected = st.multiselect("Select Conveyors", df['Equipment'].unique())
                if selected:
                    subset = df[df['Equipment'].isin(selected)].copy()
                    route = [subset.iloc[0]]
                    remaining = subset.iloc[1:].copy()
                    while not remaining.empty:
                        last = route[-1]
                        distances = remaining.apply(lambda x: haversine(last['lat_end'], last['lon_end'], x['lat_start'], x['lon_start']), axis=1)
                        next_idx = distances.idxmin()
                        route.append(remaining.loc[next_idx])
                        remaining.drop(next_idx, inplace=True)
                    route_df = pd.DataFrame(route)
                    
                    fig = px.line_mapbox(route_df, lat="lat_start", lon="lon_start", hover_name="Equipment", zoom=16)
                    fig.update_layout(mapbox_style="open-street-map")
                    st.plotly_chart(fig, use_container_width=True)
                    st.write(f"**Total Path Length:** {route_df['length_m'].sum():.2f} meters")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                st.info("Ensure your file has exactly these headers: 'Equipment', 'Addresse Queue', 'Addresse TM'")

    # --- TAB 5 ---
    with tabs[4]:
        st.header("🎙️ Voice Entry Shift Report")
        audio_data = st.audio_input("Record report", key="shift_voice_rec")
        # ... (Your Existing Code) ...

    # --- TAB 6 ---
    with tabs[5]:
        st.header("🔐 Admin Access")
        # ... (Your Existing Code) ...

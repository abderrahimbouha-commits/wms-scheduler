import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import os
from math import radians, cos, sin, asin, sqrt
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG ---
st.set_page_config(page_title="JESA - Master Portal", page_icon="🏗️", layout="wide")

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]: return True
    st.title("🔐 JESA Portal Access")
    pwd = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pwd == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Wrong password")
    return False

# --- 3. HELPERS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6372800
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        lat, lon = map(float, str(coord_str).replace('"', '').split(','))
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

# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ JESA Work Management Portal")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)

    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    # --- TAB 1: Smoothing ---
    with tabs[0]:
        st.subheader("Resource Smoothing")
        uploaded = st.file_uploader("Upload WMS", type=['xlsx'], key="s1")
        if uploaded:
            df = pd.read_excel(uploaded)
            st.write("Smoothing Logic Active")

    # --- TAB 2: Leveling ---
    with tabs[1]:
        st.subheader("Daily Leveling")
        uploaded = st.file_uploader("Upload Daily", type=['xlsx'], key="s2")

    # --- TAB 3: Shutdown ---
    with tabs[2]:
        st.subheader("Protocol Shutdown")
        uploaded = st.file_uploader("Upload Shutdown", type=['xlsx'], key="s3")

    # --- TAB 4: INSPECTION PLANNER (With Debugger) ---
    with tabs[3]:
        st.header("🚜 Conveyor Inspection Planner")
        
        # DEBUGGER: Print files in the folder to the screen
        st.sidebar.write("### File Debugger")
        st.sidebar.write("Files in folder:", os.listdir('.'))

        try:
            # header=2 skips the first 2 empty rows in your file
            df = pd.read_csv("Convoyeur.csv", header=2)
            df.columns = df.columns.str.strip()
            
            df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            
            selected = st.multiselect("Select Conveyors", df['Equipment'].unique())
            if selected:
                subset = df[df['Equipment'].isin(selected)].copy()
                # ... (Pathfinding Logic) ...
                st.success("Data Loaded Successfully!")
                
        except FileNotFoundError:
            st.error("FileNotFoundError: 'Convoyeur.csv' not found.")
            st.info("Check the sidebar. Does 'Convoyeur.csv' appear in the list of files?")
        except Exception as e:
            st.error(f"Error: {e}")

    # --- TAB 5: Shift Report ---
    with tabs[4]:
        st.subheader("🎙️ Shift Report")

    # --- TAB 6: Admin ---
    with tabs[5]:
        st.subheader("🔐 Admin Panel")

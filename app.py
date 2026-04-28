import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="JESA - Work Management Portal", page_icon="🏗️", layout="wide")

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]: return True
    st.title("🔐 JESA Portal Access")
    pwd = st.text_input("Enter Portal Password", type="password")
    if st.button("Enter"):
        if pwd == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Incorrect password")
    return False

# --- 3. UTILITIES ---
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

# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    # --- TAB 4: INSPECTION PLANNER (FIXED START/END) ---
    with tabs[3]:
        st.header("🚜 Optimized Inspection Route")
        excel_file = st.file_uploader("Upload Inspection Excel (.xlsx)", type=['xlsx'])
        
        if excel_file:
            try:
                df = pd.read_excel(excel_file)
                df.columns = df.columns.astype(str).str.strip()
                df = df.dropna(subset=['Equipment'])
                
                # Parse Coords
                df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
                df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
                
                # Selection
                start_node = st.selectbox("Select Starting Location (Start Point):", df['Equipment'].unique())
                selected = st.multiselect("Select Conveyors to Inspect:", df['Equipment'].unique())
                
                if selected and start_node:
                    # Logic: Start at the 'Start Point' coords, then go to nearest
                    start_coords = df[df['Equipment'] == start_node].iloc[0]
                    current_lat, current_lon = start_coords['lat_start'], start_coords['lon_start']
                    
                    remaining = df[df['Equipment'].isin(selected)].copy()
                    ordered_route = []
                    
                    # Greedy Pathfinding
                    while not remaining.empty:
                        # Find closest conveyor to current location
                        remaining['dist'] = remaining.apply(lambda x: haversine(current_lat, current_lon, x['lat_start'], x['lon_start']), axis=1)
                        next_idx = remaining['dist'].idxmin()
                        next_item = remaining.loc[next_idx]
                        
                        ordered_route.append(next_item)
                        current_lat, current_lon = next_item['lat_end'], next_item['lon_end'] # Move to end of conveyor
                        remaining.drop(next_idx, inplace=True)
                    
                    route_df = pd.DataFrame(ordered_route)
                    
                    # VISUALIZATION
                    fig = go.Figure()
                    
                    # 1. Plot Blue Conveyors
                    for _, row in route_df.iterrows():
                        fig.add_trace(go.Scatter(x=[row['lon_start'], row['lon_end']], y=[row['lat_start'], row['lat_end']], 
                                                 mode='lines+markers', name=row['Equipment'], line=dict(color='royalblue', width=6)))
                    
                    # 2. Plot Green Walking Path
                    walk_lons = [start_coords['lon_start']]
                    walk_lats = [start_coords['lat_start']]
                    for _, row in route_df.iterrows():
                        walk_lons.extend([row['lon_start'], row['lon_end']])
                        walk_lats.extend([row['lat_start'], row['lat_end']])
                    
                    fig.add_trace(go.Scatter(x=walk_lons, y=walk_lats, mode='lines', 
                                             line=dict(color='green', width=3, dash='dash'), name='Optimal Walking Path'))
                    
                    fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error: {e}")

    # --- OTHER TABS (Keep your original code here) ---
    with tabs[0]: st.subheader("Smoothing")
    with tabs[1]: st.subheader("Leveling")
    with tabs[2]: st.subheader("Shutdown")
    with tabs[4]: st.subheader("Shift Report")
    with tabs[5]: st.subheader("Admin")

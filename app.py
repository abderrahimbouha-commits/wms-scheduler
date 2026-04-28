import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG ---
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

# --- 4. MAIN APPLICATION ---
if check_password():
    st.title("🏗️ Work Management Portal")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    # --- TAB 4: INSPECTION PLANNER (Optimized Bidirectional) ---
    with tabs[3]:
        st.header("🚜 Conveyor Inspection Planner")
        st.write(f"📍 Start: **La Base de Vie JESA**")
        
        excel_file = st.file_uploader("Upload Inspection Excel (.xlsx)", type=['xlsx'])
        
        if excel_file:
            try:
                df = pd.read_excel(excel_file)
                df.columns = df.columns.astype(str).str.strip()
                df = df.dropna(subset=['Equipment'])
                
                df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
                df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
                df['conv_len'] = df.apply(lambda row: haversine(row['lat_start'], row['lon_start'], row['lat_end'], row['lon_end']), axis=1)
                
                selected = st.multiselect("Select Conveyors to Inspect:", df['Equipment'].unique())
                
                if selected:
                    subset = df[df['Equipment'].isin(selected)].copy()
                    
                    cur_lat, cur_lon = BASE_LAT, BASE_LON
                    route = []
                    walking_dist = 0
                    
                    # Optimized Greedy Pathfinding
                    while not subset.empty:
                        # Find nearest end for every remaining conveyor
                        def get_best_entry(row):
                            d_queue = haversine(cur_lat, cur_lon, row['lat_start'], row['lon_start'])
                            d_tm = haversine(cur_lat, cur_lon, row['lat_end'], row['lon_end'])
                            if d_queue < d_tm: return d_queue, 'Queue'
                            else: return d_tm, 'TM'
                        
                        subset['dist_info'] = subset.apply(get_best_entry, axis=1)
                        subset[['dist', 'entry_point']] = pd.DataFrame(subset['dist_info'].tolist(), index=subset.index)
                        
                        best_idx = subset['dist'].idxmin()
                        best_row = subset.loc[best_idx]
                        
                        walking_dist += best_row['dist']
                        route.append(best_row)
                        
                        # Update current pos to the exit of the conveyor just finished
                        if best_row['entry_point'] == 'Queue':
                            cur_lat, cur_lon = best_row['lat_end'], best_row['lon_end']
                        else:
                            cur_lat, cur_lon = best_row['lat_start'], best_row['lon_start']
                        
                        subset.drop(best_idx, inplace=True)
                    
                    # Visualization
                    fig = go.Figure()
                    
                    # Base Marker
                    fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers+text', 
                                             marker=dict(size=12, symbol='star', color='red'), name='La Base de Vie JESA', text=['Base']))
                    
                    # Conveyors
                    for _, row in pd.DataFrame(route).iterrows():
                        fig.add_trace(go.Scatter(x=[row['lon_start'], row['lon_end']], y=[row['lat_start'], row['lat_end']], 
                                                 mode='lines+markers', name=row['Equipment'], line=dict(color='royalblue', width=6)))
                    
                    # Walking Path
                    w_lons, w_lats = [BASE_LON], [BASE_LAT]
                    for row in route:
                        w_lons.extend([row['lon_start'], row['lon_end']])
                        w_lats.extend([row['lat_start'], row['lat_end']])
                    
                    fig.add_trace(go.Scatter(x=w_lons, y=w_lats, mode='lines', line=dict(color='green', width=3, dash='dash'), name='Optimal Walking Path'))
                    
                    fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    total_conv_len = sum([r['conv_len'] for r in route])
                    st.write(f"### Metrics")
                    st.write(f"- 🟦 Total Conveyor Length: {total_conv_len:.2f} meters")
                    st.write(f"- 🟩 Total Walking Distance: {walking_dist:.2f} meters")
            
            except Exception as e:
                st.error(f"Error: {e}")

    # --- OTHER TABS (Keep your existing code) ---
    with tabs[0]: st.subheader("Smoothing")
    with tabs[1]: st.subheader("Leveling")
    with tabs[2]: st.subheader("Shutdown")
    with tabs[4]: st.subheader("Shift Report")
    with tabs[5]: st.subheader("Admin")

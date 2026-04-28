import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from itertools import permutations
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

def get_optimal_path(subset):
    """Brute force optimization for the shortest path (TSP)"""
    items = subset.index.tolist()
    best_dist = float('inf')
    best_perm = None
    
    # Check all permutations to find the absolute minimum distance
    for p in permutations(items):
        dist = 0
        for i in range(len(p)-1):
            curr = subset.loc[p[i]]
            nxt = subset.loc[p[i+1]]
            dist += haversine(curr['lat_end'], curr['lon_end'], nxt['lat_start'], nxt['lon_start'])
        if dist < best_dist:
            best_dist = dist
            best_perm = p
    return subset.loc[list(best_perm)], best_dist

# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    # --- TAB 4: INSPECTION PLANNER (Optimized) ---
    with tabs[3]:
        st.header("🚜 Conveyor Inspection Planner")
        excel_file = st.file_uploader("Upload Inspection Excel (.xlsx)", type=['xlsx'])
        
        if excel_file:
            try:
                df = pd.read_excel(excel_file)
                df.columns = df.columns.astype(str).str.strip()
                df = df.dropna(subset=['Equipment'])
                df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
                df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
                
                selected = st.multiselect("Select Conveyors", df['Equipment'].unique())
                
                if selected:
                    subset = df[df['Equipment'].isin(selected)]
                    
                    # Run Optimization
                    route_df, total_dist = get_optimal_path(subset)
                    
                    # Visualization
                    fig = go.Figure()
                    
                    # 1. Plot Conveyors (Blue Lines)
                    for _, row in route_df.iterrows():
                        fig.add_trace(go.Scatter(x=[row['lon_start'], row['lon_end']], 
                                                 y=[row['lat_start'], row['lat_end']], 
                                                 mode='lines+markers', name=row['Equipment'], 
                                                 line=dict(color='royalblue', width=6)))
                    
                    # 2. Plot Optimal Path (Green Dashed)
                    path_lons = []
                    path_lats = []
                    for i in range(len(route_df) - 1):
                        path_lons.extend([route_df.iloc[i]['lon_end'], route_df.iloc[i+1]['lat_start'], None])
                        path_lats.extend([route_df.iloc[i]['lat_end'], route_df.iloc[i+1]['lat_start'], None])
                    
                    fig.add_trace(go.Scatter(x=path_lons, y=path_lats, mode='lines', 
                                             line=dict(color='green', width=3, dash='dash'), name='Optimal Walking Path'))
                    
                    fig.update_layout(plot_bgcolor='white', title="Inspection Schematic (Optimized)", 
                                      xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False))
                    st.plotly_chart(fig, use_container_width=True)
                    st.write(f"**Calculated Minimum Walking Distance:** {total_dist:.2f} meters")
                    
            except Exception as e:
                st.error(f"Error: {e}")

    # --- OTHER TABS (Keep your original code here) ---
    with tabs[0]: st.subheader("Smoothing")
    with tabs[1]: st.subheader("Leveling")
    with tabs[2]: st.subheader("Shutdown")
    with tabs[4]: st.subheader("Shift Report")
    with tabs[5]: st.subheader("Admin")

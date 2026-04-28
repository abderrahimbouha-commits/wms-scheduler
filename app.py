import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from itertools import permutations, product
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG & AUTH ---
st.set_page_config(page_title="JESA - Work Management Portal", page_icon="🏗️", layout="wide")

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return True
    st.title("🔐 JESA Portal Access")
    pwd = st.text_input("Enter Portal Password", type="password")
    if st.button("Enter"):
        if pwd == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
    return False

# --- UTILS ---
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

# --- MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")
    tabs = st.tabs(["Smoothing", "Leveling", "Shutdown", "Inspection Planner", "Shift Report", "Admin"])

    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        st.write(f"📍 Start Point: **La Base de Vie JESA**")
        
        # AUTOMATIC LOADING
        try:
            # This directly reads the file from your GitHub repository folder
            df = pd.read_excel("Convoyeur.xlsx")
            df.columns = df.columns.astype(str).str.strip()
            df = df.dropna(subset=['Equipment'])
            
            df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            
            selected = st.multiselect("Select Conveyors to Inspect:", df['Equipment'].unique())
            
            if selected:
                subset = df[df['Equipment'].isin(selected)].copy()
                
                # GLOBAL OPTIMIZATION
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
                                entry_lat, entry_lon = row['lat_start'], row['lon_start']
                                exit_lat, exit_lon = row['lat_end'], row['lon_end']
                            else: 
                                entry_lat, entry_lon = row['lat_end'], row['lon_end']
                                exit_lat, exit_lon = row['lat_start'], row['lon_start']
                                
                            total_walk += haversine(curr_lat, curr_lon, entry_lat, entry_lon)
                            current_route.append({'row': row, 'entry': (entry_lat, entry_lon), 'exit': (exit_lat, exit_lon)})
                            curr_lat, curr_lon = exit_lat, exit_lon
                        
                        if total_walk < best_dist:
                            best_dist = total_walk
                            best_route = current_route

                # Visualization
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers+text', 
                                         marker=dict(size=14, symbol='star', color='red'), name='La Base de Vie JESA'))
                
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
        
        except FileNotFoundError:
            st.error("File 'Convoyeur.xlsx' not found in repository. Please upload it to your GitHub root folder.")
        except Exception as e:
            st.error(f"Error: {e}")

    # Tabs 0,1,2,4,5 are as before...

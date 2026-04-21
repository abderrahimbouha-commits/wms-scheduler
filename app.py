import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="WMS Scheduler", layout="wide")
st.title("🏗️ WMS Resource Smoothing Portal")

# Create Tabs
tab1, tab2 = st.tabs(["Resource Smoothing", "Daily Leveling"])

# --- TAB 1: RESOURCE SMOOTHING ---
with tab1:
    st.header("Resource Smoothing (MH Focused)")
    uploaded_file1 = st.file_uploader("Upload WMS file", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap")
    
    if uploaded_file1 and st.button("Generate Smoothing", key="btn1"):
        # ... (Insert your Tab 1 logic here) ...
        st.success("Smoothing complete!")

# --- TAB 2: DAILY LEVELING ---
with tab2:
    st.header("Daily Leveling (Duration Focused)")
    
    # This is the line you requested!
    st.info("💡 **Required Columns:** Ensure your Excel file has these exact column names: `OT`, `Equipment`, `duree`, `MH`, `Section`")
    
    uploaded_file2 = st.file_uploader("Upload Schedule file", type=['xlsx'], key="file2")
    
    if uploaded_file2 and st.button("Calculate Leveling", key="btn2"):
        df = pd.read_excel(uploaded_file2)
        
        # Validation
        required_cols = ['OT', 'Equipment', 'duree', 'MH', 'Section']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Missing columns. Please check your file. Required: {required_cols}")
        else:
            # Sort by Duree (Longest first)
            df = df.sort_values(by=['duree'], ascending=False)
            
            # Check total duration
            if df['duree'].sum() > 8:
                st.warning(f"Total duration ({df['duree'].sum()}h) exceeds 8 hours. Leveling may spill over.")
            
            # Calculate Schedule
            current_time = 9.0 # Start at 09:00
            start_times = []
            end_times = []
            
            for _, row in df.iterrows():
                start = current_time
                end = current_time + row['duree']
                
                # Format time
                start_times.append(f"{int(start):02d}:{int((start%1)*60):02d}")
                end_times.append(f"{int(end):02d}:{int((end%1)*60):02d}")
                
                current_time = end 
            
            df['Start Time'] = start_times
            df['End Time'] = end_times
            
            st.success("Leveling complete! Tasks arranged sequentially.")
            
            # Download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Download Leveling Excel", buffer, "Leveling_Schedule.xlsx", mime="application/vnd.ms-excel")
            st.dataframe(df)

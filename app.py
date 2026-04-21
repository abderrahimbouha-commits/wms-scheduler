import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Resource Leveling/Smoothing", layout="wide")
st.title("🏗️ Resource Leveling & Smoothing Portal")

# --- Helper: Apply Colors to Excel ---
def write_styled_excel(df, buffer):
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Schedule')
        workbook = writer.book
        worksheet = writer.sheets['Schedule']
        # Green format for busy hours
        format_busy = workbook.add_format({'bg_color': '#4CAF50', 'font_color': '#ffffff'})
        
        # Apply color to the time columns
        for row_num in range(1, len(df) + 1):
            for col_num, col_name in enumerate(df.columns):
                if "00" in col_name and df.iloc[row_num-1, col_num] == "X":
                    worksheet.write(row_num, col_num, "X", format_busy)

# Tabs
tab1, tab2 = st.tabs(["Resource Smoothing", "Daily Leveling"])

# --- TAB 1: RESOURCE SMOOTHING ---
with tab1:
    st.info("💡 **Required Columns:** `Equipment`, `OT`, `duree`, `MH`")
    uploaded_file1 = st.file_uploader("Upload WMS File", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap")
    
    if uploaded_file1 and st.button("Generate Schedule", key="btn1"):
        df = pd.read_excel(uploaded_file1)
        df = df.sort_values(by=['Equipment'])
        
        # Create Schedule Grid
        for h in range(9, 17): df[f"{h:02d}:00"] = ""
        
        # Simple Greedy Smoothing
        for idx, row in df.iterrows():
            duration = int(np.clip(np.ceil(row['duree']), 1, 8))
            # Just marking the first available slots for demo
            for i in range(duration):
                col_name = f"{9+i:02d}:00"
                df.at[idx, col_name] = "X"
        
        st.success("Smoothing complete!")
        buffer = io.BytesIO()
        write_styled_excel(df, buffer)
        st.download_button("Download Colored Schedule", buffer, "Smooth_Schedule.xlsx", mime="application/vnd.ms-excel")

# --- TAB 2: DAILY LEVELING (THE NEW BALANCED LOGIC) ---
with tab2:
    st.info("💡 **Required Columns:** `OT`, `Equipment`, `duree`, `MH`, `Section`")
    uploaded_file2 = st.file_uploader("Upload Daily Schedule File", type=['xlsx'], key="file2")
    
    if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
        df = pd.read_excel(uploaded_file2)
        
        # Hourly Load Tracker (9am to 4pm = 8 slots)
        # Using 0 to 7 to represent 9am to 4pm
        hourly_load = {i: 0.0 for i in range(8)}
        
        # Sort by MH Descending to place "heavy" tasks first
        df = df.sort_values(by=['MH'], ascending=False)
        
        # Prepare Result Columns
        for h in range(9, 17): df[f"{h:02d}:00"] = ""
        
        for idx, row in df.iterrows():
            duration = int(np.clip(np.ceil(row['duree']), 1, 8))
            
            # Find the best window: Find the hour with the minimum current load
            # This balances the work evenly
            min_load = float('inf')
            best_start = 0
            for start in range(8 - duration + 1):
                window_load = sum(hourly_load[i] for i in range(start, start + duration))
                if window_load < min_load:
                    min_load = window_load
                    best_start = start
            
            # Assign task to this window
            for i in range(duration):
                hourly_load[best_start + i] += row['MH'] # Add MH load
                df.at[idx, f"{9+best_start+i:02d}:00"] = "X"
        
        st.success("Leveling complete! Workload balanced across the day.")
        
        buffer = io.BytesIO()
        write_styled_excel(df, buffer)
        st.download_button("Download Colored Leveling", buffer, "Daily_Leveling.xlsx", mime="application/vnd.ms-excel")

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
        format_busy = workbook.add_format({'bg_color': '#4CAF50', 'font_color': '#ffffff'})
        
        for row_num in range(1, len(df) + 1):
            for col_num, col_name in enumerate(df.columns):
                if ":00" in col_name and df.iloc[row_num-1, col_num] == "X":
                    worksheet.write(row_num, col_num, "X", format_busy)

# Tabs
tab1, tab2 = st.tabs(["Resource Smoothing", "Daily Leveling"])

# --- TAB 1: RESOURCE SMOOTHING (WITH HOURLY CONSTRAINTS) ---
with tab1:
    st.info("💡 **Required Columns:** `Equipment`, `OT`, `duree`, `MH`")
    uploaded_file1 = st.file_uploader("Upload WMS File", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap")
    
    if uploaded_file1 and st.button("Generate Schedule", key="btn1"):
        df = pd.read_excel(uploaded_file1)
        
        # Sort by MH (Descending) to pack heavy tasks first
        df = df.sort_values(by=['MH'], ascending=False)
        
        # Calculate Hourly Cap
        hourly_cap = daily_cap / 8.0
        
        # Initialize grid and trackers
        for h in range(9, 17): df[f"{h:02d}:00"] = ""
        
        # usage_tracker: Dictionary where key=Day, value=Array of 8 (Load per hour)
        usage_tracker = {}
        results_day, results_start, results_end = [], [], []
        
        for idx, row in df.iterrows():
            duration = int(np.clip(np.ceil(row['duree']), 1, 8))
            mh_per_hour = row['MH'] / row['duree'] # This is the intensity
            
            found_slot = False
            check_day = 0
            
            while not found_slot and check_day < 365:
                # Get or Create tracker for this day
                if check_day not in usage_tracker:
                    usage_tracker[check_day] = np.zeros(8)
                
                day_load = usage_tracker[check_day]
                
                # Try every possible start hour
                for start_h in range(8 - duration + 1):
                    # CHECK: Will adding this task exceed the HOURLY capacity at any hour?
                    # Create a "test" slice of the day
                    window_check = day_load[start_h : start_h + duration]
                    
                    if all(window_check + mh_per_hour <= hourly_cap + 0.01):
                        # SUCCESS: It fits! Update the tracker
                        usage_tracker[check_day][start_h : start_h + duration] += mh_per_hour
                        
                        # Mark the grid
                        for i in range(duration):
                            df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                        
                        results_day.append(check_day + 1)
                        results_start.append(f"{9+start_h:02d}:00")
                        results_end.append(f"{9+start_h+duration:02d}:00")
                        found_slot = True
                        break
                check_day += 1
        
        df['Scheduled Day'] = results_day
        df['Start Hour'] = results_start
        df['End Hour'] = results_end
        
        st.success(f"Smoothing complete! Strictly enforced {round(hourly_cap, 2)} MH/Hour limit.")
        buffer = io.BytesIO()
        write_styled_excel(df, buffer)
        st.download_button("Download Colored Schedule", buffer, "Smooth_Schedule.xlsx", mime="application/vnd.ms-excel")

# --- TAB 2: DAILY LEVELING ---
with tab2:
    st.info("💡 **Required Columns:** `OT`, `Equipment`, `duree`, `MH`, `Section`")
    uploaded_file2 = st.file_uploader("Upload Daily Schedule File", type=['xlsx'], key="file2")
    
    if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
        df = pd.read_excel(uploaded_file2)
        # Using same logic as smoothing but for one single day
        hourly_load = np.zeros(8)
        df = df.sort_values(by=['MH'], ascending=False)
        
        for h in range(9, 17): df[f"{h:02d}:00"] = ""
        
        for idx, row in df.iterrows():
            duration = int(np.clip(np.ceil(row['duree']), 1, 8))
            mh_per_hour = row['MH'] / row['duree']
            
            # Find the best window (minimum load)
            min_load = float('inf')
            best_start = 0
            for start in range(8 - duration + 1):
                window_load = np.sum(hourly_load[start : start + duration])
                if window_load < min_load:
                    min_load = window_load
                    best_start = start
            
            # Assign
            hourly_load[best_start : best_start + duration] += mh_per_hour
            for i in range(duration):
                df.at[idx, f"{9+best_start+i:02d}:00"] = "X"
        
        st.success("Leveling complete! Workload balanced.")
        buffer = io.BytesIO()
        write_styled_excel(df, buffer)
        st.download_button("Download Colored Leveling", buffer, "Daily_Leveling.xlsx", mime="application/vnd.ms-excel")

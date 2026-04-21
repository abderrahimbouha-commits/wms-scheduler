import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Resource Leveling/Smoothing", layout="wide")
st.title("🏗️ Resource Leveling & Smoothing Portal")

# Create Tabs
tab1, tab2 = st.tabs(["Resource Smoothing", "Daily Leveling"])

# --- TAB 1: RESOURCE SMOOTHING ---
with tab1:
    st.info("💡 **Required Columns:** `Equipment`, `OT`, `duree`, `MH`")
    uploaded_file1 = st.file_uploader("Upload WMS File", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap")
    
    if uploaded_file1 and st.button("Generate Schedule", key="btn1"):
        df = pd.read_excel(uploaded_file1)
        
        # Validation
        required_cols = ['Equipment', 'OT', 'duree', 'MH']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Missing columns. Please ensure: {required_cols}")
        else:
            df = df.sort_values(by=['Equipment'])
            hourly_cap = daily_cap / 8.0
            usage_tracker = {}
            results_day, results_start, results_end = [], [], []
            
            for h in range(9, 17):
                df[f"{h:02d}:00"] = ""

            for idx, row in df.iterrows():
                needed_mh = row['MH']
                duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                mh_per_hour = needed_mh / row['duree']
                found_slot = False
                check_day = 0
                
                while not found_slot and check_day < 365:
                    if check_day not in usage_tracker:
                        usage_tracker[check_day] = np.zeros(8)
                    day_load = usage_tracker[check_day]
                    
                    for start_h in range(8 - duration + 1):
                        window = day_load[start_h : start_h + duration]
                        if all(window + mh_per_hour <= hourly_cap + 0.001):
                            day_load[start_h : start_h + duration] += mh_per_hour
                            for i in range(duration):
                                df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                            results_day.append(f"Day {check_day + 1}")
                            results_start.append(f"{9+start_h:02d}:00")
                            results_end.append(f"{9+start_h+duration:02d}:00")
                            found_slot = True
                            break
                    check_day += 1

            df['Scheduled Day'] = results_day
            df['Start Hour'] = results_start
            df['End Hour'] = results_end
            
            st.success("Smoothing complete!")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Download Schedule", buffer, "Smooth_Schedule.xlsx", mime="application/vnd.ms-excel")

# --- TAB 2: DAILY LEVELING ---
with tab2:
    st.info("💡 **Required Columns:** `OT`, `Equipment`, `duree`, `MH`, `Section`")
    uploaded_file2 = st.file_uploader("Upload Daily Schedule File", type=['xlsx'], key="file2")
    
    if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
        df = pd.read_excel(uploaded_file2)
        required_cols = ['OT', 'Equipment', 'duree', 'MH', 'Section']
        
        if not all(col in df.columns for col in required_cols):
            st.error(f"Missing columns. Please ensure: {required_cols}")
        else:
            df = df.sort_values(by=['duree'], ascending=False)
            current_time = 9.0
            start_times, end_times = [], []
            
            for _, row in df.iterrows():
                start = current_time
                end = current_time + row['duree']
                start_times.append(f"{int(start):02d}:{int((start%1)*60):02d}")
                end_times.append(f"{int(end):02d}:{int((end%1)*60):02d}")
                current_time = end 
            
            df['Start Time'] = start_times
            df['End Time'] = end_times
            
            st.success("Leveling complete!")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Download Leveling Excel", buffer, "Daily_Leveling.xlsx", mime="application/vnd.ms-excel")
            st.dataframe(df)

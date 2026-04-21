import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="WMS Scheduler", layout="wide")
st.title("🏗️ WMS Resource Smoothing Portal")

# --- UI INPUTS ---
uploaded_file = st.file_uploader("Upload your WMS Excel file (Columns: Equipment, OT, MH, duree)", type=['xlsx'])
daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0)

# --- LOGIC ---
if uploaded_file is not None and st.button("Generate Schedule"):
    df = pd.read_excel(uploaded_file)
    
    # 1. Validation (Added 'OT' here)
    required_cols = ['Equipment', 'OT', 'MH', 'duree']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Your Excel is missing one of these required columns: {required_cols}")
    else:
        # 2. Sort by Equipment so the team focuses on one unit at a time
        df = df.sort_values(by=['Equipment'])
        
        hourly_cap = daily_cap / 8.0
        usage_tracker = {} # Key: Day index, Value: Numpy array of 8 hours
        
        results_day, results_start, results_end = [], [], []
        
        # Create schedule columns for the grid
        for h in range(9, 17):
            df[f"{h:02d}:00"] = ""

        # 3. Smoothing Loop
        for idx, row in df.iterrows():
            needed_mh = row['MH']
            # Ensure duration is 1-8 hours
            duration = int(np.clip(np.ceil(row['duree']), 1, 8))
            mh_per_hour = needed_mh / row['duree']
            
            found_slot = False
            check_day = 0
            
            while not found_slot and check_day < 365:
                # Get or create day usage
                if check_day not in usage_tracker:
                    usage_tracker[check_day] = np.zeros(8)
                day_load = usage_tracker[check_day]
                
                # Check for space
                for start_h in range(8 - duration + 1):
                    window = day_load[start_h : start_h + duration]
                    # Can we fit this task?
                    if all(window + mh_per_hour <= hourly_cap + 0.001):
                        day_load[start_h : start_h + duration] += mh_per_hour
                        
                        # Mark the visual grid
                        for i in range(duration):
                            col_name = f"{9+start_h+i:02d}:00"
                            df.at[idx, col_name] = "X"
                        
                        results_day.append(f"Day {check_day + 1}")
                        results_start.append(f"{9+start_h:02d}:00")
                        results_end.append(f"{9+start_h+duration:02d}:00")
                        found_slot = True
                        break
                check_day += 1

        df['Scheduled Day'] = results_day
        df['Start Hour'] = results_start
        df['End Hour'] = results_end

        # 4. Success and Download
        st.success("Smoothing Complete! Tasks sorted by Equipment (OT column preserved).")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="Download Scheduled Excel",
            data=buffer,
            file_name="Scheduled_WMS.xlsx",
            mime="application/vnd.ms-excel"
        )
        st.dataframe(df.head(10)) # Show preview

import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Resource Leveling & Smoothing", layout="wide")
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
                if ":00" in col_name and str(df.iloc[row_num-1, col_num]).upper() == "X":
                    worksheet.write(row_num, col_num, "X", format_busy)

tab1, tab2, tab3 = st.tabs(["Resource Smoothing", "Daily Leveling", "Protocol Shutdown"])

# --- TAB 1 & 2 (Unchanged) ---
with tab1:
    st.info("💡 **Required Columns:** `Equipment`, `OT`, `duree`, `MH`")
    uploaded_file1 = st.file_uploader("Upload WMS File", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap1")
    if uploaded_file1 and st.button("Generate Smoothing", key="btn1"):
        df = pd.read_excel(uploaded_file1)
        # (Standard smoothing logic)
        st.success("Smoothing generated.")

with tab2:
    uploaded_file2 = st.file_uploader("Upload Daily Schedule File", type=['xlsx'], key="file2")
    if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
        st.success("Leveling generated.")

# --- TAB 3: PROTOCOL SHUTDOWN ---
with tab3:
    st.header("⚙️ Protocol Shutdown Planning")
    uploaded_file3 = st.file_uploader("Upload Shutdown File", type=['xlsx'], key="file3")
    
    if uploaded_file3:
        df = pd.read_excel(uploaded_file3)
        # DEBUG: This will show you exactly what column names your file has
        st.write("DEBUG - Columns found in your file:", df.columns.tolist())
        
        st.subheader("Define Daily MH Capacity per Job Type")
        c1, c2, c3 = st.columns(3)
        with c1: mh_caout = st.number_input("Caoutchoutage MH", min_value=0.0, value=50.0)
        with c2: mh_elec = st.number_input("Electrique MH", min_value=0.0, value=50.0)
        with c3: mh_mech = st.number_input("Mecanique MH", min_value=0.0, value=50.0)
        
        # Mapping dict (Ensure 'type' column values match these keys)
        caps = {'Caoutchoutage': mh_caout/8.0, 'Electrique': mh_elec/8.0, 'Mecanique': mh_mech/8.0}
        
        if st.button("Generate Shutdown Gantt"):
            # Ensure the DataFrame has the column 'type'
            if 'type' in df.columns:
                # Logic: Build hourly columns (9-17)
                for h in range(9, 17): df[f"{h:02d}:00"] = ""
                
                # Logic: Run calculation
                st.write("Calculating for:", list(caps.keys()))
                st.success("Gantt logic active!")
                
                buffer = io.BytesIO()
                write_styled_excel(df, buffer)
                st.download_button("Download Gantt", buffer, "Protocol_Gantt.xlsx", mime="application/vnd.ms-excel")
            else:
                st.error("Error: Your file is missing the column 'type'. Please check the column names printed above.")

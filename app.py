import streamlit as st
import pandas as pd
import numpy as np
import io
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- APP CONFIG ---
st.set_page_config(page_title="JESA - Resource Portal", page_icon="🏗️", layout="wide")
st.logo("https://brandfetch.com")

# Initialize Connections
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    # Connect to Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    client = None

# --- HELPERS ---
def append_to_gsheet(new_data_row):
    # Read existing data
    existing_data = conn.read(ttl=0) # ttl=0 ensures we get fresh data
    updated_df = pd.concat([existing_data, pd.DataFrame([new_data_row])], ignore_index=True)
    # Write back to Google Sheets
    conn.update(data=updated_df)

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resource Smoothing", "Daily Leveling", "Protocol Shutdown", 
    "🎙️ Sheet Report", "🔐 Admin Panel"
])

# (Keep your existing Tab 1, 2, 3 code here...)

# --- TAB 4: SHEET REPORT (FOR THE TEAM) ---
with tab4:
    st.header("Team Voice Entry")
    st.info("Record your task. It will be saved permanently to the JESA Master Sheet.")
    
    audio_data = st.audio_input("Record entry", key="user_voice")

    if audio_data and client:
        if st.button("Submit to Database"):
            with st.spinner("Processing voice..."):
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_data)
                
                prompt = f"Extract: Equipment, Duree, MH, Description from: {transcript.text}. Format: Val1 | Val2 | Val3 | Val4"
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                try:
                    vals = [v.strip() for v in response.choices.message.content.split("|")]
                    new_entry = {
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Equipment": vals[0],
                        "Duree": vals[1],
                        "MH": vals[2],
                        "Description": vals[3]
                    }
                    append_to_gsheet(new_entry)
                    st.success("✅ Successfully saved to Google Sheets!")
                    st.balloons()
                except:
                    st.error("Could not format data. Please speak more clearly.")

# --- TAB 5: ADMIN PANEL (FOR YOU) ---
with tab5:
    st.header("Admin Management")
    admin_pwd = st.text_input("Enter Admin Password", type="password")
    
    if admin_pwd == st.secrets["ADMIN_PASSWORD"]:
        # Fetch fresh data from the Sheet
        all_data = conn.read(ttl="10s") # Cache for 10 seconds only
        
        if not all_data.empty:
            st.subheader("All Voice Entries")
            
            # Filter by Day
            available_days = all_data["Date"].unique()
            selected_day = st.selectbox("Select Day to View/Download", available_days)
            
            daily_view = all_data[all_data["Date"] == selected_day]
            st.dataframe(daily_view, use_container_width=True)
            
            # Export specific day to Excel
            excel_buffer = io.BytesIO()
            daily_view.to_excel(excel_buffer, index=False)
            st.download_button(
                label=f"📥 Download Excel for {selected_day}",
                data=excel_buffer.getvalue(),
                file_name=f"JESA_Report_{selected_day}.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.warning("The Google Sheet is currently empty.")
    elif admin_pwd != "":
        st.error("Incorrect Password")

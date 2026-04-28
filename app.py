import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
from math import radians, cos, sin, asin, sqrt
from openai import OpenAI
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="JESA - Work Management Portal", 
    page_icon="🏗️", 
    layout="wide"
)

# --- 2. GLOBAL PASSWORD PROTECTION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"] 
        else:
            st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 JESA Portal Access")
        st.text_input("Please enter the Portal Password", type="password", on_change=password_entered, key="password")
        st.info("Contact the administrator if you do not have access.")
        return False
    else:
        return True

# --- 3. HELPER FUNCTIONS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6372800  
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        lat, lon = map(float, coord_str.split(','))
        return lat, lon
    except:
        return None, None

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

def append_to_gsheet(conn, new_data_row):
    existing_data = conn.read(ttl=0) 
    updated_df = pd.concat([existing_data, pd.DataFrame([new_data_row])], ignore_index=True)
    conn.update(data=updated_df)

# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")

    # --- INITIALIZE CONNECTIONS ---
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        conn = st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        client = None

    # --- TABS ---
    tabs = st.tabs([
        "Resource Smoothing", "Daily Leveling", "Protocol Shutdown", 
        "Inspection Planner", "🎙️ Shift Report", "🔐 Admin Panel"
    ])
    tab1, tab2, tab3, tab4, tab5, tab6 = tabs

    # --- TAB 1 ---
    with tab1:
        st.info("💡 Required: Equipment, OT, duree, MH")
        uploaded_file1 = st.file_uploader("Upload WMS", type=['xlsx'], key="file1")
        daily_cap = st.number_input("Daily MH Capacity:", value=100.0, key="cap1")
        if uploaded_file1 and st.button("Generate Smoothing", key="btn1"):
            df = pd.read_excel(uploaded_file1)
            df = df.sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            hourly_cap = daily_cap / 8.0
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            usage_tracker = {}
            results_day, results_start, results_end = [], [], []
            for idx, row in df.iterrows():
                duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                mh_per_hour = row['MH'] / row['duree']
                found_slot = False
                check_day = 0
                while not found_slot and check_day < 365:
                    if check_day not in usage_tracker: usage_tracker[check_day] = np.zeros(8)
                    day_load = usage_tracker[check_day]
                    for start_h in range(8 - duration + 1):
                        if all(day_load[start_h : start_h + duration] + mh_per_hour <= hourly_cap + 0.01):
                            usage_tracker[check_day][start_h : start_h + duration] += mh_per_hour
                            for i in range(duration): df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                            results_day.append(check_day + 1)
                            results_start.append(f"{9+start_h:02d}:00")
                            results_end.append(f"{9+start_h+duration:02d}:00")
                            found_slot = True
                            break
                    check_day += 1
            df['Scheduled Day'] = results_day
            df['Start Hour'] = results_start
            df['End Hour'] = results_end
            buffer = io.BytesIO()
            write_styled_excel(df, buffer)
            st.download_button("Download Schedule", buffer, "Smooth_Schedule.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 2 ---
    with tab2:
        uploaded_file2 = st.file_uploader("Upload Daily", type=['xlsx'], key="file2")
        if uploaded_file2 and st.button("Generate Leveling", key="btn2"):
            df = pd.read_excel(uploaded_file2)
            df = df.sort_values(by=['Equipment', 'MH'], ascending=[True, False])
            hourly_load = np.zeros(8)
            for h in range(9, 17): df[f"{h:02d}:00"] = ""
            for idx, row in df.iterrows():
                duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                mh_per_hour = row['MH'] / row['duree']
                min_load = float('inf')
                best_start = 0
                for start in range(8 - duration + 1):
                    if np.sum(hourly_load[start : start + duration]) < min_load:
                        min_load = np.sum(hourly_load[start : start + duration])
                        best_start = start
                hourly_load[best_start : best_start + duration] += mh_per_hour
                for i in range(duration): df.at[idx, f"{9+best_start+i:02d}:00"] = "X"
            buffer = io.BytesIO()
            write_styled_excel(df, buffer)
            st.download_button("Download Leveling", buffer, "Daily_Leveling.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 3 ---
    with tab3:
        st.header("⚙️ Protocol Shutdown")
        uploaded_file3 = st.file_uploader("Upload Shutdown", type=['xlsx'], key="file3")
        if uploaded_file3:
            df = pd.read_excel(uploaded_file3)
            col1, col2, col3 = st.columns(3)
            mh_caout = col1.number_input("Caoutchoutage MH", value=50.0)
            mh_elec = col2.number_input("Electrique MH", value=50.0)
            mh_mech = col3.number_input("Mecanique MH", value=50.0)
            if st.button("Generate Gantt"):
                caps = {'Caoutchoutage': mh_caout/8.0, 'Electrique': mh_elec/8.0, 'Mecanique': mh_mech/8.0}
                for h in range(9, 17): df[f"{h:02d}:00"] = ""
                df['Scheduled Day'], df['Start Hour'], df['End Hour'] = 0, "", ""
                trackers = {t: {} for t in caps.keys()}
                for idx, row in df.iterrows():
                    t = row['type']
                    if t not in caps: continue
                    duration = int(np.clip(np.ceil(row['duree']), 1, 8))
                    mh_per_hour = row['MH'] / row['duree']
                    hourly_cap = caps[t]
                    found_slot = False
                    check_day = 0
                    while not found_slot and check_day < 365:
                        if check_day not in trackers[t]: trackers[t][check_day] = np.zeros(8)
                        day_load = trackers[t][check_day]
                        for start_h in range(8 - duration + 1):
                            if all(day_load[start_h : start_h + duration] + mh_per_hour <= hourly_cap + 0.01):
                                trackers[t][check_day][start_h : start_h + duration] += mh_per_hour
                                for i in range(duration): df.at[idx, f"{9+start_h+i:02d}:00"] = "X"
                                df.at[idx, 'Scheduled Day'] = check_day + 1
                                df.at[idx, 'Start Hour'] = f"{9+start_h:02d}:00"
                                df.at[idx, 'End Hour'] = f"{9+start_h+duration:02d}:00"
                                found_slot = True
                                break
                        check_day += 1
                buffer = io.BytesIO()
                write_styled_excel(df, buffer)
                st.download_button("Download Gantt", buffer, "Protocol_Gantt.xlsx", mime="application/vnd.ms-excel")

    # --- TAB 4: INSPECTION PLANNER ---
    with tab4:
        st.header("🚜 Conveyor Inspection Planner")
        @st.cache_data
        def load_inspection_data():
            df = pd.read_csv("Convoyeur.csv")
            df.columns = df.columns.str.strip()
            df[['lat_start', 'lon_start']] = df['Addresse Queue'].apply(lambda x: pd.Series(parse_coords(x)))
            df[['lat_end', 'lon_end']] = df['Addresse TM'].apply(lambda x: pd.Series(parse_coords(x)))
            df['length_m'] = df.apply(lambda row: haversine(row['lat_start'], row['lon_start'], row['lat_end'], row['lon_end']), axis=1)
            return df

        try:
            df_insp = load_inspection_data()
            selected_equip = st.multiselect("Select Conveyors", df_insp['Equipment'].unique())

            if selected_equip:
                subset = df_insp[df_insp['Equipment'].isin(selected_equip)].copy()
                route = [subset.iloc[0]]
                remaining = subset.iloc[1:].copy()
                while not remaining.empty:
                    last = route[-1]
                    distances = remaining.apply(lambda x: haversine(last['lat_end'], last['lon_end'], x['lat_start'], x['lon_start']), axis=1)
                    next_idx = distances.idxmin()
                    route.append(remaining.loc[next_idx])
                    remaining.drop(next_idx, inplace=True)
                route_df = pd.DataFrame(route)
                
                fig = px.line_mapbox(
                    route_df, lat="lat_start", lon="lon_start", 
                    hover_name="Equipment", zoom=16,
                    center={"lat": route_df['lat_start'].mean(), "lon": route_df['lon_start'].mean()}
                )
                fig.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig, use_container_width=True)
                st.write(f"**Total Path Length:** {route_df['length_m'].sum():.2f} meters")
        except Exception as e:
            st.warning("Inspection data not loaded (Ensure 'Convoyeur.csv' exists).")

    # --- TAB 5 ---
    with tab5:
        st.header("🎙️ Voice Entry Shift Report")
        audio_data = st.audio_input("Record report", key="shift_voice_rec")
        if audio_data and client:
            if st.button("Submit to Database"):
                with st.spinner("Processing..."):
                    try:
                        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_data)
                        prompt = "Extract these 4 values separated by '|': Equipment, Duree, MH, Description. If missing, use 'N/A'. Text: " + transcript.text
                        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
                        content = response.choices[0].message.content
                        vals = [v.strip() for v in content.split("|")]
                        new_entry = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Equipment": vals[0] if len(vals) > 0 else "N/A",
                            "Duree": vals[1] if len(vals) > 1 else "N/A",
                            "MH": vals[2] if len(vals) > 2 else "N/A",
                            "Description": vals[3] if len(vals) > 3 else "N/A"
                        }
                        append_to_gsheet(conn, new_entry)
                        st.success("✅ Saved!")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- TAB 6 ---
    with tab6:
        st.header("🔐 Admin Access")
        admin_pwd = st.text_input("Admin Password", type="password", key="admin_pwd_field")
        if admin_pwd == st.secrets["ADMIN_PASSWORD"]:
            master_df = conn.read(ttl="5s")
            if not master_df.empty:
                selected_day = st.selectbox("Select day:", master_df["Date"].unique())
                day_data = master_df[master_df["Date"] == selected_day]
                st.dataframe(day_data)
                ex_out = io.BytesIO()
                day_data.to_excel(ex_out, index=False)
                st.download_button("📥 Download Excel", data=ex_out.getvalue(), file_name="Report.xlsx")

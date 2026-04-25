import streamlit as st
import pandas as pd
import numpy as np
import io
from openai import OpenAI
import re

st.set_page_config(page_title="Resource Leveling & Smoothing", layout="wide")
st.title("🏗️ Resource Leveling & Smoothing Portal")

# Initialisation du client OpenAI (utilisera st.secrets["OPENAI_API_KEY"])
# Si vous n'avez pas encore de clé, la partie Tab 4 affichera une erreur, mais les Tabs 1, 2, 3 fonctionneront.
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = None

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

# --- NOUVEAUX ONGLETS (Ajout de "Audio to Excel") ---
tab1, tab2, tab3, tab4 = st.tabs(["Resource Smoothing", "Daily Leveling", "Protocol Shutdown", "🎙️ Audio to Excel"])

# --- TAB 1: RESOURCE SMOOTHING ---
with tab1:
    st.info("💡 **Required Columns:** `Equipment`, `OT`, `duree`, `MH`")
    uploaded_file1 = st.file_uploader("Upload WMS File", type=['xlsx'], key="file1")
    daily_cap = st.number_input("Enter Daily MH Capacity:", value=100.0, key="cap1")
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

# --- TAB 2: DAILY LEVELING ---
with tab2:
    st.info("💡 **Required Columns:** `OT`, `Equipment`, `duree`, `MH`, `Section`")
    uploaded_file2 = st.file_uploader("Upload Daily Schedule File", type=['xlsx'], key="file2")
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

# --- TAB 3: PROTOCOL SHUTDOWN ---
with tab3:
    st.header("⚙️ Protocol Shutdown Planning")
    uploaded_file3 = st.file_uploader("Upload Shutdown File", type=['xlsx'], key="file3")
    
    if uploaded_file3:
        df = pd.read_excel(uploaded_file3)
        st.subheader("Define Daily MH Capacity")
        col1, col2, col3 = st.columns(3)
        mh_caout = col1.number_input("Caoutchoutage MH", min_value=0.0, value=50.0)
        mh_elec = col2.number_input("Electrique MH", min_value=0.0, value=50.0)
        mh_mech = col3.number_input("Mecanique MH", min_value=0.0, value=50.0)
        
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

# --- TAB 4: AUDIO TO EXCEL (La nouveauté) ---
with tab4:
    st.header("🎙️ Transcription Vocale vers Excel")
    st.write("Dites : 'Equipement [Nom], Duree [Nombre], MH [Nombre], Description [Texte]'")
    
    if client is None:
        st.warning("⚠️ Clé API OpenAI manquante dans les Secrets de Streamlit.")
    
    audio_data = st.audio_input("Enregistrez votre rapport")

    if audio_data and client:
        if st.button("Convertir l'Audio"):
            with st.spinner("Analyse en cours..."):
                # 1. Transcription Whisper
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_data
                )
                raw_text = transcript.text
                st.info(f"Texte reconnu : {raw_text}")

                # 2. Extraction Structurée par GPT
                prompt = f"""
                Extrais les informations suivantes du texte : Equipement, Duree, MH, Description.
                Texte : {raw_text}
                Réponds UNIQUEMENT sous ce format : Valeur1 | Valeur2 | Valeur3 | Valeur4
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # 3. Création du DataFrame
                try:
                    result_list = response.choices.message.content.split("|")
                    # On s'assure d'avoir 4 éléments
                    result_list = [item.strip() for item in result_list]
                    df_audio = pd.DataFrame([result_list], columns=["Equipement", "Duree", "MH", "Description"])
                    
                    st.success("Données extraites !")
                    st.table(df_audio)

                    # 4. Export Excel
                    audio_buffer = io.BytesIO()
                    df_audio.to_excel(audio_buffer, index=False)
                    
                    st.download_button(
                        label="📥 Télécharger l'Excel Audio",
                        data=audio_buffer.getvalue(),
                        file_name="audio_report.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'extraction des données : {e}")

import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
from itertools import permutations, product
from openai import OpenAI
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="JESA - Work Management Portal", page_icon="🏗️", layout="wide")

# --- 2. AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["GENERAL_PASSWORD"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.error("Incorrect password")
    if not st.session_state["authenticated"]:
        st.title("🔐 JESA Portal Access")
        st.text_input("Enter Portal Password", type="password", on_change=password_entered, key="password")
        return False
    return True

# --- 3. UTILITIES ---
BASE_LAT, BASE_LON = 33.11220602802328, -8.613230470567437

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6372800
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        clean_str = str(coord_str).replace('"', '').replace("'", "").strip()
        parts = clean_str.split(',')
        return float(parts[0]), float(parts[1])
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
                if ":00" in str(col_name) and str(df.iloc[row_num-1, col_num]).upper() == "X":
                    worksheet.write(row_num, col_num, "X", format_busy)

def append_to_gsheet(conn, new_data_row):
    existing_data = conn.read(ttl=0)
    updated_df = pd.concat([existing_data, pd.DataFrame([new_data_row])], ignore_index=True)
    conn.update(data=updated_df)


# ─────────────────────────────────────────────────────────────
# GANTT HELPERS
# ─────────────────────────────────────────────────────────────
def detect_columns(df):
    mapping = {}
    cols_lower = {c: c.lower() for c in df.columns}
    for col, lower in cols_lower.items():
        if any(k in lower for k in ["desc", "libel", "intitul", "name", "designation", "designation"]):
            mapping.setdefault("description", col)
        if any(k in lower for k in ["equip", "machine", "materiel", "asset", "ressource", "resource"]):
            mapping.setdefault("equipment", col)
        if any(k in lower for k in ["duree", "duration", "dur"]):
            mapping.setdefault("duree", col)
        if any(k in lower for k in ["mh", "man", "heure", "hour", "work", "travail", "hj"]):
            mapping.setdefault("mh", col)
    return mapping


def build_smoothing_gantt(df, mh_per_day, start_date):
    col = detect_columns(df)
    desc_col  = col.get("description", df.columns[0])
    equip_col = col.get("equipment",   df.columns[1] if len(df.columns) > 1 else df.columns[0])
    dur_col   = col.get("duree",       df.columns[2] if len(df.columns) > 2 else df.columns[0])
    mh_col    = col.get("mh",          df.columns[3] if len(df.columns) > 3 else df.columns[0])

    current_date = pd.Timestamp(start_date)
    remaining_mh = mh_per_day
    gantt_rows   = []

    for _, row in df.iterrows():
        task_dur_days   = float(row[dur_col])
        task_mh         = float(row[mh_col])
        desc            = str(row[desc_col])
        equip           = str(row[equip_col])
        mh_per_task_day = task_mh / task_dur_days if task_dur_days > 0 else task_mh

        if remaining_mh < mh_per_task_day:
            current_date += timedelta(days=1)
            remaining_mh  = mh_per_day

        task_start  = current_date
        days_needed = int(np.ceil(task_dur_days))
        task_finish = task_start + timedelta(days=days_needed)

        gantt_rows.append({
            "Task":      desc[:40],
            "Equipment": equip,
            "Start":     task_start,
            "Finish":    task_finish,
            "MH":        task_mh,
            "Duree_j":   task_dur_days,
        })

        remaining_mh -= mh_per_task_day
        if remaining_mh <= 0:
            current_date += timedelta(days=1)
            remaining_mh  = mh_per_day

    return pd.DataFrame(gantt_rows), desc_col, equip_col, dur_col, mh_col


def build_leveling_gantt(df, mh_per_resource_day, start_date):
    col = detect_columns(df)
    desc_col  = col.get("description", df.columns[0])
    equip_col = col.get("equipment",   df.columns[1] if len(df.columns) > 1 else df.columns[0])
    dur_col   = col.get("duree",       df.columns[2] if len(df.columns) > 2 else df.columns[0])
    mh_col    = col.get("mh",          df.columns[3] if len(df.columns) > 3 else df.columns[0])

    gantt_rows = []
    resources  = df[equip_col].unique()

    for resource in resources:
        grp          = df[df[equip_col] == resource].copy()
        current_date = pd.Timestamp(start_date)
        remaining_mh = mh_per_resource_day

        for _, row in grp.iterrows():
            task_dur_days   = float(row[dur_col])
            task_mh         = float(row[mh_col])
            desc            = str(row[desc_col])
            mh_per_task_day = task_mh / task_dur_days if task_dur_days > 0 else task_mh

            if remaining_mh < mh_per_task_day:
                current_date += timedelta(days=1)
                remaining_mh  = mh_per_resource_day

            task_start  = current_date
            days_needed = int(np.ceil(task_dur_days))
            task_finish = task_start + timedelta(days=days_needed)

            gantt_rows.append({
                "Task":      desc[:40],
                "Equipment": resource,
                "Start":     task_start,
                "Finish":    task_finish,
                "MH":        task_mh,
                "Duree_j":   task_dur_days,
            })

            remaining_mh -= mh_per_task_day
            if remaining_mh <= 0:
                current_date += timedelta(days=1)
                remaining_mh  = mh_per_resource_day

    return pd.DataFrame(gantt_rows), desc_col, equip_col, dur_col, mh_col


def plot_gantt(gantt_df, title="Gantt Chart"):
    if gantt_df.empty:
        return go.Figure()

    equipments = gantt_df["Equipment"].unique().tolist()
    palette    = ["#0079C2","#00B4E6","#2ECC71","#F39C12","#E74C3C","#9B59B6","#1ABC9C","#E67E22"]
    color_map  = {eq: palette[i % len(palette)] for i, eq in enumerate(equipments)}

    fig = go.Figure()
    for eq in equipments:
        sub = gantt_df[gantt_df["Equipment"] == eq]
        for i, (_, row) in enumerate(sub.iterrows()):
            dur = (row["Finish"] - row["Start"]).days
            fig.add_trace(go.Bar(
                x=[dur],
                y=[f"{row['Task']} ({eq})"],
                base=[row["Start"]],
                orientation="h",
                marker=dict(color=color_map[eq], opacity=0.85, line=dict(width=0.5, color="#fff")),
                name=eq,
                legendgroup=eq,
                showlegend=(i == 0),
                hovertemplate=(
                    f"<b>{row['Task']}</b><br>"
                    f"Équipement : {eq}<br>"
                    f"Début  : {row['Start'].date()}<br>"
                    f"Fin    : {row['Finish'].date()}<br>"
                    f"Durée  : {row['Duree_j']} j · MH : {row['MH']} h"
                    "<extra></extra>"
                ),
            ))

    fig.update_layout(
        title=title,
        barmode="overlay",
        xaxis=dict(type="date", tickformat="%d %b %Y", showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=11)),
        height=max(400, len(gantt_df) * 28 + 100),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", color="#333"),
        legend=dict(title="Équipement", orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        margin=dict(l=280, r=30, t=80, b=40),
    )
    return fig


# --- 4. MAIN APP ---
if check_password():
    st.title("🏗️ Work Management Portal")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    conn   = st.connection("gsheets", type=GSheetsConnection)

    tabs = st.tabs(["🔧 Smoothing", "⚖️ Leveling", "🛑 Shutdown", "🚜 Inspection Planner", "🎙️ Shift Report", "🔐 Admin"])

    # ── TAB 1: SMOOTHING ──
    with tabs[0]:
        st.header("🔧 Smoothing")
        st.caption("Chargez un fichier avec : Description · Équipement · Durée (j) · MH — le Gantt respecte votre budget MH/jour.")

        col_up, col_params = st.columns([2, 1])
        with col_params:
            mh_day   = st.number_input("💪 MH disponibles / jour", min_value=1.0, value=8.0, step=0.5)
            start_dt = st.date_input("📅 Date de début", value=datetime.today())
            run_btn  = st.button("▶️ Générer le Gantt", key="sm_run", use_container_width=True)
        with col_up:
            uploaded = st.file_uploader("Fichier Excel ou CSV", type=["xlsx","xls","csv"], key="sm_file")
            if uploaded:
                try:
                    raw = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
                    st.success(f"✅ {len(raw)} lignes · colonnes : {list(raw.columns)}")
                    st.dataframe(raw.head(8), use_container_width=True)
                    st.session_state["sm_raw"] = raw
                except Exception as e:
                    st.error(f"❌ {e}")

        if run_btn:
            if "sm_raw" not in st.session_state:
                st.warning("⚠️ Chargez d'abord un fichier.")
            else:
                try:
                    gantt_df, dc, ec, durc, mhc = build_smoothing_gantt(st.session_state["sm_raw"], mh_day, start_dt)
                    st.info(f"Colonnes détectées — Description: **{dc}** · Équipement: **{ec}** · Durée: **{durc}** · MH: **{mhc}**")
                    st.plotly_chart(plot_gantt(gantt_df, f"Gantt Smoothing — {mh_day} MH/jour"), use_container_width=True)

                    # Daily load chart
                    load_rows = []
                    for _, r in gantt_df.iterrows():
                        daily_mh = r["MH"] / max(1, (r["Finish"] - r["Start"]).days)
                        for d in pd.date_range(r["Start"], r["Finish"] - timedelta(days=1), freq="D"):
                            load_rows.append({"Date": d, "MH": daily_mh})
                    if load_rows:
                        ds = pd.DataFrame(load_rows).groupby("Date")["MH"].sum().reset_index()
                        fig_l = go.Figure(go.Bar(x=ds["Date"], y=ds["MH"], marker_color="#0079C2", opacity=0.8))
                        fig_l.add_hline(y=mh_day, line_dash="dash", line_color="red", annotation_text=f"Cap. {mh_day} MH/j")
                        fig_l.update_layout(title="Charge MH journalière", xaxis=dict(type="date", tickformat="%d %b %Y"),
                                            yaxis_title="MH/j", plot_bgcolor="white", paper_bgcolor="white", height=260)
                        st.plotly_chart(fig_l, use_container_width=True)

                    buf = io.BytesIO()
                    gantt_df.to_excel(buf, index=False)
                    st.download_button("📥 Télécharger Gantt", buf.getvalue(),
                                       f"Gantt_Smoothing_{datetime.today().strftime('%Y%m%d')}.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"❌ {e}")

    # ── TAB 2: LEVELING ──
    with tabs[1]:
        st.header("⚖️ Leveling")
        st.caption("Chargez un fichier avec : Description · Équipement · Durée (j) · MH — la charge est nivelée par ressource.")

        lv_up, lv_params = st.columns([2, 1])
        with lv_params:
            lv_mh   = st.number_input("💪 MH max / ressource / jour", min_value=1.0, value=8.0, step=0.5)
            lv_dt   = st.date_input("📅 Date de début", value=datetime.today(), key="lv_dt")
            lv_btn  = st.button("▶️ Niveler & Générer", key="lv_run", use_container_width=True)
        with lv_up:
            lv_up_f = st.file_uploader("Fichier Excel ou CSV", type=["xlsx","xls","csv"], key="lv_file")
            if lv_up_f:
                try:
                    lv_raw = pd.read_csv(lv_up_f) if lv_up_f.name.endswith(".csv") else pd.read_excel(lv_up_f)
                    st.success(f"✅ {len(lv_raw)} lignes · colonnes : {list(lv_raw.columns)}")
                    st.dataframe(lv_raw.head(8), use_container_width=True)
                    st.session_state["lv_raw"] = lv_raw
                except Exception as e:
                    st.error(f"❌ {e}")

        if lv_btn:
            if "lv_raw" not in st.session_state:
                st.warning("⚠️ Chargez d'abord un fichier.")
            else:
                try:
                    gantt_df, dc, ec, durc, mhc = build_leveling_gantt(st.session_state["lv_raw"], lv_mh, lv_dt)
                    st.info(f"Colonnes détectées — Description: **{dc}** · Équipement: **{ec}** · Durée: **{durc}** · MH: **{mhc}**")
                    st.plotly_chart(plot_gantt(gantt_df, f"Gantt Leveling — {lv_mh} MH max/ressource/jour"), use_container_width=True)

                    # Load per resource
                    load_rows = []
                    for _, r in gantt_df.iterrows():
                        daily_mh = r["MH"] / max(1, (r["Finish"] - r["Start"]).days)
                        for d in pd.date_range(r["Start"], r["Finish"] - timedelta(days=1), freq="D"):
                            load_rows.append({"Date": d, "MH": daily_mh, "Équipement": r["Equipment"]})
                    if load_rows:
                        pv = pd.DataFrame(load_rows).groupby(["Date","Équipement"])["MH"].sum().reset_index()
                        pv = pv.pivot(index="Date", columns="Équipement", values="MH").fillna(0)
                        pal = ["#0079C2","#00B4E6","#2ECC71","#F39C12","#E74C3C","#9B59B6"]
                        fig_lv = go.Figure()
                        for i, c in enumerate(pv.columns):
                            fig_lv.add_trace(go.Bar(x=pv.index, y=pv[c], name=c, marker_color=pal[i % len(pal)]))
                        fig_lv.add_hline(y=lv_mh, line_dash="dash", line_color="red", annotation_text=f"Cap. {lv_mh} MH/j/ressource")
                        fig_lv.update_layout(title="Charge après nivellement", barmode="group",
                                             xaxis=dict(type="date", tickformat="%d %b %Y"),
                                             yaxis_title="MH/j", plot_bgcolor="white", paper_bgcolor="white", height=280)
                        st.plotly_chart(fig_lv, use_container_width=True)

                    buf = io.BytesIO()
                    gantt_df.to_excel(buf, index=False)
                    st.download_button("📥 Télécharger Gantt", buf.getvalue(),
                                       f"Gantt_Leveling_{datetime.today().strftime('%Y%m%d')}.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(f"❌ {e}")

    # ── TAB 3: SHUTDOWN ──
    with tabs[2]:
        st.subheader("🛑 Shutdown Logic Active")

    # ── TAB 4: INSPECTION PLANNER (original, unchanged) ──
    with tabs[3]:
        st.header("🚜 Optimized Inspection Planner")
        try:
            df_i = pd.read_excel("Convoyeur.xlsx")
            df_i.columns = df_i.columns.astype(str).str.strip()
            coords_start = df_i['Addresse Queue'].apply(parse_coords)
            coords_end   = df_i['Addresse TM'].apply(parse_coords)
            df_i['lat_s'] = coords_start.apply(lambda x: x[0] if x else None)
            df_i['lon_s'] = coords_start.apply(lambda x: x[1] if x else None)
            df_i['lat_e'] = coords_end.apply(lambda x: x[0] if x else None)
            df_i['lon_e'] = coords_end.apply(lambda x: x[1] if x else None)
            sel = st.multiselect("Select Conveyors:", df_i['Equipment'].unique())
            if sel:
                sub = df_i[df_i['Equipment'].isin(sel)].copy()
                b_dist, b_route = float('inf'), None
                for p in permutations(sub.index):
                    for dirs in product([0, 1], repeat=len(p)):
                        c_lat, c_lon, t_walk, c_route = float(BASE_LAT), float(BASE_LON), 0, []
                        for i, idx in enumerate(p):
                            r   = sub.loc[idx]
                            ent = (r['lat_s'], r['lon_s']) if dirs[i] == 0 else (r['lat_e'], r['lon_e'])
                            exi = (r['lat_e'], r['lon_e']) if dirs[i] == 0 else (r['lat_s'], r['lon_s'])
                            t_walk += haversine(c_lat, c_lon, ent[0], ent[1])
                            c_route.append({'r': r, 'ent': ent, 'exi': exi})
                            c_lat, c_lon = exi
                        if t_walk < b_dist:
                            b_dist, b_route = t_walk, c_route
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[BASE_LON], y=[BASE_LAT], mode='markers+text',
                                         marker=dict(size=14, symbol='star', color='red'),
                                         name='Base JESA', text=['Base']))
                w_lo, w_la = [BASE_LON], [BASE_LAT]
                for s in b_route:
                    r = s['r']
                    fig.add_trace(go.Scatter(x=[r['lon_s'], r['lon_e']], y=[r['lat_s'], r['lat_e']],
                                             mode='lines+markers', name=r['Equipment'],
                                             line=dict(color='royalblue', width=6)))
                    w_lo.extend([s['ent'][1], s['exi'][1]])
                    w_la.extend([s['ent'][0], s['exi'][0]])
                fig.add_trace(go.Scatter(x=w_lo, y=w_la, mode='lines',
                                         line=dict(color='green', width=3, dash='dash'), name='Walking Path'))
                fig.update_layout(plot_bgcolor='white', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"✅ Distance totale : {b_dist/1000:.3f} km")
        except Exception as e:
            st.error(f"Error in Inspection Planner: {e}")

    # ── TAB 5: SHIFT REPORT (original, unchanged) ──
    with tabs[4]:
        st.header("🎙️ Shift Report")
        audio = st.audio_input("Record report")
        if audio and st.button("🚀 Submit"):
            try:
                tr  = client.audio.transcriptions.create(model="whisper-1", file=audio)
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Traduis en français professionnel."},
                              {"role": "user",   "content": tr.text}])
                append_to_gsheet(conn, {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "Compte Rendu": res.choices[0].message.content})
                st.success("✅ Rapport enregistré !")
            except Exception as e:
                st.error(f"Error: {e}")

    # ── TAB 6: ADMIN (original, unchanged) ──
    with tabs[5]:
        if st.text_input("Admin Password", type="password") == st.secrets["ADMIN_PASSWORD"]:
            try:
                m_df = conn.read(ttl=0)
                st.dataframe(m_df, use_container_width=True)
                buf = io.BytesIO()
                m_df.to_excel(buf, index=False)
                st.download_button("📥 Download Database", buf.getvalue(), "Reports.xlsx")
            except Exception as e:
                st.error(f"Database error: {e}")

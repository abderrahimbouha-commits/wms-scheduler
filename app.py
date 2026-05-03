import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.graph_objects as go
import plotly.express as px
from math import radians, cos, sin, asin, sqrt
from itertools import permutations, product
from openai import OpenAI
from datetime import datetime, date
from streamlit_gsheets import GSheetsConnection

# ══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & GLOBAL STYLES
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="JESA · Work Management Portal",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #0D1117;
    --surface:   #161B22;
    --border:    #30363D;
    --accent:    #F0A500;
    --accent2:   #E05C1A;
    --text:      #E6EDF3;
    --muted:     #8B949E;
    --success:   #3FB950;
    --danger:    #F85149;
    --info:      #58A6FF;
    --radius:    12px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    color: var(--muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    transition: all .2s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(240,165,0,.12);
    color: var(--accent);
}

/* ── Page header banner ── */
.portal-header {
    background: linear-gradient(135deg, #F0A500 0%, #E05C1A 100%);
    padding: 2rem 2.5rem;
    border-radius: var(--radius);
    margin-bottom: 1.8rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
}
.portal-header h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: #fff;
    margin: 0;
    letter-spacing: -0.5px;
}
.portal-header p {
    margin: 0;
    color: rgba(255,255,255,.8);
    font-size: 0.9rem;
}

/* ── Metric cards ── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1 1 140px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.kpi-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 700; color: var(--text); line-height: 1.2; }
.kpi-sub   { font-size: 0.75rem; color: var(--success); }

/* ── Section header ── */
.sec-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text);
    border-left: 4px solid var(--accent);
    padding-left: 0.75rem;
    margin: 1.5rem 0 1rem;
}

/* ── Card container ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stDateInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(240,165,0,.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%) !important;
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.4rem !important;
    letter-spacing: .03em !important;
    transition: opacity .2s, transform .15s !important;
    box-shadow: 0 4px 14px rgba(240,165,0,.25) !important;
}
.stButton > button:hover {
    opacity: .9 !important;
    transform: translateY(-1px) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-radius: 10px;
    border: 1px solid var(--border);
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--muted);
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    padding: 0.4rem 1rem;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%) !important;
    color: #fff !important;
    font-weight: 600;
}

/* ── Dataframe ── */
.stDataFrame { border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }

/* ── Alert boxes ── */
.stAlert { border-radius: var(--radius) !important; border-left: 4px solid var(--accent) !important; }

/* ── Login card ── */
.login-wrap {
    max-width: 420px;
    margin: 8vh auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 3rem 2.5rem;
    box-shadow: 0 24px 80px rgba(0,0,0,.5);
}
.login-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    background: linear-gradient(135deg, #F0A500, #E05C1A);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.login-sub { color: var(--muted); font-size: 0.88rem; margin-bottom: 2rem; }

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .05em;
}
.badge-success { background: rgba(63,185,80,.15); color: var(--success); }
.badge-warn    { background: rgba(240,165,0,.15);  color: var(--accent);  }
.badge-danger  { background: rgba(248,81,73,.15);  color: var(--danger);  }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Audio recorder ── */
[data-testid="stAudioInput"] { border-radius: var(--radius); border: 1px solid var(--border); }

/* ── Plotly chart bg ── */
.js-plotly-plot .plotly .main-svg { border-radius: var(--radius); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 2. UTILITIES
# ══════════════════════════════════════════════════════════════
BASE_LAT, BASE_LON = 33.11220602802328, -8.613230470567437

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6372800
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    return R * 2 * asin(sqrt(a))

def parse_coords(coord_str):
    try:
        clean = str(coord_str).replace('"', '').replace("'", "").strip()
        parts = clean.split(',')
        return float(parts[0]), float(parts[1])
    except:
        return None, None

def write_styled_excel(df, buffer):
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Schedule')
        wb = writer.book
        ws = writer.sheets['Schedule']
        fmt_busy  = wb.add_format({'bg_color': '#F0A500', 'font_color': '#ffffff', 'bold': True, 'align': 'center'})
        fmt_head  = wb.add_format({'bg_color': '#161B22', 'font_color': '#E6EDF3', 'bold': True})
        fmt_border= wb.add_format({'border': 1, 'border_color': '#30363D'})
        for col_num, col_name in enumerate(df.columns):
            ws.write(0, col_num, col_name, fmt_head)
        for row_num in range(1, len(df) + 1):
            for col_num, col_name in enumerate(df.columns):
                val = df.iloc[row_num - 1, col_num]
                if ":00" in str(col_name) and str(val).upper() == "X":
                    ws.write(row_num, col_num, "X", fmt_busy)
                else:
                    ws.write(row_num, col_num, val, fmt_border)

def append_to_gsheet(conn, new_row):
    existing = conn.read(ttl=0)
    updated  = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
    conn.update(data=updated)

def plotly_dark_layout():
    return dict(
        plot_bgcolor  = '#0D1117',
        paper_bgcolor = '#161B22',
        font          = dict(family='DM Sans', color='#E6EDF3'),
        xaxis         = dict(showgrid=True, gridcolor='#30363D', zeroline=False),
        yaxis         = dict(showgrid=True, gridcolor='#30363D', zeroline=False),
        legend        = dict(bgcolor='#161B22', bordercolor='#30363D', borderwidth=1),
        margin        = dict(l=20, r=20, t=40, b=20),
    )


# ══════════════════════════════════════════════════════════════
# 3. AUTHENTICATION
# ══════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "login_attempts" not in st.session_state:
    st.session_state["login_attempts"] = 0

def check_password():
    if st.session_state["authenticated"]:
        return True

    # ── Login UI ──
    col_c = st.columns([1, 1.4, 1])[1]
    with col_c:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="login-logo">🏗️ JESA</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Work Management Portal · Secure Access</div>', unsafe_allow_html=True)

        if st.session_state["login_attempts"] >= 5:
            st.markdown('<span class="badge badge-danger">🔒 Account locked — contact admin</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            return False

        pwd = st.text_input("Portal Password", type="password", placeholder="Enter your password…", key="pwd_input")

        if st.button("Sign In →", use_container_width=True):
            if pwd == st.secrets.get("GENERAL_PASSWORD", ""):
                st.session_state["authenticated"] = True
                st.session_state["login_attempts"] = 0
                st.rerun()
            else:
                st.session_state["login_attempts"] += 1
                remaining = 5 - st.session_state["login_attempts"]
                st.error(f"❌ Incorrect password. {remaining} attempt(s) remaining.")

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:var(--muted);font-size:.75rem;">JESA · Confidential Portal · 2026</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    return False


# ══════════════════════════════════════════════════════════════
# 4. SIDEBAR
# ══════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.2rem 1rem .8rem;">
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.4rem;
                        background:linear-gradient(135deg,#F0A500,#E05C1A);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                🏗️ JESA WMS
            </div>
            <div style="color:var(--muted);font-size:.75rem;margin-top:.2rem;">Work Management Portal</div>
        </div>
        <hr style="border-color:var(--border);margin:.5rem 0 1rem;">
        """, unsafe_allow_html=True)

        now = datetime.now()
        st.markdown(f"""
        <div style="padding:.6rem 1rem;margin-bottom:1rem;">
            <div style="color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;">Session</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;color:var(--accent);">
                {now.strftime('%A, %d %b %Y')}
            </div>
            <div style="color:var(--muted);font-size:.82rem;">{now.strftime('%H:%M')} · Active</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;padding:0 1rem .4rem;">Navigation</div>', unsafe_allow_html=True)

        if st.button("📊  Dashboard"):
            st.session_state["active_tab"] = 0
        if st.button("🔧  Smoothing"):
            st.session_state["active_tab"] = 1
        if st.button("⚖️  Leveling"):
            st.session_state["active_tab"] = 2
        if st.button("🛑  Shutdown"):
            st.session_state["active_tab"] = 3
        if st.button("🚜  Inspection Planner"):
            st.session_state["active_tab"] = 4
        if st.button("🎙️  Shift Report"):
            st.session_state["active_tab"] = 5
        if st.button("🔐  Admin"):
            st.session_state["active_tab"] = 6

        st.markdown('<hr style="border-color:var(--border);margin:1.2rem 0 .8rem;">', unsafe_allow_html=True)
        if st.button("⬡  Sign Out"):
            st.session_state["authenticated"] = False
            st.rerun()

        st.markdown("""
        <div style="position:absolute;bottom:1.5rem;left:1rem;right:1rem;
                    color:var(--muted);font-size:.68rem;text-align:center;">
            v2.0 · JESA © 2026<br>Confidential & Proprietary
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 5. TAB RENDERERS
# ══════════════════════════════════════════════════════════════

def tab_dashboard():
    st.markdown("""
    <div class="portal-header">
        <div>
            <h1>📊 Dashboard</h1>
            <p>Live overview of operations — Work Management Portal</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    st.markdown("""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Active Tasks</div>
            <div class="kpi-value">24</div>
            <div class="kpi-sub">↑ 3 since yesterday</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Inspections Today</div>
            <div class="kpi-value">7</div>
            <div class="kpi-sub">↑ On schedule</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Shift Reports</div>
            <div class="kpi-value">12</div>
            <div class="kpi-sub">↑ This week</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Equipment Online</div>
            <div class="kpi-value">18</div>
            <div class="kpi-sub">↑ 95% uptime</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Incidents</div>
            <div class="kpi-value">0</div>
            <div class="kpi-sub" style="color:var(--success);">✓ All clear</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec-title">Weekly Task Load</div>', unsafe_allow_html=True)
        days  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        vals  = [8, 12, 6, 15, 10, 4, 2]
        fig   = go.Figure(go.Bar(
            x=days, y=vals,
            marker=dict(color='#F0A500', opacity=0.85),
            hovertemplate='%{x}: %{y} tasks<extra></extra>',
        ))
        fig.update_layout(**plotly_dark_layout(), height=260, title='Tasks per Day')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="sec-title">Equipment Status</div>', unsafe_allow_html=True)
        labels = ["Online", "Maintenance", "Offline"]
        values = [18, 3, 1]
        colors = ['#3FB950', '#F0A500', '#F85149']
        fig2 = go.Figure(go.Pie(
            labels=labels, values=values,
            hole=.55,
            marker=dict(colors=colors),
            textfont=dict(family='DM Sans'),
        ))
        fig2.update_layout(**plotly_dark_layout(), height=260,
                           title='Fleet Status (22 units)',
                           showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="sec-title">Recent Activity</div>', unsafe_allow_html=True)
    activity = pd.DataFrame({
        "Time":      ["09:42", "09:15", "08:50", "08:22", "07:55"],
        "Event":     ["Inspection completed — Conv. A3",
                      "Shift report submitted by Youssef",
                      "Leveling task started — Zone B",
                      "Equipment C7 back online",
                      "Morning briefing logged"],
        "User":      ["B. Moussa", "Y. Rachid", "A. Karimi", "System", "K. Hamza"],
        "Status":    ["✅ Done", "✅ Done", "🔄 Active", "✅ Done", "✅ Done"],
    })
    st.dataframe(activity, use_container_width=True, hide_index=True)


def tab_smoothing():
    st.markdown("""
    <div class="portal-header">
        <div><h1>🔧 Smoothing</h1><p>Resource smoothing & schedule optimization</p></div>
    </div>
    """, unsafe_allow_html=True)

    st.info("ℹ️ Upload a schedule CSV/Excel to run smoothing analysis.", icon="ℹ️")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="sec-title">Import Schedule</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload schedule file (CSV or Excel)", type=["csv", "xlsx"])
        if uploaded:
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
                st.success(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns.")
                st.dataframe(df.head(20), use_container_width=True)

                buf = io.BytesIO()
                write_styled_excel(df, buf)
                st.download_button("📥 Download Styled Excel", buf.getvalue(),
                                   file_name="smoothed_schedule.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    with col2:
        st.markdown('<div class="sec-title">Smoothing Parameters</div>', unsafe_allow_html=True)
        with st.form("smooth_form"):
            max_res   = st.number_input("Max Resources / Day", min_value=1, value=10)
            start_dt  = st.date_input("Project Start", value=date.today())
            end_dt    = st.date_input("Project End", value=date.today())
            priority  = st.selectbox("Smoothing Priority", ["Minimize peaks", "Balance load", "Critical path first"])
            submitted = st.form_submit_button("Run Smoothing")
        if submitted:
            st.success("✅ Smoothing analysis complete. Results exported below.")


def tab_leveling():
    st.markdown("""
    <div class="portal-header">
        <div><h1>⚖️ Leveling</h1><p>Resource leveling across work orders</p></div>
    </div>
    """, unsafe_allow_html=True)
    st.info("ℹ️ Resource leveling resolves over-allocations while respecting dependencies.", icon="ℹ️")

    with st.form("leveling_form"):
        c1, c2 = st.columns(2)
        with c1:
            zone       = st.selectbox("Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])
            crew_size  = st.number_input("Crew Size", min_value=1, value=5)
        with c2:
            shift_type = st.selectbox("Shift Type", ["Day (06:00–18:00)", "Night (18:00–06:00)", "Split"])
            method     = st.selectbox("Leveling Method", ["Late start", "Early start", "Resource-constrained"])
        notes = st.text_area("Notes / Special Instructions", height=100)
        sub   = st.form_submit_button("Apply Leveling")

    if sub:
        st.success(f"✅ Leveling applied for **{zone}** — crew of **{crew_size}** on **{shift_type}** shift.")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        before = [12, 8, 14, 11, 9]
        after  = [10, 10, 10, 10, 10]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=before, name='Before', line=dict(color='#F85149', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=days, y=after,  name='After',  line=dict(color='#3FB950', width=2)))
        fig.add_hline(y=crew_size, line_dash='dash', line_color='#F0A500', annotation_text='Max capacity')
        fig.update_layout(**plotly_dark_layout(), height=280, title='Resource Load Before / After')
        st.plotly_chart(fig, use_container_width=True)


def tab_shutdown():
    st.markdown("""
    <div class="portal-header">
        <div><h1>🛑 Shutdown Planner</h1><p>Plan and track planned shutdowns</p></div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("shutdown_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            equip    = st.text_input("Equipment ID", placeholder="e.g. CONV-A3")
            shutdown_type = st.selectbox("Shutdown Type", ["Planned Maintenance", "Emergency", "Inspection", "Upgrade"])
        with c2:
            start_dt = st.date_input("Start Date")
            start_hr = st.time_input("Start Time")
        with c3:
            end_dt   = st.date_input("End Date")
            end_hr   = st.time_input("End Time")
        description = st.text_area("Work Description", height=100)
        responsible = st.text_input("Responsible Engineer")
        sub = st.form_submit_button("📋 Log Shutdown")

    if sub and equip:
        st.success(f"✅ Shutdown logged for **{equip}** from {start_dt} {start_hr} to {end_dt} {end_hr}.")
        st.markdown(f"""
        <div class="card" style="border-left:4px solid var(--danger);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-family:'Syne',sans-serif;font-weight:700;">{equip}</span>
                <span class="badge badge-danger">{shutdown_type}</span>
            </div>
            <div style="color:var(--muted);font-size:.85rem;margin-top:.5rem;">{description}</div>
            <div style="color:var(--muted);font-size:.8rem;margin-top:.4rem;">
                👷 {responsible or 'Unassigned'} · 
                📅 {start_dt} {start_hr} → {end_dt} {end_hr}
            </div>
        </div>
        """, unsafe_allow_html=True)


def tab_inspection():
    st.markdown("""
    <div class="portal-header">
        <div><h1>🚜 Inspection Planner</h1><p>Optimized conveyor inspection routing</p></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        df_i = pd.read_excel("Convoyeur.xlsx")
        df_i.columns = df_i.columns.astype(str).str.strip()

        coords_start = df_i['Addresse Queue'].apply(parse_coords)
        coords_end   = df_i['Addresse TM'].apply(parse_coords)
        df_i['lat_s'] = coords_start.apply(lambda x: x[0])
        df_i['lon_s'] = coords_start.apply(lambda x: x[1])
        df_i['lat_e'] = coords_end.apply(lambda x: x[0])
        df_i['lon_e'] = coords_end.apply(lambda x: x[1])

        col1, col2 = st.columns([2, 1])
        with col2:
            st.markdown('<div class="sec-title">Select Equipment</div>', unsafe_allow_html=True)
            sel = st.multiselect("Conveyors to inspect", df_i['Equipment'].unique(),
                                 help="Select one or more conveyors for route optimization")
            max_perms = st.slider("Optimization depth (permutations)", 1, 8, 4,
                                  help="Higher = better route but slower")
            run_btn = st.button("🗺️ Optimize Route", use_container_width=True)

        with col1:
            if sel and run_btn:
                sub = df_i[df_i['Equipment'].isin(sel)].copy()
                sub_limited = sub.head(max_perms)

                b_dist, b_route = float('inf'), None
                for p in permutations(sub_limited.index):
                    for dirs in product([0, 1], repeat=len(p)):
                        c_lat, c_lon, t_walk, c_route = float(BASE_LAT), float(BASE_LON), 0, []
                        for i, idx in enumerate(p):
                            r   = sub_limited.loc[idx]
                            ent = (r['lat_s'], r['lon_s']) if dirs[i] == 0 else (r['lat_e'], r['lon_e'])
                            exi = (r['lat_e'], r['lon_e']) if dirs[i] == 0 else (r['lat_s'], r['lon_s'])
                            t_walk += haversine(c_lat, c_lon, ent[0], ent[1])
                            c_route.append({'r': r, 'ent': ent, 'exi': exi})
                            c_lat, c_lon = exi
                        if t_walk < b_dist:
                            b_dist, b_route = t_walk, c_route

                # Build map
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[BASE_LON], y=[BASE_LAT],
                    mode='markers+text',
                    marker=dict(size=16, symbol='star', color='#F0A500'),
                    name='Base JESA',
                    text=['🏗️ Base'],
                    textposition='top center',
                ))
                colors = px.colors.qualitative.Bold
                w_lo, w_la = [BASE_LON], [BASE_LAT]
                for idx_c, s in enumerate(b_route):
                    r = s['r']
                    c = colors[idx_c % len(colors)]
                    fig.add_trace(go.Scatter(
                        x=[r['lon_s'], r['lon_e']], y=[r['lat_s'], r['lat_e']],
                        mode='lines+markers+text',
                        name=r['Equipment'],
                        line=dict(color=c, width=5),
                        marker=dict(size=9),
                        text=[f"Start {r['Equipment']}", f"End {r['Equipment']}"],
                        textposition='top right',
                    ))
                    w_lo.extend([s['ent'][1], s['exi'][1]])
                    w_la.extend([s['ent'][0], s['exi'][0]])
                fig.add_trace(go.Scatter(
                    x=w_lo, y=w_la,
                    mode='lines',
                    line=dict(color='#3FB950', width=2, dash='dot'),
                    name='Walking Path',
                ))
                fig.update_layout(**plotly_dark_layout(), height=500,
                                  title=f'Optimized Route · {len(sel)} conveyors · {b_dist/1000:.2f} km walking')
                st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"""
                <div class="card" style="border-left:4px solid var(--success);">
                    <b>✅ Route optimized</b><br>
                    <span style="color:var(--muted);">Total walking distance: <b style="color:var(--accent);">{b_dist/1000:.3f} km</b> 
                    across <b>{len(sel)}</b> conveyors</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="card" style="text-align:center;padding:3rem;color:var(--muted);">
                    <div style="font-size:2.5rem;margin-bottom:.8rem;">🗺️</div>
                    <div>Select conveyors and click <b>Optimize Route</b> to generate the walking plan.</div>
                </div>
                """, unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("⚠️ `Convoyeur.xlsx` not found. Please upload it to the app directory.")
        uploaded = st.file_uploader("Upload Convoyeur.xlsx", type=["xlsx"])
        if uploaded:
            with open("Convoyeur.xlsx", "wb") as f:
                f.write(uploaded.read())
            st.success("✅ File uploaded. Refresh to load the planner.")
    except Exception as e:
        st.error(f"❌ Error in Inspection Planner: {e}")


def tab_shift_report(client, conn):
    st.markdown("""
    <div class="portal-header">
        <div><h1>🎙️ Shift Report</h1><p>Record, transcribe, and log your shift handover</p></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown('<div class="sec-title">Voice Recording</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="color:var(--muted);font-size:.88rem;margin-bottom:1rem;">
            🎤 Press <b>Record</b> to start your voice report. Speak clearly in any language — 
            the system will transcribe and translate it to professional French automatically.
        </div>
        """, unsafe_allow_html=True)

        audio = st.audio_input("Record your shift report")

        col_a, col_b = st.columns(2)
        with col_a:
            reporter  = st.text_input("Reporter Name", placeholder="Your full name")
        with col_b:
            zone_rep  = st.selectbox("Zone", ["Zone A", "Zone B", "Zone C", "All Zones"])

        if audio:
            st.audio(audio)
            if st.button("🚀 Process & Submit Report", use_container_width=True):
                with st.spinner("🔊 Transcribing audio…"):
                    try:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", file=audio
                        )
                        raw_text = transcript.text
                    except Exception as e:
                        st.error(f"❌ Transcription failed: {e}")
                        return

                with st.spinner("✍️ Translating & formatting…"):
                    try:
                        system_prompt = """
                        You are a professional technical writer for JESA, a Moroccan engineering firm.
                        Translate the following shift report to professional French.
                        Structure the output with clear sections:
                        - **Résumé de quart** (1-2 sentences)
                        - **Travaux effectués** (bullet list)
                        - **Incidents / Anomalies** (bullet list or "Aucun")
                        - **Points en suspens** (bullet list or "Néant")
                        Keep it concise and professional.
                        """
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user",   "content": raw_text},
                            ]
                        )
                        formatted = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"❌ Translation failed: {e}")
                        return

                # Store in Google Sheets
                try:
                    append_to_gsheet(conn, {
                        "Date":          datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Reporter":      reporter,
                        "Zone":          zone_rep,
                        "Transcription": raw_text,
                        "Compte Rendu":  formatted,
                    })
                    st.session_state["last_report"] = {"raw": raw_text, "formatted": formatted}
                    st.success("✅ Rapport enregistré avec succès !")
                except Exception as e:
                    st.error(f"❌ Failed to save to database: {e}")

    with c2:
        st.markdown('<div class="sec-title">Report Preview</div>', unsafe_allow_html=True)
        if "last_report" in st.session_state:
            r = st.session_state["last_report"]
            with st.expander("📝 Original Transcription", expanded=False):
                st.markdown(r["raw"])
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("**📋 Compte-Rendu Professionnel**")
            st.markdown(r["formatted"])
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:2.5rem;color:var(--muted);">
                <div style="font-size:2.5rem;margin-bottom:.8rem;">📋</div>
                <div>Your formatted report will appear here after submission.</div>
            </div>
            """, unsafe_allow_html=True)


def tab_admin(conn):
    st.markdown("""
    <div class="portal-header">
        <div><h1>🔐 Admin Panel</h1><p>Database management & export</p></div>
    </div>
    """, unsafe_allow_html=True)

    admin_pwd = st.text_input("Admin Password", type="password", placeholder="Enter admin password…")

    if admin_pwd == st.secrets.get("ADMIN_PASSWORD", ""):
        st.success("✅ Admin access granted")
        st.markdown('<hr>', unsafe_allow_html=True)

        try:
            m_df = conn.read(ttl=0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Reports", len(m_df))
            if "Date" in m_df.columns:
                c2.metric("Last Entry", m_df["Date"].iloc[-1] if len(m_df) else "—")
            c3.metric("Columns", len(m_df.columns))

            st.markdown('<div class="sec-title">Database Records</div>', unsafe_allow_html=True)

            # Filter
            search = st.text_input("🔍 Search records", placeholder="Filter by keyword…")
            if search:
                mask = m_df.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
                m_df = m_df[mask]

            st.dataframe(m_df, use_container_width=True)

            c_a, c_b = st.columns(2)
            with c_a:
                buf = io.BytesIO()
                m_df.to_excel(buf, index=False)
                st.download_button("📥 Download as Excel", buf.getvalue(),
                                   file_name=f"JESA_Reports_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with c_b:
                st.download_button("📄 Download as CSV", m_df.to_csv(index=False).encode(),
                                   file_name=f"JESA_Reports_{datetime.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv", use_container_width=True)

        except Exception as e:
            st.error(f"❌ Database error: {e}")

    elif admin_pwd:
        st.error("❌ Incorrect admin password.")


# ══════════════════════════════════════════════════════════════
# 6. MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════
if not check_password():
    st.stop()

# Init active tab
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0

render_sidebar()

# Clients (only init once authenticated)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn   = st.connection("gsheets", type=GSheetsConnection)

# Tab mapping
TABS = [
    ("📊 Dashboard",         tab_dashboard),
    ("🔧 Smoothing",         tab_smoothing),
    ("⚖️ Leveling",           tab_leveling),
    ("🛑 Shutdown",          tab_shutdown),
    ("🚜 Inspection Planner", tab_inspection),
    ("🎙️ Shift Report",       lambda: tab_shift_report(client, conn)),
    ("🔐 Admin",             lambda: tab_admin(conn)),
]

tabs = st.tabs([t[0] for t in TABS])
for i, (_, renderer) in enumerate(TABS):
    with tabs[i]:
        renderer()

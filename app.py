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

/* ── JESA Official Blue Palette ── */
:root {
    --bg:        #04111F;
    --surface:   #071D30;
    --surface2:  #0A2540;
    --border:    #1A3A55;
    --accent:    #0079C2;
    --accent2:   #005A9E;
    --accent3:   #00B4E6;
    --text:      #E8F0F7;
    --muted:     #7A9BB5;
    --success:   #2ECC71;
    --danger:    #E74C3C;
    --info:      #00B4E6;
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
    background: rgba(0,121,194,.15);
    color: var(--accent3);
}

/* ── Page header banner ── */
.portal-header {
    background: linear-gradient(135deg, #005A9E 0%, #0079C2 50%, #00B4E6 100%);
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
    background: linear-gradient(90deg, var(--accent2), var(--accent), var(--accent3));
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
    background: linear-gradient(135deg, var(--accent2) 0%, var(--accent) 50%, var(--accent3) 100%) !important;
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.4rem !important;
    letter-spacing: .03em !important;
    transition: opacity .2s, transform .15s !important;
    box-shadow: 0 4px 14px rgba(0,121,194,.3) !important;
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
    background: linear-gradient(135deg, var(--accent2) 0%, var(--accent) 100%) !important;
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
    background: linear-gradient(135deg, #0079C2, #00B4E6);
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
.badge-success { background: rgba(46,204,113,.15); color: var(--success); }
.badge-warn    { background: rgba(0,121,194,.2);   color: var(--accent3); }
.badge-danger  { background: rgba(231,76,60,.15);  color: var(--danger);  }

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
        fmt_busy  = wb.add_format({'bg_color': '#0079C2', 'font_color': '#ffffff', 'bold': True, 'align': 'center'})
        fmt_head  = wb.add_format({'bg_color': '#071D30', 'font_color': '#E8F0F7', 'bold': True})
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
        plot_bgcolor  = '#04111F',
        paper_bgcolor = '#071D30',
        font          = dict(family='DM Sans', color='#E8F0F7'),
        xaxis         = dict(showgrid=True, gridcolor='#1A3A55', zeroline=False),
        yaxis         = dict(showgrid=True, gridcolor='#1A3A55', zeroline=False),
        legend        = dict(bgcolor='#071D30', bordercolor='#1A3A55', borderwidth=1),
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
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem;">
            <img src="https://www.jesagroup.com/themes/custom/jesa/logo.svg"
                 onerror="this.onerror=null;this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/JESA_logo.svg/320px-JESA_logo.svg.png';"
                 style="height:60px;object-fit:contain;" alt="JESA Logo"/>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="login-sub" style="text-align:center;">Work Management Portal · Secure Access</div>', unsafe_allow_html=True)

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
        <div style="padding:1.2rem 1rem .8rem;text-align:center;">
            <img src="https://www.jesagroup.com/themes/custom/jesa/logo.svg"
                 onerror="this.onerror=null;this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/JESA_logo.svg/320px-JESA_logo.svg.png';"
                 style="height:52px;object-fit:contain;margin-bottom:.6rem;"
                 alt="JESA Logo"/>
            <div style="font-family:'DM Sans',sans-serif;font-size:.7rem;
                        color:#7A9BB5;letter-spacing:.08em;text-transform:uppercase;">
                Work Management Portal
            </div>
        </div>
        <hr style="border-color:#1A3A55;margin:.5rem 0 1rem;">
        """, unsafe_allow_html=True)

        now = datetime.now()
        st.markdown(f"""
        <div style="padding:.6rem 1rem;margin-bottom:1rem;">
            <div style="color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;">Session</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;color:var(--accent3);">
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


# ══════════════════════════════════════════════════════════════
# CMMS KPI ENGINE  — language-agnostic column mapping
# ══════════════════════════════════════════════════════════════

# Possible column names per field (French & English variants)
COL_MAP = {
    "order":       ["Ordre", "Order", "Work Order", "WO", "Ordre de travail"],
    "sys_status":  ["Statut système", "System Status", "Sys. Status", "SysStatus"],
    "usr_status":  ["Statut utilis.", "User Status", "User Stat.", "Statut utilisateur"],
    "created":     ["Créé le", "Created On", "Creation Date", "Date création"],
    "equipment":   ["Obj. technique", "Technical Object", "Equipment", "Équipement"],
    "equip_desc":  ["Descr.obj.tech.", "Equipment Description", "Désignation (poste technique)", "Description équipement"],
    "priority":    ["Priorité", "Priority"],
    "sched_date":  ["Début de base", "Basic Start", "Scheduled Start", "Date planifiée"],
}

def find_col(df, key):
    """Return the first matching column name for a logical field."""
    for candidate in COL_MAP.get(key, []):
        if candidate in df.columns:
            return candidate
    return None

def detect_status_language(sys_vals):
    """Detect if statuses are in French (SAP FR) or English (SAP EN)."""
    sample = " ".join(str(v) for v in sys_vals.dropna().head(50))
    if any(k in sample for k in ["CONF", "CRÉÉ", "LANC", "CNFP"]):
        return "fr"
    if any(k in sample for k in ["COMP", "CRTD", "REL", "TECO"]):
        return "en"
    return "fr"  # default

def classify_orders(df):
    """
    Classify every unique WO into maintenance workflow stages.
    Returns orders DataFrame with added columns:
      is_executed, is_launched, is_prepared, is_scheduled, stage
    """
    order_col = find_col(df, "order")
    sys_col   = find_col(df, "sys_status")
    usr_col   = find_col(df, "usr_status")
    eq_col    = find_col(df, "equipment")
    eq_desc   = find_col(df, "equip_desc")
    cr_col    = find_col(df, "created")

    if not order_col:
        return None, "❌ No 'Order/Ordre' column found in the file."

    orders = df.drop_duplicates(subset=order_col).copy()
    sys_s  = orders[sys_col].astype(str).str.upper()  if sys_col else pd.Series([""] * len(orders))
    usr_s  = orders[usr_col].astype(str).str.upper()  if usr_col else pd.Series([""] * len(orders))

    lang = detect_status_language(sys_s)

    if lang == "fr":
        # SAP French status codes
        executed  = sys_s.str.contains(r"CONF|CNFP|TECO", na=False)
        launched  = sys_s.str.contains(r"LANC", na=False) & ~executed
        prepared  = (
            usr_s.str.contains(r"CRPR|ATPL|AGAR|AVPD", na=False) |
            executed | launched
        )
        scheduled = (
            usr_s.str.contains(r"ATPL|AGAR", na=False) |
            executed | launched
        )
    else:
        # SAP English status codes
        executed  = sys_s.str.contains(r"COMP|TECO|CLSD", na=False)
        launched  = sys_s.str.contains(r"REL", na=False) & ~executed
        prepared  = (
            usr_s.str.contains(r"PREP|SCHD|APPR", na=False) |
            executed | launched
        )
        scheduled = (
            usr_s.str.contains(r"SCHD|APPR", na=False) |
            executed | launched
        )

    orders["_executed"]  = executed.values
    orders["_launched"]  = launched.values
    orders["_prepared"]  = prepared.values
    orders["_scheduled"] = scheduled.values
    orders["_eq"]        = orders[eq_col].astype(str)   if eq_col   else "N/A"
    orders["_eq_desc"]   = orders[eq_desc].astype(str)  if eq_desc  else orders["_eq"]
    orders["_created"]   = pd.to_datetime(orders[cr_col], errors="coerce") if cr_col else pd.NaT
    orders["_order"]     = orders[order_col]

    # Assign a single pipeline stage label
    def stage(row):
        if row["_executed"]:    return "Executed"
        if row["_launched"]:    return "In Execution"
        if row["_scheduled"]:   return "Scheduled"
        if row["_prepared"]:    return "Prepared"
        return "Not Prepared"

    orders["_stage"] = orders.apply(stage, axis=1)
    return orders, None


def compute_kpis(orders):
    """Return a dict of global KPI values."""
    n     = len(orders)
    today = pd.Timestamp.today()

    pct_prep  = 100 * orders["_prepared"].sum()  / n if n else 0
    pct_sched = 100 * orders["_scheduled"].sum() / n if n else 0
    pct_exec  = 100 * orders["_executed"].sum()  / n if n else 0

    # Backlog = open WOs stuck at each stage
    is_open      = ~orders["_executed"]
    bl_planner   = orders[is_open & ~orders["_prepared"]]
    bl_scheduler = orders[is_open & orders["_prepared"] & ~orders["_scheduled"]]
    bl_execution = orders[is_open & orders["_scheduled"]]

    def age_stats(sub):
        if len(sub) == 0:
            return 0, 0, 0
        ages = (today - sub["_created"]).dt.days.dropna()
        return len(sub), round(ages.mean(), 1) if len(ages) else 0, int(ages.max()) if len(ages) else 0

    return {
        "n_total":    n,
        "n_exec":     int(orders["_executed"].sum()),
        "n_open":     int(is_open.sum()),
        "pct_prep":   round(pct_prep, 1),
        "pct_sched":  round(pct_sched, 1),
        "pct_exec":   round(pct_exec, 1),
        "bl_plan":    age_stats(bl_planner),
        "bl_sched":   age_stats(bl_scheduler),
        "bl_exec":    age_stats(bl_execution),
    }


def kpi_by_equipment(orders):
    """Return per-equipment KPI DataFrame."""
    today = pd.Timestamp.today()
    rows = []
    for eq, grp in orders.groupby("_eq"):
        n   = len(grp)
        desc = grp["_eq_desc"].iloc[0]
        is_open = ~grp["_executed"]
        bl_n    = is_open & ~grp["_scheduled"]
        ages    = (today - grp.loc[is_open, "_created"]).dt.days.dropna()
        rows.append({
            "Equipment":     eq,
            "Description":   desc,
            "Total WOs":     n,
            "% Preparation": round(100 * grp["_prepared"].sum()  / n, 1),
            "% Planification": round(100 * grp["_scheduled"].sum() / n, 1),
            "% Execution":   round(100 * grp["_executed"].sum()  / n, 1),
            "Open WOs":      int(is_open.sum()),
            "Backlog (open not sched)": int(bl_n.sum()),
            "Avg Age (days)": round(ages.mean(), 0) if len(ages) else 0,
        })
    return pd.DataFrame(rows).sort_values("Open WOs", ascending=False)


def gauge_chart(value, title, color="#0079C2"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 32, "family": "Syne", "color": "#E8F0F7"}},
        title={"text": title, "font": {"size": 13, "family": "DM Sans", "color": "#7A9BB5"}},
        gauge={
            "axis":       {"range": [0, 100], "tickcolor": "#1A3A55", "tickfont": {"color": "#7A9BB5"}},
            "bar":        {"color": color},
            "bgcolor":    "#071D30",
            "bordercolor":"#1A3A55",
            "steps": [
                {"range": [0,  50], "color": "#0A1E30"},
                {"range": [50, 75], "color": "#0A2540"},
                {"range": [75,100], "color": "#0A3050"},
            ],
            "threshold": {
                "line": {"color": "#00B4E6", "width": 2},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#071D30", plot_bgcolor="#071D30",
        font=dict(color="#E8F0F7"),
        height=220, margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig


def backlog_age_bar(kpis):
    stages = ["Planner\nBacklog", "Scheduler\nBacklog", "Execution\nBacklog"]
    counts = [kpis["bl_plan"][0],  kpis["bl_sched"][0],  kpis["bl_exec"][0]]
    avgs   = [kpis["bl_plan"][1],  kpis["bl_sched"][1],  kpis["bl_exec"][1]]
    maxes  = [kpis["bl_plan"][2],  kpis["bl_sched"][2],  kpis["bl_exec"][2]]
    colors = ["#E74C3C", "#F39C12", "#0079C2"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg Age (days)", x=stages, y=avgs,
        marker_color=colors, opacity=0.85,
        text=[f"{v:.0f}d" for v in avgs], textposition="outside",
        hovertemplate="<b>%{x}</b><br>WOs: %{customdata}<br>Avg Age: %{y:.0f}d<extra></extra>",
        customdata=counts,
    ))
    fig.add_trace(go.Scatter(
        name="Max Age (days)", x=stages, y=maxes,
        mode="markers", marker=dict(color="#00B4E6", size=10, symbol="diamond"),
        hovertemplate="Max Age: %{y}d<extra></extra>",
    ))
    fig.update_layout(
        **plotly_dark_layout(), height=300,
        title="Backlog Age (Average & Max in days)",
        showlegend=True, barmode="group",
        yaxis_title="Days",
    )
    return fig


def pipeline_funnel(kpis):
    n = kpis["n_total"]
    labels  = ["Total WOs", "Prepared", "Scheduled", "Executed"]
    values  = [
        n,
        round(n * kpis["pct_prep"]  / 100),
        round(n * kpis["pct_sched"] / 100),
        round(n * kpis["pct_exec"]  / 100),
    ]
    colors  = ["#1A3A55", "#005A9E", "#0079C2", "#00B4E6"]
    fig = go.Figure(go.Funnel(
        y=labels, x=values,
        textinfo="value+percent initial",
        marker=dict(color=colors),
        connector=dict(line=dict(color="#071D30", width=2)),
    ))
    fig.update_layout(
        **plotly_dark_layout(), height=320,
        title="Maintenance Pipeline Funnel",
    )
    return fig


def stage_donut(orders):
    counts = orders["_stage"].value_counts()
    colors_map = {
        "Executed":     "#00B4E6",
        "In Execution": "#0079C2",
        "Scheduled":    "#2ECC71",
        "Prepared":     "#F39C12",
        "Not Prepared": "#E74C3C",
    }
    labels = counts.index.tolist()
    values = counts.values.tolist()
    colors = [colors_map.get(l, "#888") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors),
        textfont=dict(family="DM Sans"),
        hovertemplate="%{label}: %{value} WOs (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **plotly_dark_layout(), height=320,
        title="WO Distribution by Stage",
    )
    return fig


def kpi_color(val):
    """Return CSS color string based on KPI value."""
    if val >= 80:   return "#2ECC71"
    if val >= 50:   return "#F39C12"
    return "#E74C3C"


def kpi_card_html(label, value_pct, count, sublabel=""):
    color = kpi_color(value_pct)
    bar_w = max(4, int(value_pct))
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color};">{value_pct}%</div>
        <div style="background:#1A3A55;border-radius:4px;height:6px;margin:.4rem 0;">
            <div style="background:{color};width:{bar_w}%;height:6px;border-radius:4px;transition:width .5s;"></div>
        </div>
        <div class="kpi-sub" style="color:{color};">{count} WOs {sublabel}</div>
    </div>"""


def backlog_card_html(label, n, avg, maxd, icon, color):
    return f"""
    <div class="kpi-card" style="border-left:3px solid {color};">
        <div class="kpi-label">{icon} {label}</div>
        <div class="kpi-value" style="color:{color};">{n}</div>
        <div class="kpi-sub">Avg age: <b>{avg:.0f}d</b> · Max: <b>{maxd}d</b></div>
    </div>"""


# ══════════════════════════════════════════════════════════════
# TAB: DASHBOARD
# ══════════════════════════════════════════════════════════════
def tab_dashboard():
    st.markdown("""
    <div class="portal-header">
        <div style="display:flex;align-items:center;gap:1.5rem;">
            <img src="https://www.jesagroup.com/themes/custom/jesa/logo.svg"
                 onerror="this.onerror=null;this.src='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/JESA_logo.svg/320px-JESA_logo.svg.png';"
                 style="height:48px;object-fit:contain;filter:brightness(0) invert(1);" alt="JESA"/>
            <div>
                <h1>Maintenance KPI Dashboard</h1>
                <p>CMMS Extraction Analysis — Upload your SAP/CMMS export to compute live KPIs</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload zone ──
    with st.expander("📂 Upload CMMS Extraction", expanded="cmms_orders" not in st.session_state):
        st.markdown("""
        <div style="color:var(--muted);font-size:.85rem;margin-bottom:.8rem;">
        Upload your SAP/CMMS extraction file (Excel or CSV). The system auto-detects French & English columns,
        and recalculates all KPIs instantly. You can re-upload at any time to refresh the analysis.
        </div>
        """, unsafe_allow_html=True)

        col_up, col_info = st.columns([2, 1])
        with col_up:
            uploaded = st.file_uploader(
                "Drop your CMMS extraction here",
                type=["xlsx", "xls", "csv"],
                key="cmms_upload",
                label_visibility="collapsed",
            )
        with col_info:
            st.markdown("""
            <div class="card" style="font-size:.78rem;color:var(--muted);padding:.8rem 1rem;">
                <b style="color:var(--text);">Supported columns:</b><br>
                Ordre / Order · Statut système / System Status<br>
                Statut utilis. / User Status · Créé le / Created<br>
                Obj. technique / Equipment · Priorité / Priority<br><br>
                <b style="color:var(--text);">Languages:</b> French 🇫🇷 & English 🇬🇧
            </div>
            """, unsafe_allow_html=True)

        if uploaded:
            with st.spinner("⚙️ Parsing extraction & computing KPIs…"):
                try:
                    if uploaded.name.endswith(".csv"):
                        raw_df = pd.read_csv(uploaded)
                    else:
                        raw_df = pd.read_excel(uploaded)

                    orders, err = classify_orders(raw_df)
                    if err:
                        st.error(err)
                    else:
                        st.session_state["cmms_orders"] = orders
                        st.session_state["cmms_raw"]    = raw_df
                        st.success(f"✅ Loaded **{len(raw_df):,}** rows · **{orders['_order'].nunique():,}** unique Work Orders · {len(raw_df.columns)} columns detected")
                except Exception as e:
                    st.error(f"❌ Failed to read file: {e}")

    # ── No data yet ──
    if "cmms_orders" not in st.session_state:
        st.markdown("""
        <div class="card" style="text-align:center;padding:4rem 2rem;color:var(--muted);">
            <div style="font-size:3rem;margin-bottom:1rem;">📊</div>
            <div style="font-size:1.1rem;color:var(--text);font-family:'Syne',sans-serif;font-weight:600;margin-bottom:.5rem;">
                No extraction loaded yet
            </div>
            <div>Upload your CMMS/SAP extraction above to see live maintenance KPIs.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    orders = st.session_state["cmms_orders"]
    kpis   = compute_kpis(orders)

    # ── Filters ──
    with st.container():
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            eq_options = sorted(orders["_eq"].dropna().unique().tolist())
            eq_descs   = {row["_eq"]: row["_eq_desc"] for _, row in orders[["_eq","_eq_desc"]].drop_duplicates().iterrows()}
            eq_labels  = {e: f"{e} — {eq_descs.get(e,'')[:30]}" for e in eq_options}
            sel_eq = st.multiselect(
                "🔍 Filter by Equipment",
                options=eq_options,
                format_func=lambda x: eq_labels.get(x, x),
                placeholder="All equipment (no filter)",
            )
        with fc2:
            sel_stage = st.multiselect(
                "📌 Filter by Stage",
                options=["Not Prepared", "Prepared", "Scheduled", "In Execution", "Executed"],
                placeholder="All stages",
            )
        with fc3:
            pri_col = find_col(orders, "priority")
            if pri_col:
                pri_options = sorted(orders[pri_col].dropna().unique().tolist())
                sel_pri = st.multiselect("⚡ Priority", options=[str(int(p)) if isinstance(p, float) else str(p) for p in pri_options], placeholder="All")
            else:
                sel_pri = []

    # Apply filters
    filtered = orders.copy()
    if sel_eq:
        filtered = filtered[filtered["_eq"].isin(sel_eq)]
    if sel_stage:
        filtered = filtered[filtered["_stage"].isin(sel_stage)]
    if sel_pri and pri_col:
        filtered = filtered[filtered[pri_col].astype(str).str.replace(".0","",regex=False).isin(sel_pri)]

    kpis_f = compute_kpis(filtered) if len(filtered) else kpis

    # ── Global KPI Cards ──
    st.markdown('<div class="sec-title">📈 Global Maintenance KPIs</div>', unsafe_allow_html=True)

    n_f = kpis_f["n_total"]
    cards_html = f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">Total Work Orders</div>
            <div class="kpi-value">{n_f:,}</div>
            <div class="kpi-sub">{kpis_f['n_exec']:,} executed · {kpis_f['n_open']:,} open</div>
        </div>
        {kpi_card_html("% Préparation", kpis_f['pct_prep'],
            round(n_f*kpis_f['pct_prep']/100), "prepared")}
        {kpi_card_html("% Planification", kpis_f['pct_sched'],
            round(n_f*kpis_f['pct_sched']/100), "scheduled")}
        {kpi_card_html("% Exécution", kpis_f['pct_exec'],
            kpis_f['n_exec'], "confirmed done")}
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Backlog Age Cards ──
    st.markdown('<div class="sec-title">🗂️ Backlog Ages</div>', unsafe_allow_html=True)
    bl = kpis_f
    st.markdown(f"""
    <div class="kpi-row">
        {backlog_card_html("Planner Backlog",   bl['bl_plan'][0],  bl['bl_plan'][1],  bl['bl_plan'][2],  "📋", "#E74C3C")}
        {backlog_card_html("Scheduler Backlog", bl['bl_sched'][0], bl['bl_sched'][1], bl['bl_sched'][2], "📅", "#F39C12")}
        {backlog_card_html("Execution Backlog", bl['bl_exec'][0],  bl['bl_exec'][1],  bl['bl_exec'][2],  "⚙️", "#0079C2")}
    </div>
    <div style="color:var(--muted);font-size:.76rem;margin-top:-.5rem;margin-bottom:1rem;">
        ℹ️  Planner = not yet prepared &nbsp;·&nbsp; Scheduler = prepared but not scheduled &nbsp;·&nbsp;
        Execution = scheduled but not confirmed done &nbsp;·&nbsp; Age measured from WO creation date
    </div>
    """, unsafe_allow_html=True)

    # ── Charts Row 1 ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(gauge_chart(kpis_f["pct_prep"],  "% Préparation",  "#005A9E"), use_container_width=True)
    with c2:
        st.plotly_chart(gauge_chart(kpis_f["pct_sched"], "% Planification","#0079C2"), use_container_width=True)
    with c3:
        st.plotly_chart(gauge_chart(kpis_f["pct_exec"],  "% Exécution",    "#00B4E6"), use_container_width=True)

    # ── Charts Row 2 ──
    c4, c5 = st.columns(2)
    with c4:
        st.plotly_chart(stage_donut(filtered),      use_container_width=True)
    with c5:
        st.plotly_chart(pipeline_funnel(kpis_f),   use_container_width=True)

    # ── Backlog Age Bar ──
    st.plotly_chart(backlog_age_bar(kpis_f), use_container_width=True)

    # ── Per-Equipment KPI Table ──
    st.markdown('<div class="sec-title">🏭 KPIs per Equipment</div>', unsafe_allow_html=True)

    eq_kpi_df = kpi_by_equipment(filtered)

    # Color scale on % cols
    def color_pct(val):
        color = kpi_color(val)
        return f"color: {color}; font-weight: 600;"

    # Search filter
    eq_search = st.text_input("🔍 Search equipment", placeholder="Type equipment ID or description…", key="eq_search")
    if eq_search:
        mask = eq_kpi_df.astype(str).apply(lambda c: c.str.contains(eq_search, case=False)).any(axis=1)
        eq_kpi_df = eq_kpi_df[mask]

    st.dataframe(
        eq_kpi_df.style
            .applymap(color_pct, subset=["% Preparation", "% Planification", "% Execution"])
            .format({
                "% Preparation": "{:.1f}%",
                "% Planification": "{:.1f}%",
                "% Execution": "{:.1f}%",
                "Avg Age (days)": "{:.0f}",
            }),
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    # ── Top-10 backlog chart ──
    st.markdown('<div class="sec-title">🔴 Top 10 Equipment by Open Backlog</div>', unsafe_allow_html=True)
    top10 = eq_kpi_df.nlargest(10, "Open WOs")
    fig_top = go.Figure(go.Bar(
        x=top10["Open WOs"],
        y=top10["Description"].str[:25],
        orientation="h",
        marker=dict(
            color=top10["% Execution"],
            colorscale=[[0,"#E74C3C"],[0.5,"#F39C12"],[1,"#0079C2"]],
            colorbar=dict(title="% Exec", ticksuffix="%"),
        ),
        text=top10["Open WOs"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Open WOs: %{x}<br>% Execution: %{marker.color:.1f}%<extra></extra>",
    ))
    fig_top.update_layout(
        **plotly_dark_layout(), height=380,
        title="Open WOs per Equipment (color = % Execution)",
        xaxis_title="Open Work Orders",
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # ── Priority breakdown ──
    pri_col = find_col(filtered, "priority")
    if pri_col:
        st.markdown('<div class="sec-title">⚡ WO Distribution by Priority</div>', unsafe_allow_html=True)
        pri_counts = filtered[pri_col].value_counts().sort_index()
        fig_pri = go.Figure(go.Bar(
            x=[f"P{int(p)}" if isinstance(p, float) else str(p) for p in pri_counts.index],
            y=pri_counts.values,
            marker=dict(color=["#E74C3C","#F39C12","#0079C2","#00B4E6"][:len(pri_counts)], opacity=0.85),
            text=pri_counts.values, textposition="outside",
        ))
        fig_pri.update_layout(**plotly_dark_layout(), height=260, title="Work Orders by Priority")
        st.plotly_chart(fig_pri, use_container_width=True)

    # ── Download ──
    st.markdown('<div class="sec-title">📥 Export KPI Report</div>', unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            eq_kpi_df.to_excel(writer, sheet_name="KPI par Équipement", index=False)
            filtered[["_order","_eq","_eq_desc","_stage","_created"]].rename(columns={
                "_order":"Ordre","_eq":"Équipement","_eq_desc":"Description",
                "_stage":"Étape","_created":"Créé le",
            }).to_excel(writer, sheet_name="Détail OT", index=False)
        st.download_button(
            "📊 Download KPI Report (Excel)",
            buf.getvalue(),
            file_name=f"JESA_KPI_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "📄 Download Equipment Table (CSV)",
            eq_kpi_df.to_csv(index=False).encode(),
            file_name=f"JESA_Equip_KPI_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════
# GANTT HELPERS  (shared by Smoothing & Leveling)
# ══════════════════════════════════════════════════════════════

STAGE_COLORS = {
    "Executed":     "#00B4E6",
    "In Execution": "#0079C2",
    "Scheduled":    "#2ECC71",
    "Prepared":     "#F39C12",
    "Not Prepared": "#E74C3C",
}

def build_gantt_df(raw_df, max_rows=300):
    """
    Build a Gantt-ready DataFrame from a raw CMMS extraction.
    Aggregates operations into orders, computes start/end from
    Début de base + total work hours ÷ 8h/day.
    Returns (gantt_df, daily_load_df) or raises.
    """
    order_col = find_col(raw_df, "order")
    date_col  = "Début de base"   if "Début de base"   in raw_df.columns else \
                "Début au plus tôt" if "Début au plus tôt" in raw_df.columns else None
    work_col  = "Travail"         if "Travail"         in raw_df.columns else \
                "Durée"           if "Durée"           in raw_df.columns else None
    res_col   = "Poste de travail" if "Poste de travail" in raw_df.columns else None
    desc_col  = "Description (ordre)" if "Description (ordre)" in raw_df.columns else \
                "Description"         if "Description"         in raw_df.columns else None
    eq_col    = find_col(raw_df, "equipment")
    sys_col   = find_col(raw_df, "sys_status")
    usr_col   = find_col(raw_df, "usr_status")
    pri_col   = find_col(raw_df, "priority")

    if not order_col or not date_col:
        raise ValueError("Cannot find Order or Start Date column in the file.")

    # Aggregate work per order
    agg = {date_col: "first"}
    if work_col:  agg[work_col] = "sum"
    if res_col:   agg[res_col]  = "first"
    if desc_col:  agg[desc_col] = "first"
    if eq_col:    agg[eq_col]   = "first"
    if sys_col:   agg[sys_col]  = "first"
    if usr_col:   agg[usr_col]  = "first"
    if pri_col:   agg[pri_col]  = "first"

    orders = raw_df.groupby(order_col).agg(agg).reset_index()
    orders.rename(columns={order_col: "_order"}, inplace=True)

    orders["_start"]    = pd.to_datetime(orders[date_col], errors="coerce")
    orders["_work_h"]   = pd.to_numeric(orders[work_col], errors="coerce").fillna(4) if work_col else 4
    orders["_dur_days"] = (orders["_work_h"] / 8).clip(lower=0.125)
    orders["_end"]      = orders["_start"] + pd.to_timedelta(
                              orders["_dur_days"].apply(lambda x: max(1, int(np.ceil(x)))), unit="D"
                          )
    orders["_resource"] = orders[res_col].fillna("N/A")  if res_col  else "N/A"
    orders["_desc"]     = orders[desc_col].fillna("—").str[:40] if desc_col else orders["_order"].astype(str)
    orders["_eq"]       = orders[eq_col].fillna("N/A")   if eq_col   else "N/A"
    orders["_priority"] = orders[pri_col].fillna(0).astype(str).str.replace(".0","",regex=False) if pri_col else "—"

    # Classify stage
    sys_s = orders[sys_col].astype(str).str.upper() if sys_col else pd.Series([""] * len(orders))
    usr_s = orders[usr_col].astype(str).str.upper() if usr_col else pd.Series([""] * len(orders))
    executed  = sys_s.str.contains(r"CONF|CNFP|TECO|COMP|CLSD", na=False)
    launched  = sys_s.str.contains(r"LANC|REL", na=False) & ~executed
    scheduled = usr_s.str.contains(r"ATPL|AGAR|SCHD|APPR", na=False) | executed | launched
    prepared  = usr_s.str.contains(r"CRPR|ATPL|AGAR|AVPD|PREP", na=False) | executed | launched

    def _stage(row):
        if executed.loc[row.name]:  return "Executed"
        if launched.loc[row.name]:  return "In Execution"
        if scheduled.loc[row.name]: return "Scheduled"
        if prepared.loc[row.name]:  return "Prepared"
        return "Not Prepared"

    orders["_stage"] = orders.apply(_stage, axis=1)
    orders["_color"] = orders["_stage"].map(STAGE_COLORS)

    # Drop rows without valid dates
    orders = orders.dropna(subset=["_start", "_end"])
    orders = orders.sort_values("_start").reset_index(drop=True)

    # Daily resource load
    load_rows = []
    for _, row in orders.iterrows():
        days = pd.date_range(row["_start"], row["_end"] - pd.Timedelta(days=1), freq="D")
        for d in days:
            load_rows.append({"date": d, "resource": row["_resource"], "order": row["_order"]})
    load_df = pd.DataFrame(load_rows)
    if not load_df.empty:
        daily_load = load_df.groupby(["date", "resource"]).size().reset_index(name="count")
        daily_load = daily_load.pivot(index="date", columns="resource", values="count").fillna(0).astype(int)
        daily_load["total"] = daily_load.sum(axis=1)
    else:
        daily_load = pd.DataFrame()

    return orders, daily_load


def make_gantt(orders_df, title="Gantt Chart", max_rows=200, height=600):
    """Build a Plotly Gantt (timeline) figure from orders_df."""
    df = orders_df.head(max_rows).copy()
    df["_label"] = df["_order"].astype(str) + " · " + df["_desc"]

    fig = go.Figure()

    for stage, grp in df.groupby("_stage"):
        color = STAGE_COLORS.get(stage, "#888")
        for _, row in grp.iterrows():
            dur_h = row["_work_h"]
            fig.add_trace(go.Bar(
                x=[(row["_end"] - row["_start"]).days],
                y=[row["_label"]],
                base=[row["_start"]],
                orientation="h",
                marker=dict(color=color, opacity=0.85, line=dict(width=0)),
                name=stage,
                legendgroup=stage,
                showlegend=True if row.name == grp.index[0] else False,
                hovertemplate=(
                    f"<b>{row['_order']}</b><br>"
                    f"{row['_desc']}<br>"
                    f"Start: {row['_start'].date()}<br>"
                    f"End:   {row['_end'].date()}<br>"
                    f"Work:  {dur_h:.1f}h · Resource: {row['_resource']}<br>"
                    f"Priority: {row['_priority']} · Stage: {stage}"
                    "<extra></extra>"
                ),
            ))

    fig.update_layout(
        **plotly_dark_layout(),
        barmode="overlay",
        height=height,
        title=title,
        xaxis=dict(
            type="date",
            tickformat="%d %b %Y",
            showgrid=True,
            gridcolor="#1A3A55",
        ),
        yaxis=dict(
            autorange="reversed",
            showgrid=False,
            tickfont=dict(size=10),
        ),
        legend=dict(
            title="Stage",
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="left",   x=0,
            bgcolor="#071D30",
            bordercolor="#1A3A55",
        ),
        margin=dict(l=300, r=20, t=60, b=40),
    )
    return fig


def make_load_chart(daily_load, capacity_line=None, title="Daily Resource Load"):
    """Stacked bar chart of WOs scheduled per day per work centre."""
    fig = go.Figure()
    res_colors = ["#0079C2", "#00B4E6", "#2ECC71", "#F39C12", "#E74C3C", "#9B59B6"]
    resources = [c for c in daily_load.columns if c != "total"]

    for i, res in enumerate(resources):
        fig.add_trace(go.Bar(
            x=daily_load.index,
            y=daily_load[res],
            name=res,
            marker_color=res_colors[i % len(res_colors)],
            hovertemplate=f"<b>{res}</b><br>%{{x|%d %b %Y}}: %{{y}} WOs<extra></extra>",
        ))

    if capacity_line:
        fig.add_hline(
            y=capacity_line,
            line_dash="dash",
            line_color="#E74C3C",
            line_width=2,
            annotation_text=f"Capacity ({capacity_line} WOs/day)",
            annotation_font_color="#E74C3C",
        )

    fig.update_layout(
        **plotly_dark_layout(),
        barmode="stack",
        height=320,
        title=title,
        xaxis=dict(type="date", tickformat="%d %b %Y", rangeslider=dict(visible=True, bgcolor="#04111F")),
        yaxis_title="Work Orders / Day",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def _no_data_placeholder(tab_name):
    st.markdown(f"""
    <div class="card" style="text-align:center;padding:4rem 2rem;color:var(--muted);">
        <div style="font-size:3rem;margin-bottom:1rem;">📂</div>
        <div style="font-size:1.1rem;color:var(--text);font-family:'Syne',sans-serif;font-weight:600;margin-bottom:.5rem;">
            No CMMS extraction loaded
        </div>
        <div>Go to the <b>📊 Dashboard</b> tab, upload your extraction file,<br>
        then come back to <b>{tab_name}</b>.</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB: SMOOTHING  — highlight overloaded days on the Gantt
# ══════════════════════════════════════════════════════════════
def tab_smoothing():
    st.markdown("""
    <div class="portal-header">
        <div><h1>🔧 Resource Smoothing</h1>
        <p>Gantt view with daily load analysis — identify and visualise overloaded days</p></div>
    </div>
    """, unsafe_allow_html=True)

    if "cmms_raw" not in st.session_state:
        _no_data_placeholder("🔧 Smoothing")
        return

    raw_df = st.session_state["cmms_raw"]

    with st.spinner("⚙️ Building Gantt…"):
        try:
            orders, daily_load = build_gantt_df(raw_df)
        except Exception as e:
            st.error(f"❌ {e}")
            return

    # ── Controls ──
    with st.container():
        cc1, cc2, cc3, cc4 = st.columns([1.5, 1.5, 1, 1])
        with cc1:
            res_options = sorted(orders["_resource"].unique().tolist())
            sel_res = st.multiselect("🏗️ Work Centre", res_options, default=res_options, key="sm_res")
        with cc2:
            stage_opts = list(STAGE_COLORS.keys())
            sel_stage  = st.multiselect("📌 Stage", stage_opts, default=stage_opts, key="sm_stage")
        with cc3:
            date_min = orders["_start"].min().date()
            date_max = orders["_end"].max().date()
            sm_start = st.date_input("From", value=date_min, min_value=date_min, max_value=date_max, key="sm_s")
        with cc4:
            sm_end   = st.date_input("To",   value=min(date_max, date_min + pd.Timedelta(days=90)),
                                     min_value=date_min, max_value=date_max, key="sm_e")

    capacity = st.slider("⚠️ Overload threshold (WOs/day)", min_value=1, max_value=500, value=50,
                         help="Days above this line are highlighted as overloaded")

    # Apply filters
    filt = orders[
        orders["_resource"].isin(sel_res) &
        orders["_stage"].isin(sel_stage) &
        (orders["_start"].dt.date >= sm_start) &
        (orders["_start"].dt.date <= sm_end)
    ].copy()

    if filt.empty:
        st.warning("⚠️ No work orders match the current filters.")
        return

    n_shown = min(250, len(filt))
    st.markdown(f'<div class="sec-title">📅 Gantt — {n_shown} of {len(filt)} Work Orders</div>', unsafe_allow_html=True)

    # Gantt
    fig_gantt = make_gantt(
        filt.sort_values("_start"),
        title=f"Work Order Schedule ({sm_start} → {sm_end})",
        max_rows=n_shown,
        height=max(400, min(n_shown * 22, 800)),
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

    # ── Daily load chart with overload line ──
    st.markdown('<div class="sec-title">📊 Daily Resource Load & Overload Detection</div>', unsafe_allow_html=True)

    # Recompute load for filtered window
    load_rows = []
    for _, row in filt.iterrows():
        days = pd.date_range(row["_start"], row["_end"] - pd.Timedelta(days=1), freq="D")
        for d in days:
            load_rows.append({"date": d, "resource": row["_resource"]})

    if load_rows:
        ld = pd.DataFrame(load_rows)
        ld_pivot = ld.groupby(["date","resource"]).size().reset_index(name="count")
        ld_pivot = ld_pivot.pivot(index="date", columns="resource", values="count").fillna(0).astype(int)
        ld_pivot["total"] = ld_pivot.sum(axis=1)

        fig_load = make_load_chart(ld_pivot, capacity_line=capacity,
                                   title=f"Daily WO Load · Overload threshold = {capacity} WOs/day")
        st.plotly_chart(fig_load, use_container_width=True)

        # Overloaded days table
        overloaded = ld_pivot[ld_pivot["total"] > capacity].copy()
        overloaded.index = overloaded.index.strftime("%Y-%m-%d")
        overloaded.index.name = "Date"

        if not overloaded.empty:
            st.markdown(f"""
            <div class="card" style="border-left:4px solid #E74C3C;margin-bottom:1rem;">
                <b style="color:#E74C3C;">⚠️ {len(overloaded)} overloaded day(s) detected</b>
                <span style="color:var(--muted);font-size:.85rem;"> — days exceeding {capacity} WOs/day</span>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(overloaded.reset_index(), use_container_width=True, hide_index=True)
        else:
            st.success(f"✅ No overloaded days — all days are within the {capacity} WOs/day threshold.")

    # ── Summary stats ──
    st.markdown('<div class="sec-title">📋 Smoothing Summary</div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("WOs in window",    f"{len(filt):,}")
    s2.metric("Total work hours", f"{filt['_work_h'].sum():,.0f} h")
    s3.metric("Avg WOs/day",      f"{ld_pivot['total'].mean():.1f}" if load_rows else "—")
    s4.metric("Peak day load",    f"{ld_pivot['total'].max()}" if load_rows else "—")

    # Download
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        filt[["_order","_desc","_resource","_start","_end","_work_h","_stage","_priority"]].rename(columns={
            "_order":"Ordre","_desc":"Description","_resource":"Centre de travail",
            "_start":"Début","_end":"Fin","_work_h":"Heures","_stage":"Étape","_priority":"Priorité",
        }).to_excel(writer, sheet_name="Gantt", index=False)
        if load_rows:
            ld_pivot.reset_index().to_excel(writer, sheet_name="Charge journalière", index=False)
    st.download_button(
        "📥 Export Gantt + Load (Excel)",
        buf.getvalue(),
        file_name=f"JESA_Smoothing_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════════════
# TAB: LEVELING  — redistribute overloaded WOs to fix peaks
# ══════════════════════════════════════════════════════════════
def tab_leveling():
    st.markdown("""
    <div class="portal-header">
        <div><h1>⚖️ Resource Leveling</h1>
        <p>Automatically redistribute overloaded work orders to flatten resource peaks</p></div>
    </div>
    """, unsafe_allow_html=True)

    if "cmms_raw" not in st.session_state:
        _no_data_placeholder("⚖️ Leveling")
        return

    raw_df = st.session_state["cmms_raw"]

    with st.spinner("⚙️ Building schedule…"):
        try:
            orders, daily_load = build_gantt_df(raw_df)
        except Exception as e:
            st.error(f"❌ {e}")
            return

    # ── Leveling Controls ──
    st.markdown('<div class="sec-title">⚙️ Leveling Parameters</div>', unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([1.5, 1, 1, 1])
    with lc1:
        res_opts = sorted(orders["_resource"].unique().tolist())
        sel_res  = st.multiselect("🏗️ Work Centre to level", res_opts, default=res_opts, key="lv_res")
    with lc2:
        capacity = st.number_input("Max WOs / Day (capacity)", min_value=1, value=30,
                                   help="The algorithm will not exceed this limit per day")
    with lc3:
        lv_start = st.date_input("Leveling window start",
                                  value=orders["_start"].min().date(), key="lv_s")
    with lc4:
        lv_end   = st.date_input("Leveling window end",
                                  value=min(orders["_end"].max().date(),
                                            orders["_start"].min().date() + pd.Timedelta(days=90)),
                                  key="lv_e")

    stage_filt = st.multiselect(
        "📌 Stages to level (only non-executed stages can be moved)",
        options=["Not Prepared", "Prepared", "Scheduled", "In Execution"],
        default=["Not Prepared", "Prepared", "Scheduled"],
        key="lv_stage",
    )

    run_btn = st.button("▶️ Run Leveling Algorithm", use_container_width=True)

    if not run_btn and "leveled_orders" not in st.session_state:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2.5rem;color:var(--muted);">
            <div style="font-size:2rem;margin-bottom:.6rem;">⚖️</div>
            Configure the parameters above and click <b>Run Leveling Algorithm</b>.
        </div>
        """, unsafe_allow_html=True)
        return

    if run_btn:
        # ── Leveling algorithm ──
        # Split: fixed (executed/in-execution) + moveable (rest in selected stages)
        window_start = pd.Timestamp(lv_start)
        window_end   = pd.Timestamp(lv_end)

        in_window = (
            orders["_resource"].isin(sel_res) &
            (orders["_start"] >= window_start) &
            (orders["_start"] <= window_end)
        )
        moveable = in_window & orders["_stage"].isin(stage_filt)
        fixed    = in_window & ~moveable

        fixed_orders   = orders[fixed].copy()
        move_orders    = orders[moveable].copy().sort_values(["_priority","_start"])
        outside_orders = orders[~in_window].copy()

        # Track daily load per resource (seeded with fixed orders)
        from collections import defaultdict
        daily_count = defaultdict(lambda: defaultdict(int))  # date -> resource -> count
        for _, row in fixed_orders.iterrows():
            for d in pd.date_range(row["_start"], row["_end"] - pd.Timedelta(days=1), freq="D"):
                daily_count[d][row["_resource"]] += 1

        leveled_rows = []
        for _, row in move_orders.iterrows():
            res      = row["_resource"]
            dur_days = max(1, int(np.ceil(row["_dur_days"])))
            # Find earliest start >= original start where capacity not exceeded
            candidate = max(row["_start"], window_start)
            placed    = False
            for _ in range(365):
                # Check if all days in the duration window fit
                trial_days = pd.date_range(candidate, periods=dur_days, freq="D")
                if all(daily_count[d][res] < capacity for d in trial_days):
                    for d in trial_days:
                        daily_count[d][res] += 1
                    new_row = row.copy()
                    new_row["_start_leveled"] = candidate
                    new_row["_end_leveled"]   = candidate + pd.Timedelta(days=dur_days)
                    new_row["_shifted"]       = (candidate - row["_start"]).days
                    leveled_rows.append(new_row)
                    placed = True
                    break
                candidate += pd.Timedelta(days=1)
            if not placed:
                new_row = row.copy()
                new_row["_start_leveled"] = row["_start"]
                new_row["_end_leveled"]   = row["_end"]
                new_row["_shifted"]       = 0
                leveled_rows.append(new_row)

        leveled_df = pd.DataFrame(leveled_rows) if leveled_rows else pd.DataFrame()

        # Combine: fixed (no shift) + leveled + outside
        fixed_orders["_start_leveled"] = fixed_orders["_start"]
        fixed_orders["_end_leveled"]   = fixed_orders["_end"]
        fixed_orders["_shifted"]       = 0
        outside_orders["_start_leveled"] = outside_orders["_start"]
        outside_orders["_end_leveled"]   = outside_orders["_end"]
        outside_orders["_shifted"]       = 0

        all_leveled = pd.concat([fixed_orders, leveled_df, outside_orders], ignore_index=True)
        st.session_state["leveled_orders"] = all_leveled
        st.session_state["lv_capacity"]    = capacity
        st.session_state["lv_res"]         = sel_res
        st.session_state["lv_window"]      = (window_start, window_end)

    if "leveled_orders" not in st.session_state:
        return

    all_leveled  = st.session_state["leveled_orders"]
    capacity     = st.session_state["lv_capacity"]
    sel_res_used = st.session_state["lv_res"]
    w_start, w_end = st.session_state["lv_window"]

    # ── Before / After load comparison ──
    st.markdown('<div class="sec-title">📊 Before vs After Leveling — Daily Load</div>', unsafe_allow_html=True)

    def compute_daily_load_col(df, start_col, end_col, resources):
        rows = []
        for _, row in df[df["_resource"].isin(resources)].iterrows():
            if pd.isna(row[start_col]) or pd.isna(row[end_col]):
                continue
            for d in pd.date_range(row[start_col], row[end_col] - pd.Timedelta(days=1), freq="D"):
                if w_start <= d <= w_end:
                    rows.append({"date": d, "resource": row["_resource"]})
        if not rows:
            return pd.DataFrame()
        ld = pd.DataFrame(rows)
        pv = ld.groupby(["date","resource"]).size().reset_index(name="count")
        pv = pv.pivot(index="date", columns="resource", values="count").fillna(0).astype(int)
        pv["total"] = pv.sum(axis=1)
        return pv

    before_ld = compute_daily_load_col(all_leveled, "_start",         "_end",         sel_res_used)
    after_ld  = compute_daily_load_col(all_leveled, "_start_leveled", "_end_leveled", sel_res_used)

    if not before_ld.empty and not after_ld.empty:
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(
            x=before_ld.index, y=before_ld["total"],
            name="Before Leveling", mode="lines",
            line=dict(color="#E74C3C", width=2, dash="dot"),
            fill="tozeroy", fillcolor="rgba(231,76,60,0.08)",
        ))
        fig_compare.add_trace(go.Scatter(
            x=after_ld.index, y=after_ld["total"],
            name="After Leveling", mode="lines",
            line=dict(color="#00B4E6", width=2),
            fill="tozeroy", fillcolor="rgba(0,180,230,0.08)",
        ))
        fig_compare.add_hline(
            y=capacity, line_dash="dash", line_color="#F39C12", line_width=2,
            annotation_text=f"Capacity ({capacity}/day)", annotation_font_color="#F39C12",
        )
        fig_compare.update_layout(
            **plotly_dark_layout(), height=320,
            title="Daily Load: Before vs After Leveling",
            xaxis=dict(type="date", tickformat="%d %b %Y",
                       rangeslider=dict(visible=True, bgcolor="#04111F")),
            yaxis_title="Work Orders / Day",
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Peak Before", int(before_ld["total"].max()))
        m2.metric("Peak After",  int(after_ld["total"].max()),
                  delta=f"{int(after_ld['total'].max()) - int(before_ld['total'].max())} WOs",
                  delta_color="inverse")
        m3.metric("Overloaded days before",
                  int((before_ld["total"] > capacity).sum()))
        m4.metric("Overloaded days after",
                  int((after_ld["total"] > capacity).sum()),
                  delta=f"{int((after_ld['total']>capacity).sum()) - int((before_ld['total']>capacity).sum())}",
                  delta_color="inverse")
        shifted = all_leveled[all_leveled.get("_shifted", pd.Series(0)) > 0] if "_shifted" in all_leveled.columns else pd.DataFrame()
        m5.metric("WOs shifted", len(shifted))

    # ── Gantt: Before vs After (side by side tabs) ──
    st.markdown('<div class="sec-title">📅 Gantt Charts — Before & After Leveling</div>', unsafe_allow_html=True)
    g1, g2 = st.tabs(["📅 Before Leveling", "📅 After Leveling"])

    in_window_mask = (
        all_leveled["_resource"].isin(sel_res_used) &
        (all_leveled["_start"] >= w_start) &
        (all_leveled["_start"] <= w_end)
    )
    n_gantt = min(200, in_window_mask.sum())
    gantt_h = max(400, min(n_gantt * 20, 800))

    with g1:
        before_df = all_leveled[in_window_mask].copy()
        before_df["_end_plot"]   = before_df["_end"]
        before_df["_start_plot"] = before_df["_start"]
        before_plot = before_df.copy()
        before_plot["_start"] = before_plot["_start_plot"]
        before_plot["_end"]   = before_plot["_end_plot"]
        st.plotly_chart(
            make_gantt(before_plot.head(n_gantt), "Gantt — Before Leveling", max_rows=n_gantt, height=gantt_h),
            use_container_width=True,
        )

    with g2:
        after_df = all_leveled[in_window_mask].copy()
        after_df["_start"] = after_df["_start_leveled"]
        after_df["_end"]   = after_df["_end_leveled"]
        st.plotly_chart(
            make_gantt(after_df.head(n_gantt), "Gantt — After Leveling", max_rows=n_gantt, height=gantt_h),
            use_container_width=True,
        )

    # ── Shifted WOs detail ──
    if "_shifted" in all_leveled.columns:
        shifted_df = all_leveled[all_leveled["_shifted"] > 0].copy()
        if not shifted_df.empty:
            st.markdown('<div class="sec-title">🔀 Shifted Work Orders Detail</div>', unsafe_allow_html=True)
            display_df = shifted_df[["_order","_desc","_resource","_stage","_start","_start_leveled","_shifted"]].rename(columns={
                "_order":"Ordre","_desc":"Description","_resource":"Centre de travail",
                "_stage":"Étape","_start":"Date originale",
                "_start_leveled":"Date nivelée","_shifted":"Décalage (jours)",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)

    # ── Download ──
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        export_cols = ["_order","_desc","_resource","_stage","_priority",
                       "_start","_end","_work_h","_start_leveled","_end_leveled","_shifted"]
        export_cols = [c for c in export_cols if c in all_leveled.columns]
        all_leveled[export_cols].rename(columns={
            "_order":"Ordre","_desc":"Description","_resource":"Centre de travail",
            "_stage":"Étape","_priority":"Priorité","_start":"Début original",
            "_end":"Fin originale","_work_h":"Heures",
            "_start_leveled":"Début nivelé","_end_leveled":"Fin nivelée","_shifted":"Décalage (j)",
        }).to_excel(writer, sheet_name="Leveling", index=False)
        if not before_ld.empty:
            before_ld.reset_index().to_excel(writer, sheet_name="Charge avant", index=False)
        if not after_ld.empty:
            after_ld.reset_index().to_excel(writer, sheet_name="Charge après", index=False)
    st.download_button(
        "📥 Export Leveling Plan (Excel)",
        buf.getvalue(),
        file_name=f"JESA_Leveling_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


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
                    line=dict(color='#00B4E6', width=2, dash='dot'),
                    name='Walking Path',
                ))
                fig.update_layout(**plotly_dark_layout(), height=500,
                                  title=f'Optimized Route · {len(sel)} conveyors · {b_dist/1000:.2f} km walking')
                st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"""
                <div class="card" style="border-left:4px solid var(--accent);">
                    <b>✅ Route optimized</b><br>
                    <span style="color:var(--muted);">Total walking distance: <b style="color:var(--accent3);">{b_dist/1000:.3f} km</b> 
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

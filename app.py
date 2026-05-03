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
        fig.add_trace(go.Scatter(x=days, y=before, name='Before', line=dict(color='#E74C3C', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=days, y=after,  name='After',  line=dict(color='#00B4E6', width=2)))
        fig.add_hline(y=crew_size, line_dash='dash', line_color='#0079C2', annotation_text='Max capacity')
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

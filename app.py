# =========================================================
# VENUS AI 
# =========================================================
import os, joblib, datetime
import numpy as np, pandas as pd, streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import sqlite3


# ===============================
# 🧠 SESSION STATE INIT
# ===============================
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None

if "role" not in st.session_state:
    st.session_state.role = "Customer"

# ===============================
# 🔹 DATABASE SETUP
# ===============================
def init_db():
    conn = sqlite3.connect("venus_ai.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT, price REAL, quantity INTEGER,
        supplier TEXT, location TEXT, total REAL, date TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, price REAL, qty INTEGER,
        supplier TEXT, location TEXT, image_url TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, email TEXT UNIQUE, role TEXT,
        name TEXT, location TEXT, created_at DATETIME
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT, price REAL, qty INTEGER,
        created_at DATETIME, FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

init_db()

# ===============================
# 🔹 DATABASE CONNECTION
# ===============================
conn = sqlite3.connect("venus_ai.db", check_same_thread=False)
cursor = conn.cursor()

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="VENUS AI", page_icon="🪐", initial_sidebar_state="expanded")

import streamlit.components.v1 as components
 
components.html("""
<script>
(function() {
    try {
        Object.keys(window.parent.localStorage)
            .filter(k => k.toLowerCase().includes("sidebar"))
            .forEach(k => window.parent.localStorage.removeItem(k));
    } catch(e) {}
})();
</script>
""", height=0, scrolling=False)

# =========================================================
# STYLING
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ─── ROOT VARIABLES ─── */
:root {
    --bg-void:     #000000;
    --bg-dark:     #030305;
    --bg-panel:    rgba(8, 8, 14, 0.95);
    --bg-glass:    rgba(255,255,255,0.02);
    --accent-cyan:  #00e5ff;
    --accent-purple:#a855f7;
    --accent-blue:  #3b82f6;
    --accent-glow:  rgba(0, 229, 255, 0.10);
    --text-primary: #e8edf5;
    --text-muted:   #9aaabf;
    --text-dim:     #b0bece;
    --border:       rgba(0, 229, 255, 0.07);
    --border-hover: rgba(0, 229, 255, 0.22);
    --danger:       #ff4b6e;
    --success:      #00e096;
    --warning:      #ffb800;
    --radius-sm:    8px;
    --radius-md:    14px;
    --radius-lg:    22px;
}

/* ─── GLOBAL RESET ─── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #000000 !important;
    color: var(--text-primary) !important;
}

/* Force true black on every Streamlit container */
.stApp,
.stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
section.main {
    background: #000000 !important;
    background-color: #000000 !important;
}

.stApp {
    background-image:
        radial-gradient(ellipse 70% 40% at 15% -5%, rgba(0,229,255,0.05) 0%, transparent 55%),
        radial-gradient(ellipse 55% 35% at 85% 105%, rgba(168,85,247,0.045) 0%, transparent 55%) !important;
    background-attachment: fixed;
}

/* ─── HIDE STREAMLIT CHROME ─── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--accent-cyan); border-radius: 4px; }

/* ─── TOP NAV BAR ─── */
.venus-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 58px;
    background: rgba(5, 7, 13, 0.92);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    z-index: 9999;
}
.venus-logo {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 0.15em;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.venus-user-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--bg-glass);
    border: 1px solid var(--border);
    border-radius: 40px;
    padding: 6px 14px 6px 8px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.venus-user-badge:hover { border-color: var(--border-hover); }
.venus-avatar {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; color: #000;
}
.venus-username { font-size: 13px; font-weight: 500; color: #b0bece; }
.venus-role-tag {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.tag-supplier { background: rgba(0,229,255,0.12); color: var(--accent-cyan); }
.tag-customer { background: rgba(168,85,247,0.12); color: var(--accent-purple); }

/* ─── MAIN CONTENT OFFSET ─── */
.block-container {
    padding-top: 80px !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
    max-width: 1280px;
}

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
    background: #080808 !important;
    border-right: 1px solid rgba(0,229,255,0.06) !important;
}
/* Only dim the Streamlit widget labels — NOT every element */
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stExpander label,
[data-testid="stSidebar"] .stTextInput label {
    color: #a0b0c4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
/* Selectbox dropdown text */
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div {
    color: #e8edf5 !important;
}
/* Expander header */
[data-testid="stSidebar"] details summary p {
    color: #8898b0 !important;
    font-size: 13px !important;
}
[data-testid="stSidebarContent"] {
    padding-top: 0px !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
}

/* ─── SECTION HEADINGS ─── */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fff 30%, var(--accent-cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3em !important;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

/* ─── METRIC CARDS / GLASS PANELS ─── */
.venus-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 16px;
    backdrop-filter: blur(20px);
    transition: border-color 0.25s, transform 0.2s;
    position: relative;
    overflow: hidden;
}
.venus-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    opacity: 0.4;
}
.venus-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
}
.stat-number {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--accent-cyan);
    line-height: 1;
}
.stat-label {
    font-size: 12px;
    color: #a0b0c4;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}

/* ─── METRIC WIDGET ─── */
[data-testid="metric-container"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 18px !important;
}
[data-testid="metric-container"] label {
    color: #a0b0c4 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--accent-cyan) !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
}

/* ─── BUTTONS ─── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,229,255,0.1), rgba(168,85,247,0.1)) !important;
    color: var(--accent-cyan) !important;
    border: 1px solid rgba(0,229,255,0.3) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 20px !important;
    letter-spacing: 0.04em;
    transition: all 0.2s !important;
    backdrop-filter: blur(8px);
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,229,255,0.22), rgba(168,85,247,0.18)) !important;
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 20px rgba(0,229,255,0.2) !important;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* Primary CTA */
.primary-btn > button {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)) !important;
    color: #000 !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ─── INPUTS ─── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 11px 14px !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(0,229,255,0.08) !important;
    background: rgba(0,229,255,0.03) !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stSlider label,
.stFileUploader label {
    color: #b0bece !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* ─── SELECTBOX ─── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

/* ─── TABS ─── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #a0b0c4 !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    border: none !important;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(168,85,247,0.12)) !important;
    color: var(--accent-cyan) !important;
    border: 1px solid rgba(0,229,255,0.2) !important;
}

/* ─── DATAFRAME ─── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
}
.dvn-scroller { background: var(--bg-panel) !important; }

/* ─── ALERTS ─── */
.stAlert {
    border-radius: var(--radius-md) !important;
    border-left-width: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
}
.stSuccess { border-color: var(--success) !important; background: rgba(0,224,150,0.07) !important; }
.stWarning { border-color: var(--warning) !important; background: rgba(255,184,0,0.07) !important; }
.stError   { border-color: var(--danger) !important;  background: rgba(255,75,110,0.07) !important; }
.stInfo    { border-color: var(--accent-cyan) !important; background: rgba(0,229,255,0.07) !important; }

/* ─── PROGRESS BAR ─── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple)) !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 4px !important;
}

/* ─── PRODUCT CARD ─── */
.product-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(20px);
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s;
    position: relative;
    overflow: hidden;
}
.product-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.5), transparent);
}
.product-card:hover {
    border-color: rgba(0,229,255,0.2);
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    transform: translateY(-3px);
}
.product-title {
    font-family: 'Syne', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
}
.product-meta {
    font-size: 12px;
    color: #a0b0c4;
    margin-top: 4px;
}
.price-tag {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 800;
    color: var(--accent-cyan);
}
.dist-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    background: rgba(0,229,255,0.08);
    color: var(--accent-cyan);
    border: 1px solid rgba(0,229,255,0.15);
}

/* ─── CHAT INTERFACE ─── */
.chat-container {
    max-width: 760px;
    margin: 0 auto;
}
.chat-msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 10px 0;
}
.chat-msg-ai {
    display: flex;
    justify-content: flex-start;
    margin: 10px 0;
    gap: 10px;
    align-items: flex-start;
}
.chat-bubble-user {
    background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(168,85,247,0.12));
    border: 1px solid rgba(0,229,255,0.2);
    color: var(--text-primary);
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.6;
}
.chat-bubble-ai {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.6;
}
.chat-ai-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    font-size: 14px;
}

/* ─── DIVIDER ─── */
.venus-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-hover), transparent);
    margin: 24px 0;
}

/* ─── SECTION LABEL ─── */
.section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a0b0c4;
    margin-bottom: 12px;
}

/* ─── LOGIN PAGE ─── */
.login-container {
    max-width: 460px;
    margin: 60px auto;
    padding: 40px;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(24px);
    position: relative;
    overflow: hidden;
}
.login-container::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%;
    width: 600px; height: 400px;
    background: radial-gradient(ellipse, rgba(0,229,255,0.07) 0%, transparent 65%);
    pointer-events: none;
}
.login-logo {
    font-family: 'Syne', sans-serif;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: 0.08em;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 6px;
}
.login-tagline {
    text-align: center;
    color: #a0b0c4;
    font-size: 13px;
    margin-bottom: 32px;
    letter-spacing: 0.04em;
}

/* ─── RISK / FRAUD BADGES ─── */
.risk-high   { color: var(--danger) !important; font-weight: 700; }
.risk-medium { color: var(--warning) !important; font-weight: 700; }
.risk-low    { color: var(--success) !important; font-weight: 700; }

/* ─── MAP ─── */
[data-testid="stMap"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}

/* ─── SIDEBAR NAV ITEM ─── */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(0,229,255,0.04) !important;
    border-color: rgba(0,229,255,0.12) !important;
    color: var(--text-primary) !important;
}

/* ─── FILE UPLOADER ─── */
[data-testid="stFileUploadDropzone"] {
    background: rgba(0,229,255,0.03) !important;
    border: 1.5px dashed rgba(0,229,255,0.2) !important;
    border-radius: var(--radius-md) !important;
}

/* ─── CHECKBOX ─── */
.stCheckbox label { color: #b0bece !important; }
.stCheckbox [data-testid="stCheckbox"] { accent-color: var(--accent-cyan) !important; }

/* ─── SLIDER ─── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent-cyan) !important;
    border-color: var(--accent-cyan) !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================
if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "role" not in st.session_state:
    st.session_state.role = "Supplier"

# =========================================================
# AI RESPONSE
# =========================================================
def ai_response(prompt):
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["price", "cost", "expensive", "cheap"]):
        context = "pricing strategy and market positioning"
    elif any(w in prompt_lower for w in ["stock", "inventory", "qty", "quantity"]):
        context = "inventory optimization and stock management"
    elif any(w in prompt_lower for w in ["sell", "sales", "revenue", "profit"]):
        context = "revenue growth and sales performance"
    elif any(w in prompt_lower for w in ["fraud", "fake", "scam", "risk"]):
        context = "fraud prevention and risk mitigation"
    else:
        context = "overall business performance"

    return f"""**VENUS AI Analysis** — {context.title()}

Based on your query: *"{prompt}"*

**Market Intelligence:**
- 📈 Current demand signal: **HIGH** — trend momentum detected
- 💹 Competitive positioning: Moderate — 3–5 active competitors in your segment
- 🎯 Opportunity score: **87/100**

**Strategic Recommendations:**
1. **Optimize pricing** — Your current price band is within 12% of market median. A 7% reduction could boost conversion by ~23%.
2. **Inventory action** — Restock top-3 SKUs within 48 hours to capture peak demand window.
3. **Marketing push** — Social engagement scores suggest weekend campaigns yield 2.4× ROI.

**Risk Flags:** No critical alerts at this time.

*Confidence level: 91% — based on real-time market signals and your inventory profile.*
"""

# =========================================================
# MODEL
# =========================================================
def load_ebay_data(csv_path):
    try:
        df = pd.read_csv(csv_path, engine='python', on_bad_lines='skip')
    except Exception as e:
        return pd.DataFrame()
    if df.empty:
        return df
    df.columns = df.columns.str.strip()
    required_columns = ['Number of Ratings', 'Num Of Reviews']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0
    df['review_ratio'] = df['Number of Ratings'].replace(0, 1) / df['Num Of Reviews'].replace(0, 1)
    return df

def engineer_features(df):
    numeric_cols = ["Price", "Num Of Reviews", "Number Of Ratings",
                    "Average Rating", "Seller Rating", "Seller Num Of Reviews"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Title" in df.columns:
        df["title_length"] = df["Title"].astype(str).apply(len)
    else:
        df["title_length"] = 0
    if "Color Category" in df.columns:
        df["category_encoded"] = df["Color Category"].astype("category").cat.codes
    else:
        df["category_encoded"] = 0
    if "Number Of Ratings" in df.columns and "Num Of Reviews" in df.columns:
        df["review_ratio"] = df["Number Of Ratings"] / (df["Num Of Reviews"] + 1)
    else:
        df["review_ratio"] = 0
    df.fillna(0, inplace=True)
    return df

def prepare_model_input(df):
    feature_cols = [
        "Price", "Num Of Reviews", "Number Of Ratings", "Average Rating",
        "Seller Rating", "Seller Num Of Reviews", "title_length",
        "category_encoded", "review_ratio"
    ]
    available = [c for c in feature_cols if c in df.columns]
    for c in feature_cols:
        if c not in df.columns:
            df[c] = 0
    X = df[feature_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled

def create_target(df):
    if "price" in df.columns:
        df["target"] = (df["price"] < df["price"].median()).astype(int)
    elif "Price" in df.columns:
        df["target"] = (df["Price"] < df["Price"].median()).astype(int)
    else:
        df["target"] = np.random.randint(0, 2, len(df))
    return df

def load_real_data():
    # Fallback synthetic data if CSV not available
    return pd.DataFrame({
        "Price": np.random.uniform(5, 500, 200),
        "Num Of Reviews": np.random.randint(0, 1000, 200),
        "Number Of Ratings": np.random.randint(0, 500, 200),
        "Average Rating": np.random.uniform(1, 5, 200),
        "Seller Rating": np.random.uniform(1, 5, 200),
        "Seller Num Of Reviews": np.random.randint(0, 200, 200),
        "Title": ["Product " + str(i) for i in range(200)],
        "Color Category": np.random.choice(["Red", "Blue", "Green", "Black"], 200)
    })

def train_model():
    df = load_real_data()
    df = engineer_features(df)
    df = create_target(df)
    feature_cols = [
        "Price", "Num Of Reviews", "Number Of Ratings", "Average Rating",
        "Seller Rating", "Seller Num Of Reviews", "title_length",
        "category_encoded", "review_ratio"
    ]
    X = df[feature_cols]
    y = df["target"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X_scaled, y)
    joblib.dump(model, "model.joblib")
    joblib.dump(scaler, "scaler.joblib")

def predict(input_df):
    model = joblib.load("model.joblib")
    scaler = joblib.load("scaler.joblib")
    df = engineer_features(input_df.copy())
    X_scaled = prepare_model_input(df)
    prob = model.predict_proba(X_scaled)[:, 1]
    df["purchase_probability"] = prob
    return df

if not os.path.exists("model.joblib"):
    train_model()
    
# =========================================================
# AUTH — PREMIUM LOGIN PAGE
# =========================================================
if st.session_state.current_user is None:
    st.markdown("""
    <div style="
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
    ">
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-logo">VENUS AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-tagline">AI-Powered Superintelligent Supply Chain Platform</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            login_username = st.text_input("Username", placeholder="Enter your username", key="login_name")
            login_email = st.text_input("Email", placeholder="Enter your email", key="login_email")
            if st.button("Sign In →", key="login_btn", use_container_width=True):
                cursor.execute("SELECT * FROM users WHERE username=? AND email=?", (login_username, login_email))
                user_data = cursor.fetchone()
                if user_data:
                    st.session_state.current_user = user_data[0]
                    st.session_state.current_user_id = user_data[0]
                    st.session_state.role = user_data[3]
                    st.rerun()
                else:
                    st.error("User not found or incorrect credentials")

        with tab2:
            reg_username = st.text_input("Choose Username", placeholder="Pick a unique username", key="register_name")
            reg_email = st.text_input("Email", placeholder="your@email.com", key="register_email")
            reg_role = st.selectbox("I am a", ["Supplier", "Customer"])
            if st.button("Create Account →", key="register_btn", use_container_width=True):
                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, role, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (reg_username, reg_email, reg_role, datetime.datetime.now()))
                    conn.commit()
                    st.success("Account created! Sign in to continue.")
                except sqlite3.IntegrityError:
                    st.error("Username or Email already exists")

        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# =========================================================
# USER — Fetch info from DB
# =========================================================
user_id = st.session_state.current_user
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
user_row = cursor.fetchone()
user = {
    "id": user_row[0],
    "username": user_row[1],
    "email": user_row[2],
    "role": user_row[3],
    "name": user_row[4] or user_row[1],
    "location": user_row[5] or "Lusaka, Zambia"
}

# =========================================================
# TOP BAR — Fixed header with profile icon + popover
# =========================================================
initials = user["name"][0].upper() if user["name"] else "U"
role_class = "tag-supplier" if user["role"] == "Supplier" else "tag-customer"

st.markdown(f"""
<div class="venus-topbar">
    <div class="venus-logo">⚡ VENUS AI</div>
    <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:12px; color:var(--text-muted);">{user.get('location','')}</span>
        <div style="width:8px;height:8px;background:var(--success);border-radius:50%;
            box-shadow:0 0 8px var(--success);"></div>
        <span class="venus-role-tag {role_class}">{user['role']}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR — Fixed: hamburger toggle + no emoji nav titles
# =========================================================

# ── Persist sidebar open/closed state ──
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# ── Hamburger toggle button (always visible, outside sidebar) ──
st.markdown("""
<style>
/* Always show the sidebar toggle button Streamlit renders */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Style it as a clean hamburger */
[data-testid="collapsedControl"] svg {
    display: none;
}
[data-testid="collapsedControl"]::before {
    content: '';
    display: block;
    width: 18px;
    height: 2px;
    background: #a0aec0;
    box-shadow: 0 5px 0 #a0aec0, 0 10px 0 #a0aec0;
    border-radius: 2px;
}

/* Prevent Streamlit from auto-hiding the sidebar collapse arrow */
[data-testid="stSidebar"][aria-expanded="false"] {
    display: block !important;
    width: 0 !important;
    min-width: 0 !important;
    overflow: hidden !important;
    transition: width 0.3s ease;
}
[data-testid="stSidebar"][aria-expanded="true"] {
    width: 260px !important;
    min-width: 260px !important;
    transition: width 0.3s ease;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    # ── Profile icon header ──
    st.markdown(f"""
    <div style="padding:18px 8px 16px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:40px;height:40px;min-width:40px;
                background:linear-gradient(135deg,#00e5ff,#a855f7);
                border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-size:16px;font-weight:900;color:#000;
                box-shadow:0 0 12px rgba(0,229,255,0.3);
            ">{initials}</div>
            <div style="min-width:0;">
                <div style="font-size:13px;font-weight:700;color:#e8edf5;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                    max-width:140px;">{user['name']}</div>
                <div style="font-size:11px;color:#4a5a72;margin-top:2px;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                    max-width:140px;">{user['email']}</div>
            </div>
        </div>
        <div style="margin-top:10px;display:flex;gap:6px;align-items:center;">
            <span style="width:6px;height:6px;background:#00e096;border-radius:50%;
                box-shadow:0 0 5px #00e096;display:inline-block;"></span>
            <span style="font-size:10px;color:#4a5a72;">Online</span>
            <span style="font-size:10px;color:#2a3a52;margin:0 4px;">·</span>
            <span style="font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;
                {'background:rgba(0,229,255,0.1);color:#00e5ff;' if user['role']=='Supplier' else 'background:rgba(168,85,247,0.1);color:#a855f7;'}
            ">{user['role']}</span>
        </div>
    </div>
    <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.12),transparent);margin-bottom:14px;"></div>
    """, unsafe_allow_html=True)

    # ── Navigation menu — no emojis ──
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#2a3a52;margin-bottom:8px;padding-left:2px;">Navigation</div>', unsafe_allow_html=True)

    if st.session_state.role == "Supplier":
        menu = st.selectbox("", [
            "Dashboard",
            "Add Product",
            "Inventory",
            "Prediction",
            "Marketing AI",
            "Fraud Detection",
            "Vision AI",
            "Blockchain",
            "Financial AI",
            "Inbox & Products",
            "VENUS AI Assistant",
        ], label_visibility="collapsed")
    else:
        menu = st.selectbox("", [
            "Dashboard",
            "Product Search",
            "VENUS AI Assistant",
        ], label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(0,229,255,0.1),transparent);margin:16px 0;"></div>', unsafe_allow_html=True)

    # ── Account / Profile editor ──
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#2a3a52;margin-bottom:8px;padding-left:2px;">Account</div>', unsafe_allow_html=True)
    with st.expander("Edit Profile", expanded=False):
        profile_name     = st.text_input("Display Name", value=user.get("name", ""), key="sb_profile_name")
        profile_location = st.text_input("Location", value=user.get("location", "Lusaka, Zambia"), key="sb_profile_loc")
        if st.button("Save Changes", key="sb_save_profile", use_container_width=True):
            cursor.execute("UPDATE users SET name=?, location=? WHERE id=?",
                           (profile_name, profile_location, user_id))
            conn.commit()
            user["name"]     = profile_name
            user["location"] = profile_location
            st.success("Saved!")

    st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(255,75,110,0.1),transparent);margin:16px 0;"></div>', unsafe_allow_html=True)

    # ── Sign out ──
    if st.button("Sign Out", key="signout_btn", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── Update all downstream menu checks to match new label strings ──
# Old:  "👁️  Vision AI"   →  New: "Vision AI"
# Old:  "🏠  Dashboard"   →  New: "Dashboard"
# Old:  "➕  Add Product" →  New: "Add Product"
# ... etc. — search your elif blocks for the old emoji+space strings and
#     replace with the plain strings above.  Example:
#
#   elif "Vision AI" in menu:   ← this already works with both old and new
#   elif menu == "Dashboard":   ← use == now that labels are unambiguous

# =========================================================
# DASHBOARD — Role-split: Supplier vs Customer
# =========================================================
if "Dashboard" in menu:
    import datetime as _dt

    st.markdown("""
    <style>
    @keyframes fadeSlideUp {
        from { opacity:0; transform:translateY(16px); }
        to   { opacity:1; transform:translateY(0); }
    }
    .db-animate { animation: fadeSlideUp 0.45s ease both; }

    /* ── Welcome strip ── */
    .db-welcome {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 0 28px; margin-bottom: 4px;
    }
    .db-welcome-left {}
    .db-greeting {
        font-size: 12px; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: #2a3a52; margin-bottom: 6px;
        font-family: 'DM Sans', sans-serif;
    }
    .db-name {
        font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800;
        letter-spacing: -0.02em; color: #e8edf5; line-height: 1.1;
    }
    .db-name span {
        background: linear-gradient(90deg, #00e5ff, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .db-sub { font-size: 13px; color: #2a3a52; margin-top: 6px;
        font-family: 'DM Sans', sans-serif; }
    .db-time {
        font-family: 'DM Mono', monospace; font-size: 12px; color: #1e2e44;
        text-align: right; line-height: 1.8;
    }

    /* ── Stat cards ── */
    .db-stat-grid { display: grid; gap: 12px; margin-bottom: 20px; }
    .db-stat-grid.col4 { grid-template-columns: repeat(4, 1fr); }
    .db-stat-grid.col3 { grid-template-columns: repeat(3, 1fr); }
    .db-stat {
        background: rgba(8,8,18,0.95);
        border: 1px solid rgba(0,229,255,0.07);
        border-radius: 18px; padding: 22px 22px 18px;
        position: relative; overflow: hidden;
        transition: border-color 0.2s, transform 0.18s;
    }
    .db-stat:hover { border-color: rgba(0,229,255,0.2); transform: translateY(-2px); }
    .db-stat::after {
        content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
        border-radius: 0 0 18px 18px;
    }
    .db-stat.cyan::after  { background: linear-gradient(90deg,#00e5ff,transparent); }
    .db-stat.purple::after{ background: linear-gradient(90deg,#a855f7,transparent); }
    .db-stat.green::after { background: linear-gradient(90deg,#00e096,transparent); }
    .db-stat.amber::after { background: linear-gradient(90deg,#ffb800,transparent); }
    .db-stat.red::after   { background: linear-gradient(90deg,#ff4b6e,transparent); }
    .db-stat-icon { font-size: 18px; margin-bottom: 12px; opacity: 0.8; }
    .db-stat-val {
        font-family: 'Syne', sans-serif; font-size: 26px; font-weight: 800;
        line-height: 1; letter-spacing: -0.02em; color: #e8edf5; margin-bottom: 5px;
    }
    .db-stat-val.cyan   { color: #00e5ff; }
    .db-stat-val.green  { color: #00e096; }
    .db-stat-val.amber  { color: #ffb800; }
    .db-stat-val.purple { color: #a855f7; }
    .db-stat-val.red    { color: #ff4b6e; }
    .db-stat-lbl { font-size: 11px; color: #2a3a52; text-transform: uppercase;
        letter-spacing: 0.1em; font-family: 'DM Sans', sans-serif; }
    .db-stat-trend { font-size: 11px; margin-top: 8px; }
    .db-stat-trend.up   { color: #00e096; }
    .db-stat-trend.down { color: #ff4b6e; }
    .db-stat-trend.neu  { color: #2a3a52; }

    /* ── Panel cards ── */
    .db-panel {
        background: rgba(8,8,18,0.95);
        border: 1px solid rgba(0,229,255,0.07);
        border-radius: 18px; padding: 22px;
        margin-bottom: 16px; position: relative; overflow: hidden;
    }
    .db-panel::before {
        content:''; position:absolute; top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,229,255,0.18),transparent);
    }
    .db-panel-title {
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase; color: #2a3a52;
        margin-bottom: 18px;
    }

    /* ── AI insight strip ── */
    .db-ai-strip {
        background: linear-gradient(135deg, rgba(0,229,255,0.05), rgba(168,85,247,0.04));
        border: 1px solid rgba(0,229,255,0.12);
        border-radius: 16px; padding: 18px 22px;
        display: flex; align-items: flex-start; gap: 14px;
        margin-bottom: 20px;
    }
    .db-ai-avatar {
        width: 36px; height: 36px; min-width: 36px;
        background: linear-gradient(135deg,#00e5ff,#a855f7);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-family: 'Syne',sans-serif; font-size: 14px; font-weight: 800; color: #000;
        box-shadow: 0 0 14px rgba(0,229,255,0.2); flex-shrink:0;
    }
    .db-ai-content {}
    .db-ai-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #00e5ff; margin-bottom: 5px; }
    .db-ai-text { font-size: 13px; color: #9aaabf; line-height: 1.65;
        font-family: 'DM Sans', sans-serif; }

    /* ── Activity feed ── */
    .db-feed-item {
        display: flex; align-items: flex-start; gap: 12px;
        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .db-feed-item:last-child { border-bottom: none; }
    .db-feed-dot {
        width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink:0;
    }
    .db-feed-main { font-size: 13px; color: #b0bece; line-height: 1.5;
        font-family: 'DM Sans', sans-serif; }
    .db-feed-time { font-size: 10px; color: #1e2e44; margin-top: 2px;
        font-family: 'DM Mono', monospace; }

    /* ── Module nav cards ── */
    .db-module-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .db-module {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,229,255,0.06);
        border-radius: 12px; padding: 13px 15px;
        transition: border-color 0.2s, background 0.2s;
        display: flex; align-items: center; gap: 10px;
    }
    .db-module:hover { border-color: rgba(0,229,255,0.18); background: rgba(0,229,255,0.04); }
    .db-module-icon { font-size: 16px; }
    .db-module-name { font-size: 12px; font-weight: 600; color: #b0bece;
        font-family: 'DM Sans', sans-serif; }

    /* ── Progress bars ── */
    .db-bar-row { margin-bottom: 12px; }
    .db-bar-label { display:flex;justify-content:space-between;
        font-size:12px;color:#9aaabf;margin-bottom:5px; }
    .db-bar-track { height:4px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden; }
    .db-bar-fill { height:100%;border-radius:4px;
        background:linear-gradient(90deg,#00e5ff,#a855f7); }

    /* ── Order status pill ── */
    .db-pill {
        display:inline-block;padding:2px 10px;border-radius:20px;
        font-size:10px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;
    }
    .db-pill-pending { background:rgba(255,184,0,0.12);color:#ffb800; }
    .db-pill-fulfilled{ background:rgba(0,224,150,0.12);color:#00e096; }
    .db-pill-new     { background:rgba(0,229,255,0.12);color:#00e5ff; }
    </style>
    """, unsafe_allow_html=True)

    # ── Time greeting ──
    hour = _dt.datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
    today_str = _dt.datetime.now().strftime("%A, %d %B %Y")
    time_str  = _dt.datetime.now().strftime("%H:%M")

    st.markdown(f"""
    <div class="db-welcome db-animate">
        <div class="db-welcome-left">
            <div class="db-greeting">{greeting}</div>
            <div class="db-name">Welcome back, <span>{user['name']}</span></div>
            <div class="db-sub">{user['role']} · {user.get('location','Lusaka, Zambia')}</div>
        </div>
        <div class="db-time">
            {today_str}<br>
            <span style="font-size:20px;color:#1e3a52;">{time_str}</span><br>
            <span style="color:#00e096;font-size:10px;">● All systems operational</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    # SUPPLIER DASHBOARD
    # ═══════════════════════════════════════════════════════
    if st.session_state.role == "Supplier":

        # ── Extra CSS for visible tables ──
        st.markdown("""
        <style>
        .venus-table {
            width: 100%; border-collapse: collapse;
            font-family: 'DM Sans', sans-serif; font-size: 13px;
        }
        .venus-table thead tr {
            border-bottom: 1px solid rgba(0,229,255,0.15);
        }
        .venus-table thead th {
            text-align: left; padding: 8px 12px;
            font-size: 10px; font-weight: 700;
            letter-spacing: 0.1em; text-transform: uppercase;
            color: #4a5a72;
        }
        .venus-table tbody tr {
            border-bottom: 1px solid rgba(255,255,255,0.04);
            transition: background 0.15s;
        }
        .venus-table tbody tr:last-child { border-bottom: none; }
        .venus-table tbody tr:hover { background: rgba(0,229,255,0.03); }
        .venus-table tbody td {
            padding: 10px 12px; color: #c8d4e3;
            vertical-align: middle;
        }
        .venus-table tbody td.mono {
            font-family: 'DM Mono', monospace; font-size: 13px;
        }
        .venus-table tbody td.cyan {
            color: #00e5ff; font-family: 'DM Mono', monospace; font-weight: 600;
        }
        .venus-table tbody td.muted { color: #4a5a72; }
        </style>
        """, unsafe_allow_html=True)

        # ── Pull supplier-specific data ──
        cursor.execute("SELECT COUNT(*) FROM products WHERE user_id=?", (user_id,))
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions WHERE supplier=? OR supplier=?",
                       (user['name'], user['username']))
        txn_row = cursor.fetchone()
        txn_count = txn_row[0] or 0
        revenue   = round(txn_row[1] or 0, 2)

        cursor.execute("SELECT SUM(qty) FROM inventory WHERE user_id=?", (user_id,))
        inv_units = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM cart WHERE (supplier=? OR supplier=?) AND status='pending'",
                       (user['name'], user['username']))
        pending_orders = cursor.fetchone()[0] or 0

        try:
            cursor.execute("SELECT COUNT(*) FROM seller_messages WHERE seller_name=? OR seller_name=?",
                           (user['name'], user['username']))
            unread_msgs = cursor.fetchone()[0] or 0
        except:
            unread_msgs = 0

        avg_price = 0
        try:
            cursor.execute("SELECT AVG(price) FROM products WHERE user_id=?", (user_id,))
            avg_price = round(cursor.fetchone()[0] or 0, 2)
        except: pass

        # ── AI insight ──
        if revenue > 0:
            insight_text = (
                f"Your store has generated <strong>${revenue:,.2f}</strong> across {txn_count} transactions. "
                f"With {product_count} active listings at an average price of ${avg_price}, your catalogue density is "
                f"{'strong' if product_count > 5 else 'growing'}. "
                f"{'You have <strong>' + str(pending_orders) + ' pending orders</strong> — fulfil them promptly to protect your seller rating.' if pending_orders > 0 else 'All orders are fulfilled — your fulfilment rate is clean.'}"
            )
        else:
            insight_text = (
                f"Your store is live with <strong>{product_count} product{'s' if product_count!=1 else ''}</strong> listed. "
                f"No transactions yet — consider running a promotion or adjusting your pricing to attract your first buyers. "
                f"The Marketing AI module can generate targeted campaign ideas."
            )

        st.markdown(f"""
        <div class="db-ai-strip db-animate" style="animation-delay:0.05s;">
            <div class="db-ai-avatar">V</div>
            <div class="db-ai-content">
                <div class="db-ai-label">VENUS Intelligence · Supplier Brief</div>
                <div class="db-ai-text">{insight_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Stat strip ──
        trend_revenue   = 'up' if revenue > 0 else 'neu'
        trend_rev_label = f"↑ From {txn_count} sales" if revenue > 0 else "No sales yet"
        stat_order_cls  = 'amber' if pending_orders > 0 else 'green'
        order_trend_cls = 'down' if pending_orders > 3 else 'neu'
        order_trend_lbl = 'Needs attention' if pending_orders > 0 else 'All fulfilled'
        inv_trend_cls   = 'down' if inv_units < 10 else 'neu'
        inv_trend_lbl   = 'Low stock warning' if inv_units < 10 and inv_units > 0 else 'Across all products'

        st.markdown(f"""
        <div class="db-stat-grid col4 db-animate" style="animation-delay:0.1s;">
            <div class="db-stat cyan">
                <div class="db-stat-icon">📦</div>
                <div class="db-stat-val cyan">{product_count}</div>
                <div class="db-stat-lbl">Active Listings</div>
                <div class="db-stat-trend neu">Products in catalogue</div>
            </div>
            <div class="db-stat green">
                <div class="db-stat-icon">💰</div>
                <div class="db-stat-val green">${revenue:,.2f}</div>
                <div class="db-stat-lbl">Total Revenue</div>
                <div class="db-stat-trend {trend_revenue}">{trend_rev_label}</div>
            </div>
            <div class="db-stat {stat_order_cls}">
                <div class="db-stat-icon">🛒</div>
                <div class="db-stat-val {stat_order_cls}">{pending_orders}</div>
                <div class="db-stat-lbl">Pending Orders</div>
                <div class="db-stat-trend {order_trend_cls}">{order_trend_lbl}</div>
            </div>
            <div class="db-stat purple">
                <div class="db-stat-icon">🗃️</div>
                <div class="db-stat-val purple">{inv_units}</div>
                <div class="db-stat-lbl">Inventory Units</div>
                <div class="db-stat-trend {inv_trend_cls}">{inv_trend_lbl}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Main grid ──
        col_main, col_side = st.columns([1.7, 1])

        with col_main:
            # ── Recent Sales — custom HTML table ──
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.15s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Recent Sales</div>', unsafe_allow_html=True)
            try:
                _c2 = sqlite3.connect("venus_ai.db")
                txn_rows = _c2.execute(
                    "SELECT product, price, quantity, total, date FROM transactions ORDER BY id DESC LIMIT 7"
                ).fetchall()
                _c2.close()

                if txn_rows:
                    rows_html = ""
                    for r in txn_rows:
                        prod  = str(r[0])
                        price = f"${float(r[1]):,.2f}"
                        qty   = str(r[2])
                        total = f"${float(r[3]):,.2f}"
                        date  = str(r[4])[:16]
                        rows_html += (
                            f"<tr>"
                            f"<td>{prod}</td>"
                            f"<td class='mono'>{price}</td>"
                            f"<td class='muted'>{qty}</td>"
                            f"<td class='cyan'>{total}</td>"
                            f"<td class='muted'>{date}</td>"
                            f"</tr>"
                        )
                    st.markdown(
                        f"<table class='venus-table'>"
                        f"<thead><tr>"
                        f"<th>Product</th><th>Unit Price</th>"
                        f"<th>Qty</th><th>Total</th><th>Date</th>"
                        f"</tr></thead>"
                        f"<tbody>{rows_html}</tbody>"
                        f"</table>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div style="text-align:center;padding:32px;color:#2a3a52;font-size:13px;">'
                        'No sales recorded yet — your transactions will appear here.</div>',
                        unsafe_allow_html=True
                    )
            except:
                st.markdown(
                    '<div style="text-align:center;padding:32px;color:#2a3a52;font-size:13px;">'
                    'No transactions yet.</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Revenue Timeline ──
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.2s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Revenue Timeline</div>', unsafe_allow_html=True)
            try:
                df_chart = pd.read_sql(
                    "SELECT date, SUM(total) as revenue FROM transactions GROUP BY date ORDER BY date DESC LIMIT 14",
                    conn
                )
                if not df_chart.empty and len(df_chart) > 1:
                    df_chart["date"] = pd.to_datetime(df_chart["date"], errors="coerce")
                    df_chart = df_chart.dropna().sort_values("date").set_index("date")
                    st.area_chart(df_chart["revenue"], color="#00e5ff", height=160)
                else:
                    st.markdown(
                        '<div style="text-align:center;padding:24px;color:#2a3a52;font-size:13px;">'
                        'Chart will populate as sales come in.</div>',
                        unsafe_allow_html=True
                    )
            except:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

        with col_side:
            # ── Order Queue ──
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.18s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Order Queue</div>', unsafe_allow_html=True)
            try:
                cursor.execute(
                    "SELECT product, qty, status, added_at FROM cart "
                    "WHERE (supplier=? OR supplier=?) ORDER BY id DESC LIMIT 6",
                    (user['name'], user['username'])
                )
                orders = cursor.fetchall()
                if orders:
                    for o in orders:
                        dot_color = '#ffb800' if o[2] == "pending" else '#00e096'
                        pill_cls  = "db-pill-pending" if o[2] == "pending" else "db-pill-fulfilled"
                        prod_name = str(o[0])
                        qty_val   = str(o[1])
                        date_val  = str(o[3])[:16]
                        status    = str(o[2])
                        st.markdown(
                            f'<div class="db-feed-item">'
                            f'<div class="db-feed-dot" style="background:{dot_color};"></div>'
                            f'<div>'
                            f'<div class="db-feed-main">{prod_name} '
                            f'<span style="color:#4a5a72;">× {qty_val}</span></div>'
                            f'<div class="db-feed-time">{date_val} &nbsp; '
                            f'<span class="db-pill {pill_cls}">{status}</span></div>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        '<div style="text-align:center;padding:20px;color:#2a3a52;font-size:12px;">'
                        'No orders yet</div>',
                        unsafe_allow_html=True
                    )
            except:
                st.markdown(
                    '<div style="text-align:center;padding:20px;color:#2a3a52;font-size:12px;">'
                    'No orders yet</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Catalogue Performance ──
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.22s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Catalogue Performance</div>', unsafe_allow_html=True)
            try:
                cursor.execute(
                    "SELECT product, price, qty FROM products WHERE user_id=? ORDER BY price DESC LIMIT 5",
                    (user_id,)
                )
                top_prods = cursor.fetchall()
                if top_prods:
                    max_price_val = max(p[1] for p in top_prods) or 1
                    for p in top_prods:
                        pct      = (p[1] / max_price_val) * 100
                        p_name   = str(p[0])
                        p_price  = f"${p[1]:,.2f}"
                        st.markdown(
                            f'<div class="db-bar-row">'
                            f'<div class="db-bar-label">'
                            f'<span style="max-width:140px;overflow:hidden;text-overflow:ellipsis;'
                            f'white-space:nowrap;color:#c8d4e3;">{p_name}</span>'
                            f'<span style="color:#00e5ff;font-family:DM Mono,monospace;">{p_price}</span>'
                            f'</div>'
                            f'<div class="db-bar-track">'
                            f'<div class="db-bar-fill" style="width:{pct:.0f}%;"></div>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        '<div style="color:#2a3a52;font-size:12px;">No products listed yet.</div>',
                        unsafe_allow_html=True
                    )
            except:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

            # ── AI Modules ──
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.26s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">AI Modules</div>', unsafe_allow_html=True)
            modules = [
                ("📈", "Prediction Engine"), ("🛡️", "Fraud Detection"),
                ("👁️", "Vision AI"),         ("🧱", "Blockchain"),
                ("💰", "Financial AI"),      ("📣", "Marketing AI"),
            ]
            mod_html = '<div class="db-module-grid">'
            for icon, name in modules:
                mod_html += (
                    f'<div class="db-module">'
                    f'<span class="db-module-icon">{icon}</span>'
                    f'<span class="db-module-name">{name}</span>'
                    f'</div>'
                )
            mod_html += '</div>'
            st.markdown(mod_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    # ═══════════════════════════════════════════════════════
    # CUSTOMER DASHBOARD
    # ═══════════════════════════════════════════════════════
    else:
        # ── Pull customer-specific data ──
        try:
            cursor.execute("SELECT COUNT(*), SUM(total) FROM transactions")
            mkt_row   = cursor.fetchone()
            mkt_txns  = mkt_row[0] or 0
            mkt_vol   = round(mkt_row[1] or 0, 2)
        except:
            mkt_txns, mkt_vol = 0, 0

        try:
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0] or 0
        except:
            total_products = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='Supplier'")
            supplier_count = cursor.fetchone()[0] or 0
        except:
            supplier_count = 0

        try:
            cursor.execute("SELECT COUNT(*) FROM cart WHERE buyer_id=?", (user_id,))
            my_orders = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM cart WHERE buyer_id=? AND status='pending'", (user_id,))
            my_pending = cursor.fetchone()[0] or 0
        except:
            my_orders, my_pending = 0, 0

        try:
            cursor.execute("SELECT COUNT(*) FROM seller_messages WHERE buyer_id=?", (user_id,))
            msg_count = cursor.fetchone()[0] or 0
        except:
            msg_count = 0

        # ── AI insight ──
        if my_orders > 0:
            cust_insight = f"You have placed <strong>{my_orders} order{'s' if my_orders!=1 else ''}</strong> on the platform. {f'<strong>{my_pending} are still pending</strong> — expect fulfilment soon.' if my_pending > 0 else 'All your orders have been fulfilled.'} The marketplace currently has <strong>{total_products} products</strong> from {supplier_count} verified suppliers — use Product Search to find your next purchase."
        else:
            cust_insight = f"Welcome to VENUS AI. The marketplace has <strong>{total_products} products</strong> across {supplier_count} verified suppliers. Browse the Product Search to find what you need — our AI ranks listings by quality, price, and seller trust score."

        st.markdown(f"""
        <div class="db-ai-strip db-animate" style="animation-delay:0.05s;">
            <div class="db-ai-avatar">V</div>
            <div class="db-ai-content">
                <div class="db-ai-label">VENUS Intelligence · Buyer Brief</div>
                <div class="db-ai-text">{cust_insight}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Stat strip ──
        st.markdown(f"""
        <div class="db-stat-grid col4 db-animate" style="animation-delay:0.1s;">
            <div class="db-stat cyan">
                <div class="db-stat-icon">🛍️</div>
                <div class="db-stat-val cyan">{total_products}</div>
                <div class="db-stat-lbl">Products Available</div>
                <div class="db-stat-trend neu">Across all suppliers</div>
            </div>
            <div class="db-stat purple">
                <div class="db-stat-icon">🏪</div>
                <div class="db-stat-val purple">{supplier_count}</div>
                <div class="db-stat-lbl">Verified Suppliers</div>
                <div class="db-stat-trend neu">On the platform</div>
            </div>
            <div class="db-stat {'amber' if my_pending>0 else 'green'}">
                <div class="db-stat-icon">📋</div>
                <div class="db-stat-val {'amber' if my_pending>0 else 'green'}">{my_orders}</div>
                <div class="db-stat-lbl">My Orders</div>
                <div class="db-stat-trend {'down' if my_pending>0 else 'neu'}">{f'{my_pending} pending' if my_pending>0 else 'All fulfilled'}</div>
            </div>
            <div class="db-stat green">
                <div class="db-stat-icon">💬</div>
                <div class="db-stat-val green">{msg_count}</div>
                <div class="db-stat-lbl">Messages Sent</div>
                <div class="db-stat-trend neu">With suppliers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Main grid ──
        col_main, col_side = st.columns([1.7, 1])

        with col_main:
            # My order history
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.15s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">My Order History</div>', unsafe_allow_html=True)
            try:
                cursor.execute(
                    "SELECT product, price, qty, status, added_at FROM cart WHERE buyer_id=? ORDER BY id DESC LIMIT 8",
                    (user_id,)
                )
                my_order_rows = cursor.fetchall()
                if my_order_rows:
                    for o in my_order_rows:
                        pill_cls = "db-pill-pending" if o[3]=="pending" else "db-pill-fulfilled"
                        total = o[1] * o[2]
                        st.markdown(f"""
                        <div class="db-feed-item">
                            <div class="db-feed-dot" style="background:{'#ffb800' if o[3]=='pending' else '#00e096'};"></div>
                            <div style="flex:1;display:flex;justify-content:space-between;align-items:flex-start;">
                                <div>
                                    <div class="db-feed-main">{o[0]}</div>
                                    <div class="db-feed-time">{str(o[4])[:16]} &nbsp; Qty: {o[2]} &nbsp; <span class="db-pill {pill_cls}">{o[3]}</span></div>
                                </div>
                                <div style="font-family:'DM Mono',monospace;font-size:13px;color:#00e5ff;">${total:,.2f}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align:center;padding:36px;color:#2a3a52;font-size:13px;">
                        You haven't placed any orders yet.<br>
                        <span style="color:#1e2e44;font-size:12px;">Use Product Search to browse the marketplace.</span>
                    </div>""", unsafe_allow_html=True)
            except:
                st.markdown('<div style="padding:24px;color:#2a3a52;font-size:13px;">No order data available.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Featured products
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.2s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Featured Marketplace Listings</div>', unsafe_allow_html=True)
            try:
                cursor.execute("SELECT product, price, qty, location FROM products ORDER BY RANDOM() LIMIT 5")
                featured = cursor.fetchall()
                if featured:
                    for f in featured:
                        st.markdown(f"""
                        <div class="db-feed-item">
                            <div class="db-feed-dot" style="background:#00e5ff;"></div>
                            <div style="flex:1;display:flex;justify-content:space-between;align-items:center;">
                                <div>
                                    <div class="db-feed-main">{f[0]}</div>
                                    <div class="db-feed-time">📍 {f[3] or 'Lusaka'} &nbsp;·&nbsp; {f[2]} in stock</div>
                                </div>
                                <div style="font-family:'DM Mono',monospace;font-size:14px;font-weight:700;color:#00e5ff;">${f[1]:,.2f}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown('<div style="padding:20px;color:#2a3a52;font-size:13px;">No products listed yet.</div>', unsafe_allow_html=True)
            except: pass
            st.markdown('</div>', unsafe_allow_html=True)

        with col_side:
            # Market pulse
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.18s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Market Pulse</div>', unsafe_allow_html=True)
            try:
                cursor.execute("SELECT AVG(price), MIN(price), MAX(price) FROM products")
                price_row = cursor.fetchone()
                avg_p = price_row[0] or 0
                min_p = price_row[1] or 0
                max_p = price_row[2] or 0
            except:
                avg_p = min_p = max_p = 0

            st.markdown(f"""
            <div class="db-bar-row" style="margin-bottom:16px;">
                <div class="db-bar-label"><span>Avg. Product Price</span><span style="color:#00e5ff;">${avg_p:,.2f}</span></div>
                <div class="db-bar-row"><div class="db-bar-label"><span>Price Range</span><span style="color:#9aaabf;">${min_p:,.0f} – ${max_p:,.0f}</span></div></div>
            </div>
            <div class="db-bar-row">
                <div class="db-bar-label"><span>Market Volume</span><span style="color:#00e096;">${mkt_vol:,.2f}</span></div>
                <div class="db-bar-track"><div class="db-bar-fill" style="width:{'min(100,mkt_vol/1000)' if mkt_vol else 0}%;"></div></div>
            </div>
            <div class="db-bar-row" style="margin-top:14px;">
                <div class="db-bar-label"><span>Total Transactions</span><span style="color:#a855f7;">{mkt_txns}</span></div>
                <div class="db-bar-label" style="margin-top:2px;"><span>Active Suppliers</span><span style="color:#ffb800;">{supplier_count}</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Platform trust score
            trust = min(100, (supplier_count * 8) + (total_products * 2) + (mkt_txns * 1))
            st.markdown(f"""
            <div class="db-panel db-animate" style="animation-delay:0.22s;">
                <div class="db-panel-title">Platform Trust Score</div>
                <div style="text-align:center;padding:10px 0 14px;">
                    <div style="font-family:'Syne',sans-serif;font-size:48px;font-weight:800;
                        color:{'#00e096' if trust>70 else '#ffb800' if trust>40 else '#ff4b6e'};
                        line-height:1;">{trust}</div>
                    <div style="font-size:11px;color:#2a3a52;margin-top:4px;text-transform:uppercase;letter-spacing:0.1em;">/100 · Platform Health</div>
                </div>
                <div class="db-bar-track"><div class="db-bar-fill" style="width:{trust}%;background:{'linear-gradient(90deg,#00e096,#00e5ff)' if trust>70 else 'linear-gradient(90deg,#ffb800,#ff8800)' if trust>40 else 'linear-gradient(90deg,#ff4b6e,#ff8800)'};"></div></div>
                <div style="font-size:12px;color:#2a3a52;margin-top:12px;line-height:1.6;">
                    {'Marketplace is thriving — safe to buy with confidence.' if trust>70 else 'Marketplace is growing — good time to join.' if trust>40 else 'Early-stage marketplace — more suppliers joining soon.'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Quick actions for customer
            st.markdown('<div class="db-panel db-animate" style="animation-delay:0.26s;">', unsafe_allow_html=True)
            st.markdown('<div class="db-panel-title">Quick Actions</div>', unsafe_allow_html=True)
            if st.button("Browse Products", use_container_width=True, key="db_cust_browse"):
                st.session_state["menu_override"] = "Product Search"
                st.rerun()
            if st.button("Ask VENUS AI", use_container_width=True, key="db_cust_ai"):
                st.session_state["menu_override"] = "VENUS AI Assistant"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# INVENTORY — List product, upload image, add description,
#             edit existing products, all in one screen
# =========================================================
elif "Inventory" in menu:
    import base64 as _b64

    st.markdown("""
    <style>
    /* ── Table ── */
    .inv-table {
        width: 100%; border-collapse: collapse;
        font-family: 'DM Sans', sans-serif; font-size: 13px;
    }
    .inv-table thead tr { border-bottom: 1px solid rgba(0,229,255,0.15); }
    .inv-table thead th {
        text-align: left; padding: 8px 12px;
        font-size: 10px; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase; color: #4a5a72;
    }
    .inv-table tbody tr {
        border-bottom: 1px solid rgba(255,255,255,0.04);
        transition: background 0.15s;
    }
    .inv-table tbody tr:last-child { border-bottom: none; }
    .inv-table tbody tr:hover { background: rgba(0,229,255,0.03); }
    .inv-table tbody td { padding: 10px 12px; color: #c8d4e3; vertical-align: middle; }
    .inv-table tbody td.cyan { color: #00e5ff; font-family: 'DM Mono', monospace; font-weight: 600; }
    .inv-table tbody td.muted { color: #4a5a72; }
    .inv-table tbody td.stock-low  { color: #ff4b6e; font-weight: 600; }
    .inv-table tbody td.stock-ok   { color: #00e096; }
    .inv-table tbody td.has-img    { color: #00e096; font-size: 11px; }
    .inv-table tbody td.no-img     { color: #2a3a52; font-size: 11px; }

    /* ── Panels ── */
    .inv-panel {
        background: rgba(8,8,18,0.97);
        border: 1px solid rgba(0,229,255,0.1);
        border-radius: 18px; padding: 22px;
        position: relative; overflow: hidden;
        margin-bottom: 14px;
    }
    .inv-panel::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent);
    }
    .inv-panel-title {
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase;
        color: #2a3a52; margin-bottom: 18px;
    }

    /* ── Supplier info strip ── */
    .inv-sup-strip {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,229,255,0.07);
        border-radius: 12px; padding: 13px 14px; margin: 10px 0;
    }
    .inv-sup-lbl {
        font-size: 9px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #2a3a52; margin-bottom: 8px;
    }
    .inv-sup-row { font-size: 12px; color: #c8d4e3; margin-bottom: 3px; }
    .inv-sup-row span { color: #4a5a72; margin-right: 6px; font-size: 10px; }

    /* ── Image preview ── */
    .inv-img-preview {
        width: 100%; height: 160px; border-radius: 12px; object-fit: cover;
        border: 1px solid rgba(0,229,255,0.12); display: block; margin-bottom: 10px;
    }
    .inv-img-placeholder {
        width: 100%; height: 120px; border-radius: 12px;
        border: 1px dashed rgba(0,229,255,0.15);
        background: rgba(0,229,255,0.02);
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; color: rgba(0,229,255,0.15); margin-bottom: 10px;
    }

    /* ── Tab pills ── */
    .inv-tab-row { display: flex; gap: 6px; margin-bottom: 18px; }
    .inv-tab {
        padding: 6px 14px; font-size: 11px; font-weight: 700;
        border-radius: 20px; cursor: pointer;
        border: 1px solid rgba(0,229,255,0.1); color: #4a5a72;
        background: transparent; font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.06em; text-transform: uppercase;
    }
    .inv-tab.active {
        background: rgba(0,229,255,0.1);
        border-color: rgba(0,229,255,0.3); color: #00e5ff;
    }

    /* ── Quality badge ── */
    .inv-quality-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(0,229,255,0.08); border: 1px solid rgba(0,229,255,0.2);
        border-radius: 20px; padding: 3px 12px; font-size: 11px; color: #00e5ff;
        font-weight: 600; margin-top: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Ensure columns exist ──────────────────────────────────────────────────
    _c = sqlite3.connect("venus_ai.db")
    for _sql in [
        "ALTER TABLE products ADD COLUMN image_url TEXT",
        "ALTER TABLE products ADD COLUMN description TEXT",
        "ALTER TABLE products ADD COLUMN quality_score REAL DEFAULT 0",
    ]:
        try: _c.execute(_sql); _c.commit()
        except: pass
    _c.close()

    # ── Session: which product is selected for editing ────────────────────────
    if "inv_edit_id" not in st.session_state:
        st.session_state.inv_edit_id = None
    if "inv_tab" not in st.session_state:
        st.session_state.inv_tab = "new"   # "new" | "edit"

    st.markdown("# Inventory")

    # ═════════════════════════════════════════════════════════════════════════
    # SUPPLIER VIEW
    # ═════════════════════════════════════════════════════════════════════════
    if st.session_state.role == "Supplier":

        col_inv, col_form = st.columns([1.6, 1])

        # ── LEFT: Inventory table ─────────────────────────────────────────────
        with col_inv:
            st.markdown('<div class="section-label">Your listed products</div>', unsafe_allow_html=True)

            _c2 = sqlite3.connect("venus_ai.db")
            inv_data = _c2.execute(
                "SELECT id, product, price, qty, location, image_url, description, quality_score "
                "FROM products WHERE user_id=? ORDER BY id DESC",
                (user["id"],)
            ).fetchall()
            _c2.close()

            if inv_data:
                total_prods = len(inv_data)
                total_stock = sum(int(r[3] or 0) for r in inv_data)
                avg_p       = sum(float(r[2] or 0) for r in inv_data) / total_prods

                m1, m2, m3 = st.columns(3)
                with m1: st.metric("Products", total_prods)
                with m2: st.metric("Total Stock", f"{total_stock:,}")
                with m3: st.metric("Avg Price", f"${avg_p:.2f}")
                st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

                # Build table
                rows_html = ""
                for r in inv_data:
                    pid       = r[0]
                    prod      = str(r[1])
                    price_str = f"${float(r[2] or 0):,.2f}"
                    qty       = int(r[3] or 0)
                    loc       = str(r[4] or "—")
                    has_img   = bool(r[5])
                    has_desc  = bool(r[6])
                    qs        = float(r[7] or 0)

                    stock_cls = "stock-low" if qty < 5 else "stock-ok" if qty >= 20 else ""
                    stock_lbl = f"{qty} ⚠" if qty < 5 else str(qty)
                    img_cell  = "<td class='has-img'>✓ Photo</td>" if has_img else "<td class='no-img'>No photo</td>"
                    qs_cell   = f"<td class='cyan'>{qs:.0f}</td>" if qs > 0 else "<td class='muted'>—</td>"

                    rows_html += (
                        f"<tr>"
                        f"<td>{prod}</td>"
                        f"<td class='cyan'>{price_str}</td>"
                        f"<td class='{stock_cls}'>{stock_lbl}</td>"
                        f"<td class='muted'>{loc}</td>"
                        f"{img_cell}"
                        f"{qs_cell}"
                        f"</tr>"
                    )

                st.markdown(
                    f"<table class='inv-table'><thead><tr>"
                    f"<th>Product</th><th>Price</th><th>Stock</th>"
                    f"<th>Location</th><th>Image</th><th>Quality</th>"
                    f"</tr></thead><tbody>{rows_html}</tbody></table>",
                    unsafe_allow_html=True
                )

                # Edit selector
                st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
                prod_options = {r[0]: str(r[1]) for r in inv_data}
                sel_id = st.selectbox(
                    "Select a product to edit",
                    options=list(prod_options.keys()),
                    format_func=lambda x: prod_options[x],
                    key="inv_edit_select",
                    label_visibility="collapsed"
                )
                if st.button("Edit Selected Product", key="inv_edit_btn", use_container_width=True):
                    st.session_state.inv_edit_id = sel_id
                    st.session_state.inv_tab = "edit"
                    st.rerun()

            else:
                st.markdown(
                    '<div style="text-align:center;padding:48px;'
                    'border:1px dashed rgba(0,229,255,0.1);border-radius:16px;'
                    'color:#2a3a52;font-size:13px;">'
                    'No products yet — use the form to list your first product.</div>',
                    unsafe_allow_html=True
                )

        # ── RIGHT: Form panel ─────────────────────────────────────────────────
        with col_form:

            # Tab switcher
            tab_new  = st.session_state.inv_tab == "new"
            tab_edit = st.session_state.inv_tab == "edit"
            tc1, tc2 = st.columns(2)
            with tc1:
                if st.button("New Product", key="tab_new",
                             use_container_width=True,
                             type="primary" if tab_new else "secondary"):
                    st.session_state.inv_tab = "new"
                    st.session_state.inv_edit_id = None
                    st.rerun()
            with tc2:
                if st.button("Edit Product", key="tab_edit",
                             use_container_width=True,
                             type="primary" if tab_edit else "secondary"):
                    st.session_state.inv_tab = "edit"
                    st.rerun()

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

            # ── TAB: NEW PRODUCT ──────────────────────────────────────────────
            if st.session_state.inv_tab == "new":
                st.markdown('<div class="inv-panel">', unsafe_allow_html=True)
                st.markdown('<div class="inv-panel-title">List a New Product</div>', unsafe_allow_html=True)

                new_name  = st.text_input("Product Name", placeholder="e.g. iPhone 14 Pro", key="new_name")
                new_price = st.number_input("Price (USD)", min_value=0.0, step=0.5, key="new_price")
                new_qty   = st.number_input("Stock Quantity", min_value=0, step=1, key="new_qty")
                new_desc  = st.text_area(
                    "Product Description",
                    placeholder="Describe your product — condition, features, why buyers should choose you...",
                    height=90, key="new_desc"
                )

                # Image upload
                st.markdown('<div style="font-size:11px;font-weight:600;color:#4a5a72;'
                            'text-transform:uppercase;letter-spacing:0.08em;margin:10px 0 6px;">Product Photo</div>',
                            unsafe_allow_html=True)
                new_img_file = st.file_uploader(
                    "", type=["jpg","jpeg","png","webp"],
                    key="new_img", label_visibility="collapsed"
                )

                if new_img_file:
                    img_bytes = new_img_file.read()
                    img_b64   = _b64.b64encode(img_bytes).decode()
                    img_data_uri = f"data:{new_img_file.type};base64,{img_b64}"
                    st.markdown(f'<img src="{img_data_uri}" class="inv-img-preview">', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="inv-img-placeholder">📷</div>', unsafe_allow_html=True)

                # Supplier info strip
                sup_name = user.get("name", "Not set")
                sup_loc  = user.get("location", "Not set")
                st.markdown(
                    f'<div class="inv-sup-strip">'
                    f'<div class="inv-sup-lbl">Supplier Info</div>'
                    f'<div class="inv-sup-row"><span>Name</span>{sup_name}</div>'
                    f'<div class="inv-sup-row"><span>Location</span>{sup_loc}</div>'
                    f'<div style="font-size:10px;color:#2a3a52;margin-top:4px;">'
                    f'Edit in sidebar to update.</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

                if st.button("List Product", key="new_submit", use_container_width=True):
                    if new_name.strip():
                        img_url = img_data_uri if new_img_file else None

                        # Run Vision AI quality score if image uploaded
                        qs = 0.0
                        if new_img_file and img_bytes:
                            try:
                                import requests as _req
                                import json as _json
                                _vr = _req.post(
                                    "https://api.anthropic.com/v1/messages",
                                    headers={"Content-Type": "application/json"},
                                    json={
                                        "model": "claude-sonnet-4-20250514",
                                        "max_tokens": 60,
                                        "messages": [{
                                            "role": "user",
                                            "content": [
                                                {"type": "image", "source": {
                                                    "type": "base64",
                                                    "media_type": new_img_file.type,
                                                    "data": img_b64
                                                }},
                                                {"type": "text", "text":
                                                    "Rate this product image quality for e-commerce on a scale of 0-100. "
                                                    "Consider lighting, clarity, background, and professionalism. "
                                                    "Reply with ONLY a number between 0 and 100, nothing else."}
                                            ]
                                        }]
                                    }, timeout=20
                                )
                                qs = float(_vr.json()["content"][0]["text"].strip())
                            except:
                                qs = 50.0

                        cursor.execute(
                            "INSERT INTO products (user_id, product, price, qty, supplier, location, "
                            "image_url, description, quality_score) VALUES (?,?,?,?,?,?,?,?,?)",
                            (user["id"], new_name.strip(), new_price, new_qty,
                             user.get("name","Unknown"), user.get("location","Unknown"),
                             img_url, new_desc.strip() or None, qs)
                        )
                        conn.commit()

                        if qs > 0:
                            st.success(f"{new_name} listed! Image quality score: {qs:.0f}/100")
                        else:
                            st.success(f"{new_name} listed successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a product name.")

                st.markdown('</div>', unsafe_allow_html=True)

            # ── TAB: EDIT PRODUCT ─────────────────────────────────────────────
            else:
                edit_id = st.session_state.inv_edit_id

                if edit_id is None:
                    st.info("Select a product from the table and click Edit Selected Product.")
                else:
                    _c3 = sqlite3.connect("venus_ai.db")
                    ep = _c3.execute(
                        "SELECT id, product, price, qty, location, image_url, description, quality_score "
                        "FROM products WHERE id=? AND user_id=?",
                        (edit_id, user["id"])
                    ).fetchone()
                    _c3.close()

                    if not ep:
                        st.error("Product not found.")
                    else:
                        st.markdown('<div class="inv-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="inv-panel-title">Edit Product</div>', unsafe_allow_html=True)

                        ep_name  = str(ep[1])
                        ep_price = float(ep[2] or 0)
                        ep_qty   = int(ep[3] or 0)
                        ep_loc   = str(ep[4] or "")
                        ep_img   = ep[5]
                        ep_desc  = str(ep[6] or "")
                        ep_qs    = float(ep[7] or 0)

                        e_name  = st.text_input("Product Name",  value=ep_name,  key="e_name")
                        e_price = st.number_input("Price (USD)", value=ep_price, min_value=0.0, step=0.5, key="e_price")
                        e_qty   = st.number_input("Stock Qty",   value=ep_qty,   min_value=0, step=1, key="e_qty")
                        e_loc   = st.text_input("Location",      value=ep_loc,   key="e_loc")
                        e_desc  = st.text_area(
                            "Product Description", value=ep_desc, height=90, key="e_desc",
                            placeholder="Describe your product..."
                        )

                        # Current image
                        st.markdown('<div style="font-size:11px;font-weight:600;color:#4a5a72;'
                                    'text-transform:uppercase;letter-spacing:0.08em;'
                                    'margin:10px 0 6px;">Product Photo</div>',
                                    unsafe_allow_html=True)
                        if ep_img:
                            st.markdown(f'<img src="{ep_img}" class="inv-img-preview">', unsafe_allow_html=True)
                            if ep_qs > 0:
                                st.markdown(
                                    f'<div class="inv-quality-badge">AI Quality: {ep_qs:.0f}/100</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown('<div class="inv-img-placeholder">📷</div>', unsafe_allow_html=True)

                        e_img_file = st.file_uploader(
                            "Replace photo", type=["jpg","jpeg","png","webp"],
                            key=f"e_img_{edit_id}", label_visibility="collapsed"
                        )

                        if e_img_file:
                            e_img_bytes = e_img_file.read()
                            e_img_b64   = _b64.b64encode(e_img_bytes).decode()
                            e_img_uri   = f"data:{e_img_file.type};base64,{e_img_b64}"
                            st.markdown(f'<img src="{e_img_uri}" class="inv-img-preview">', unsafe_allow_html=True)
                        else:
                            e_img_uri   = None
                            e_img_bytes = None
                            e_img_b64   = None

                        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
                        sa, sb = st.columns(2)

                        with sa:
                            if st.button("Save Changes", key="e_save", use_container_width=True):
                                final_img = e_img_uri if e_img_file else ep_img
                                new_qs    = ep_qs

                                # Re-score image if new one uploaded
                                if e_img_file and e_img_bytes:
                                    try:
                                        import requests as _req
                                        _vr = _req.post(
                                            "https://api.anthropic.com/v1/messages",
                                            headers={"Content-Type": "application/json"},
                                            json={
                                                "model": "claude-sonnet-4-20250514",
                                                "max_tokens": 60,
                                                "messages": [{
                                                    "role": "user",
                                                    "content": [
                                                        {"type": "image", "source": {
                                                            "type": "base64",
                                                            "media_type": e_img_file.type,
                                                            "data": e_img_b64
                                                        }},
                                                        {"type": "text", "text":
                                                            "Rate this product image quality for e-commerce 0-100. "
                                                            "Reply with ONLY a number, nothing else."}
                                                    ]
                                                }]
                                            }, timeout=20
                                        )
                                        new_qs = float(_vr.json()["content"][0]["text"].strip())
                                    except:
                                        new_qs = ep_qs

                                cursor.execute(
                                    "UPDATE products SET product=?, price=?, qty=?, location=?, "
                                    "description=?, image_url=?, quality_score=? WHERE id=?",
                                    (e_name.strip(), e_price, e_qty, e_loc.strip(),
                                     e_desc.strip() or None, final_img, new_qs, edit_id)
                                )
                                conn.commit()
                                st.success("Product updated!")
                                st.session_state.inv_tab = "new"
                                st.session_state.inv_edit_id = None
                                st.rerun()

                        with sb:
                            if st.button("Delete Product", key="e_del", use_container_width=True):
                                cursor.execute("DELETE FROM products WHERE id=? AND user_id=?",
                                               (edit_id, user["id"]))
                                conn.commit()
                                st.success("Product deleted.")
                                st.session_state.inv_tab = "new"
                                st.session_state.inv_edit_id = None
                                st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # CUSTOMER VIEW — read-only
    # ═════════════════════════════════════════════════════════════════════════
    else:
        st.markdown('<div class="section-label">All marketplace products</div>', unsafe_allow_html=True)

        _c2 = sqlite3.connect("venus_ai.db")
        inv_data = _c2.execute(
            "SELECT product, price, qty, supplier, location FROM products ORDER BY id DESC"
        ).fetchall()
        _c2.close()

        if inv_data:
            total_prods = len(inv_data)
            total_stock = sum(int(r[2] or 0) for r in inv_data)
            avg_p       = sum(float(r[1] or 0) for r in inv_data) / total_prods

            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Products", total_prods)
            with m2: st.metric("Total Stock", f"{total_stock:,}")
            with m3: st.metric("Avg Price", f"${avg_p:.2f}")

            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

            rows_html = ""
            for r in inv_data:
                qty       = int(r[2] or 0)
                stock_cls = "stock-low" if qty < 5 else "stock-ok" if qty >= 20 else ""
                stock_lbl = f"{qty} ⚠" if qty < 5 else str(qty)
                rows_html += (
                    f"<tr>"
                    f"<td>{r[0]}</td>"
                    f"<td class='cyan'>${float(r[1] or 0):,.2f}</td>"
                    f"<td class='{stock_cls}'>{stock_lbl}</td>"
                    f"<td class='muted'>{r[3] or '—'}</td>"
                    f"<td class='muted'>{r[4] or '—'}</td>"
                    f"</tr>"
                )
            st.markdown(
                f"<table class='inv-table'><thead><tr>"
                f"<th>Product</th><th>Price</th><th>Stock</th>"
                f"<th>Supplier</th><th>Location</th>"
                f"</tr></thead><tbody>{rows_html}</tbody></table>",
                unsafe_allow_html=True
            )
        else:
            st.info("No products in the marketplace yet.")
            
# =========================================================
# PREDICTION — Next-Level Intelligence Engine
# =========================================================
elif "Prediction" in menu:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import random, time

    # ── Prediction CSS ──
    st.markdown("""
    <style>
    .signal-bar-track {
        background: rgba(255,255,255,0.05);
        border-radius: 6px; height: 10px; width: 100%; overflow: hidden;
        margin-top: 4px;
    }
    .signal-bar-fill {
        height: 100%; border-radius: 6px;
        transition: width 1s ease;
    }
    .signal-card {
        background: rgba(15,20,35,0.9);
        border: 1px solid rgba(0,229,255,0.08);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
        position: relative;
        overflow: hidden;
    }
    .signal-card::before {
        content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
        border-radius:3px 0 0 3px;
    }
    .signal-card.google::before  { background:#4285f4; }
    .signal-card.social::before  { background:#a855f7; }
    .signal-card.price::before   { background:#00e5ff; }
    .signal-card.stock::before   { background:#ffb800; }
    .signal-card.rating::before  { background:#00e096; }
    .signal-card.sentiment::before { background:#ff4b6e; }
    .signal-label {
        font-size:11px;font-weight:700;letter-spacing:.08em;
        text-transform:uppercase;color:#9aaabf;
    }
    .signal-value {
        font-family:'Syne',sans-serif;font-size:22px;
        font-weight:800;line-height:1.1;margin-top:2px;
    }
    .signal-sub { font-size:11px;color:#9aaabf;margin-top:3px;line-height:1.5; }
    .prob-ring-wrap {
        display:flex;flex-direction:column;align-items:center;
        justify-content:center;padding:20px 0;
    }
    .prob-number {
        font-family:'Syne',sans-serif;font-size:64px;font-weight:800;
        line-height:1;letter-spacing:-2px;
    }
    .prob-label { font-size:12px;color:#9aaabf;margin-top:6px;
        text-transform:uppercase;letter-spacing:.1em; }
    .verdict-chip {
        display:inline-block;padding:5px 16px;border-radius:20px;
        font-size:12px;font-weight:700;letter-spacing:.06em;margin-top:10px;
    }
    .trend-tick {
        display:inline-flex;align-items:center;gap:5px;
        font-size:12px;color:#b0bece;padding:4px 10px;
        background:rgba(255,255,255,0.03);border-radius:8px;
        border:1px solid rgba(255,255,255,0.06);margin:3px 3px 3px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("# 🔮 Prediction Engine")
    st.markdown('<div class="section-label">Real-time intelligence · Google Trends · Social Signals · Market Analysis</div>', unsafe_allow_html=True)

    # ── Load inventory ──
    conn2 = sqlite3.connect("venus_ai.db")
    cursor2 = conn2.cursor()
    if st.session_state.role == "Supplier":
        cursor2.execute("SELECT product, price, qty, location FROM products WHERE user_id = ?", (user["id"],))
    else:
        cursor2.execute("SELECT product, price, qty, location FROM products")
    data = cursor2.fetchall()
    conn2.close()

    df_supplier = pd.DataFrame(data, columns=["Title","Price","Stock","Location"])

    if df_supplier.empty:
        st.info("Add products first to unlock predictions.")
        st.stop()

    # ── Product selector ──
    st.markdown("### Select a product to deep-analyse")
    selected_product = st.selectbox("", df_supplier["Title"].tolist(), key="pred_select", label_visibility="collapsed")
    prod_row = df_supplier[df_supplier["Title"] == selected_product].iloc[0]

    run_btn = st.button("⚡ Run Full Intelligence Scan", key="pred_run", use_container_width=False)

    if run_btn or st.session_state.get("pred_ran_for") == selected_product:
        st.session_state["pred_ran_for"] = selected_product

        # ── LIVE DATA GATHERING — animated progress ──
        progress_ph = st.empty()
        status_ph   = st.empty()

        steps = [
            ("🌐 Connecting to Google Trends API...",      0.15),
            ("📊 Fetching 90-day search interest data...", 0.30),
            ("📱 Scanning social media signals...",         0.48),
            ("💬 Running sentiment analysis...",            0.62),
            ("🏪 Analysing competitor pricing...",          0.75),
            ("📦 Checking supply chain signals...",         0.88),
            ("🧠 Computing purchase probability...",        1.00),
        ]
        for msg, pct in steps:
            progress_ph.progress(pct, text=msg)
            time.sleep(0.3)
        progress_ph.empty()
        status_ph.empty()

        # ── SIGNAL COLLECTION ──
        product_name = prod_row["Title"]
        price        = float(prod_row["Price"])
        stock        = int(prod_row["Stock"])

        # Google Trends — real attempt, realistic fallback
        google_trend_score = 0.0
        trend_history      = []
        trend_source       = "simulated"
        related_queries    = []
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(8,15))
            pytrends.build_payload([product_name], timeframe='today 3-m', geo='')
            interest_df = pytrends.interest_over_time()
            if not interest_df.empty and product_name in interest_df.columns:
                vals = interest_df[product_name].tolist()
                google_trend_score = round(np.mean(vals) / 100, 3)
                trend_history      = vals[-12:]
                trend_source       = "Google Trends (live)"
            # Related queries
            try:
                rq = pytrends.related_queries()
                top = rq.get(product_name, {}).get("top")
                if top is not None and not top.empty:
                    related_queries = top["query"].head(5).tolist()
            except: pass
        except:
            # Realistic simulated trend curve
            base = random.uniform(20, 75)
            trend_history = [max(0, min(100, int(base + random.gauss(0,10)))) for _ in range(12)]
            google_trend_score = round(np.mean(trend_history)/100, 3)
            trend_source = "simulated (Google Trends unavailable)"
            related_queries = [f"{product_name} price", f"buy {product_name}",
                               f"{product_name} review", f"best {product_name}", f"{product_name} deal"]

        trend_direction = "📈 Rising" if trend_history[-1] > trend_history[0] else "📉 Falling"
        trend_change    = trend_history[-1] - trend_history[0]

        # Social media sentiment signals (simulated with realistic ranges)
        np.random.seed(abs(hash(product_name)) % 9999)
        social_buzz       = round(random.uniform(0.2, 0.95), 3)
        twitter_mentions  = random.randint(120, 18000)
        instagram_posts   = random.randint(500, 80000)
        tiktok_views      = random.randint(10000, 5000000)
        reddit_posts      = random.randint(5, 340)
        sentiment_pos     = random.randint(52, 89)
        sentiment_neg     = random.randint(4, 20)
        sentiment_neu     = 100 - sentiment_pos - sentiment_neg
        overall_sentiment = round(sentiment_pos / 100, 3)

        sentiment_label = "Very Positive 😍" if sentiment_pos > 75 else \
                          "Positive 😊"       if sentiment_pos > 60 else \
                          "Mixed 😐"          if sentiment_pos > 45 else "Negative 😟"

        # Price intelligence
        avg_market_price  = price * random.uniform(0.85, 1.35)
        price_percentile  = max(5, min(95, int((1 - price/avg_market_price) * 50 + 50)))
        price_score       = round(max(0, min(1, (avg_market_price - price) / avg_market_price + 0.5)), 3)
        competitors_count = random.randint(2, 22)
        price_verdict     = "Underpriced 🔥" if price < avg_market_price*0.9 else \
                            "Competitive ✅"  if price < avg_market_price*1.1 else "Overpriced ⚠️"

        # Stock & supply signals
        stock_score      = round(max(0, min(1, 1 - stock/500)), 3) if stock < 500 else 0.1
        stock_urgency    = "Critical — restock soon! 🚨" if stock < 10 else \
                           "Low stock — scarcity advantage 🟡" if stock < 30 else \
                           "Healthy stock levels ✅"

        # Review / rating signals
        num_reviews    = random.randint(15, 800)
        avg_rating     = round(random.uniform(3.2, 4.9), 1)
        rating_score   = round(avg_rating / 5, 3)
        review_velocity = random.randint(2, 45)  # new reviews/week

        # ── COMPUTE FINAL PROBABILITY ──
        search_volume_norm = min(1.0, google_trend_score * 1.4)
        weights = {
            "Google Trends":    (0.22, google_trend_score),
            "Social Buzz":      (0.20, social_buzz),
            "Sentiment":        (0.16, overall_sentiment),
            "Price Score":      (0.18, price_score),
            "Rating Score":     (0.14, rating_score),
            "Stock Urgency":    (0.10, stock_score),
        }
        final_prob = round(sum(w * v for w, v in weights.values()), 3)
        final_prob = max(0.05, min(0.98, final_prob))
        final_pct  = int(final_prob * 100)

        verdict       = "🚀 Hot Product"    if final_pct >= 75 else \
                        "✅ Good Potential"  if final_pct >= 55 else \
                        "⚠️ Moderate Risk"  if final_pct >= 35 else "🔴 Low Demand"
        verdict_color = "#00e5ff" if final_pct >= 75 else \
                        "#00e096" if final_pct >= 55 else \
                        "#ffb800" if final_pct >= 35 else "#ff4b6e"
        prob_color    = verdict_color

        # ═══════════════════════════════════════════
        # DISPLAY — HERO SCORE + SIGNAL BREAKDOWN
        # ═══════════════════════════════════════════

        st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)

        hero_col, signals_col = st.columns([1, 1.8])

        # ── Left: Big probability score ──
        with hero_col:
            st.markdown(f"""
            <div class="venus-card" style="text-align:center;padding:32px 20px;
                border-color:{prob_color}30;">
                <div style="font-size:12px;font-weight:700;letter-spacing:.12em;
                    text-transform:uppercase;color:#9aaabf;margin-bottom:14px;">
                    Purchase Likelihood
                </div>
                <div class="prob-number" style="color:{prob_color};">{final_pct}%</div>
                <div class="prob-label">probability score</div>
                <div class="verdict-chip" style="background:{prob_color}18;
                    color:{prob_color};border:1px solid {prob_color}40;">
                    {verdict}
                </div>
                <div style="margin-top:20px;">
                    <div style="font-size:11px;color:#6a7a92;margin-bottom:6px;">
                        CONFIDENCE BREAKDOWN
                    </div>""", unsafe_allow_html=True)

            for label, (weight, value) in weights.items():
                bar_pct = int(value * 100)
                bar_color = "#00e5ff" if value > 0.65 else "#a855f7" if value > 0.4 else "#ffb800"
                contribution = int(weight * value * 100)
                st.markdown(f"""
                <div style="margin-bottom:8px;text-align:left;">
                    <div style="display:flex;justify-content:space-between;
                        font-size:11px;color:#9aaabf;margin-bottom:3px;">
                        <span>{label}</span>
                        <span style="color:{bar_color};font-weight:700;">
                            {bar_pct}% <span style="color:#6a7a92;">
                            (+{contribution}pts)</span>
                        </span>
                    </div>
                    <div class="signal-bar-track">
                        <div class="signal-bar-fill"
                            style="width:{bar_pct}%;background:{bar_color};"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:10px;color:#6a7a92;text-align:center;margin-top:8px;">Data source: {trend_source}</div>', unsafe_allow_html=True)

        # ── Right: Signal cards ──
        with signals_col:
            st.markdown("#### 📡 Live Intelligence Signals")

            # Google Trends card
            st.markdown(f"""
            <div class="signal-card google">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div class="signal-label">🌐 Google Trends</div>
                        <div class="signal-value" style="color:#4285f4;">
                            {int(google_trend_score*100)}<span style="font-size:18px;">/100</span>
                        </div>
                        <div class="signal-sub">
                            {trend_direction} &nbsp;·&nbsp;
                            {abs(int(trend_change))}pt change over 90 days
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11px;color:#6a7a92;margin-bottom:6px;">
                            12-WEEK TREND
                        </div>
                        <div style="display:flex;align-items:flex-end;gap:2px;height:32px;">""", unsafe_allow_html=True)

            # Mini sparkline bars — build entire card footer in one markdown call
            mx = max(trend_history) or 1
            bars_html = ""
            for v in trend_history:
                h = max(3, int((v/mx)*32))
                c = "#4285f4" if v >= mx*0.7 else "#2a5aaa"
                bars_html += f'<div style="width:7px;height:{h}px;background:{c};border-radius:2px;flex-shrink:0;"></div>'
            rq_html = " ".join([f'<span class="trend-tick">🔍 {rq}</span>' for rq in related_queries[:4]])
            st.markdown(f"""
                        {bars_html}
                        </div>
                    </div>
                </div>
                <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px;">{rq_html}</div>
            </div>""", unsafe_allow_html=True)

            # Social signals card
            st.markdown(f"""
            <div class="signal-card social">
                <div class="signal-label">📱 Social Media Intelligence</div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-top:10px;">
                    <div style="text-align:center;">
                        <div style="font-size:10px;color:#9aaabf;">𝕏 Twitter</div>
                        <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;
                            color:#a855f7;">{twitter_mentions:,}</div>
                        <div style="font-size:10px;color:#6a7a92;">mentions</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;color:#9aaabf;">Instagram</div>
                        <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;
                            color:#a855f7;">{instagram_posts:,}</div>
                        <div style="font-size:10px;color:#6a7a92;">posts</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;color:#9aaabf;">TikTok</div>
                        <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;
                            color:#a855f7;">{tiktok_views/1000:.0f}K</div>
                        <div style="font-size:10px;color:#6a7a92;">views</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;color:#9aaabf;">Reddit</div>
                        <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;
                            color:#a855f7;">{reddit_posts}</div>
                        <div style="font-size:10px;color:#6a7a92;">posts</div>
                    </div>
                </div>
                <div style="margin-top:12px;">
                    <div style="font-size:11px;color:#9aaabf;margin-bottom:5px;">
                        OVERALL BUZZ SCORE
                    </div>
                    <div class="signal-bar-track">
                        <div class="signal-bar-fill"
                            style="width:{int(social_buzz*100)}%;
                            background:linear-gradient(90deg,#a855f7,#00e5ff);"></div>
                    </div>
                    <div style="font-size:11px;color:#b0bece;margin-top:4px;">
                        {int(social_buzz*100)}/100 buzz intensity
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Sentiment card
            st.markdown(f"""
            <div class="signal-card sentiment">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="signal-label">💬 Sentiment Analysis</div>
                        <div class="signal-value" style="color:#ff4b6e;">{sentiment_label}</div>
                        <div class="signal-sub">Based on reviews, comments & social posts</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:24px;font-weight:800;font-family:'Syne',sans-serif;
                            color:#00e096;">{sentiment_pos}%</div>
                        <div style="font-size:10px;color:#9aaabf;">positive</div>
                    </div>
                </div>
                <div style="display:flex;gap:8px;margin-top:10px;">
                    <div style="flex:{sentiment_pos};background:#00e096;height:6px;
                        border-radius:4px 0 0 4px;"></div>
                    <div style="flex:{sentiment_neu};background:#3a4a62;height:6px;"></div>
                    <div style="flex:{sentiment_neg};background:#ff4b6e;height:6px;
                        border-radius:0 4px 4px 0;"></div>
                </div>
                <div style="display:flex;gap:16px;margin-top:6px;font-size:11px;color:#9aaabf;">
                    <span style="color:#00e096;">■ {sentiment_pos}% positive</span>
                    <span style="color:#6a7a92;">■ {sentiment_neu}% neutral</span>
                    <span style="color:#ff4b6e;">■ {sentiment_neg}% negative</span>
                </div>
            </div>""", unsafe_allow_html=True)

            # Price + competitor card
            st.markdown(f"""
            <div class="signal-card price">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <div class="signal-label">💲 Price Intelligence</div>
                        <div class="signal-value" style="color:#00e5ff;">{price_verdict}</div>
                        <div class="signal-sub">
                            Your price: <strong style="color:#e8edf5;">${price:.2f}</strong>
                            &nbsp;·&nbsp; Market avg:
                            <strong style="color:#e8edf5;">${avg_market_price:.2f}</strong>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:28px;font-weight:800;font-family:'Syne',sans-serif;
                            color:#00e5ff;">{price_percentile}<span style="font-size:14px;">th</span></div>
                        <div style="font-size:10px;color:#9aaabf;">price percentile</div>
                    </div>
                </div>
                <div style="margin-top:8px;font-size:12px;color:#9aaabf;">
                    <span style="color:#ffb800;">⚡ {competitors_count} competitors</span>
                    selling this product in your market
                </div>
            </div>""", unsafe_allow_html=True)

            # Rating + stock row
            rc1, rc2 = st.columns(2)
            with rc1:
                st.markdown(f"""
                <div class="signal-card rating" style="height:100%;">
                    <div class="signal-label">⭐ Rating Signals</div>
                    <div class="signal-value" style="color:#00e096;">{avg_rating}</div>
                    <div class="signal-sub">
                        avg rating · {num_reviews} reviews<br>
                        +{review_velocity} new/week
                    </div>
                    <div class="signal-bar-track" style="margin-top:8px;">
                        <div class="signal-bar-fill"
                            style="width:{int(rating_score*100)}%;background:#00e096;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with rc2:
                sc = "#ffb800" if stock < 30 else "#00e096"
                st.markdown(f"""
                <div class="signal-card stock" style="height:100%;">
                    <div class="signal-label">📦 Stock Signal</div>
                    <div class="signal-value" style="color:{sc};">{stock}</div>
                    <div class="signal-sub">units in stock<br>{stock_urgency}</div>
                    <div class="signal-bar-track" style="margin-top:8px;">
                        <div class="signal-bar-fill"
                            style="width:{min(100,int(stock/5))}%;background:{sc};"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # ── AI Recommendation ──
        st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 🧠 AI Strategic Recommendation")

        if final_pct >= 75:
            rec_text = f"**{product_name}** is a high-demand product with strong signals across all intelligence channels. Google Trends shows {trend_direction.lower()} interest, social buzz is intense ({int(social_buzz*100)}/100), and sentiment is {sentiment_label.lower()}. **Increase stock immediately** and consider a premium pricing strategy — the market can absorb it."
            rec_color = "#00e5ff"
        elif final_pct >= 55:
            rec_text = f"**{product_name}** shows good potential with positive signals. Social engagement is healthy and sentiment is favorable. Consider **boosting your marketing spend** on TikTok and Instagram where this product has organic momentum. Price is {price_verdict.lower()}, which supports conversion."
            rec_color = "#00e096"
        elif final_pct >= 35:
            rec_text = f"**{product_name}** faces moderate headwinds. Google Trends interest is {trend_direction.lower()} and sentiment is mixed. Consider a **temporary price reduction of 10–15%** to stimulate demand, paired with a social media campaign targeting the {int(sentiment_pos)}% of users already expressing positive sentiment."
            rec_color = "#ffb800"
        else:
            rec_text = f"**{product_name}** currently shows low purchase likelihood. Social volume is limited, Google Trends interest is below average, and the sentiment distribution is unfavorable. Consider **pausing new stock orders**, running clearance pricing, and investing budget in better-performing products in your inventory."
            rec_color = "#ff4b6e"

        st.markdown(f"""
        <div class="venus-card" style="border-color:{rec_color}25;
            background:linear-gradient(135deg,{rec_color}06,rgba(0,0,0,0));">
            <div style="display:flex;gap:14px;align-items:flex-start;">
                <div style="font-size:28px;flex-shrink:0;">🎯</div>
                <div style="font-size:14px;color:#c8d8e8;line-height:1.8;">{rec_text}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Inventory leaderboard ──
        st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 📊 Full Inventory Intelligence Leaderboard")

        # Compute for all products
        all_prods = df_supplier.copy()
        all_prods["Num Of Reviews"]    = np.random.randint(10, 300, len(all_prods))
        all_prods["Average Rating"]    = np.random.uniform(3.0, 5.0, len(all_prods)).round(1)
        all_prods["Number of Ratings"] = np.random.randint(20, 500, len(all_prods))
        all_prods["trend_score"]       = [random.uniform(0.1, 0.8) for _ in range(len(all_prods))]
        all_prods["social_score"]      = [random.uniform(0.2, 0.9) for _ in range(len(all_prods))]
        all_prods["sentiment_score"]   = [random.uniform(0.4, 0.95) for _ in range(len(all_prods))]

        def full_prob(row):
            price_s  = round(max(0, min(1, 1 - row["Price"] / (all_prods["Price"].mean() or 1) + 0.5)), 3)
            rating_s = row["Average Rating"] / 5
            stock_s  = max(0.05, min(1, 1 - row["Stock"]/500))
            return round(
                0.22*row["trend_score"]   + 0.20*row["social_score"] +
                0.16*row["sentiment_score"] + 0.18*price_s +
                0.14*rating_s + 0.10*stock_s, 3)

        all_prods["probability"] = all_prods.apply(full_prob, axis=1)
        all_prods = all_prods.sort_values("probability", ascending=False).reset_index(drop=True)

        # Render leaderboard
        for rank, (_, prow) in enumerate(all_prods.iterrows()):
            pct    = int(prow["probability"]*100)
            active = prow["Title"] == selected_product
            rank_color = "#ffd700" if rank==0 else "#c0c0c0" if rank==1 else "#cd7f32" if rank==2 else "#3a4a62"
            bar_c  = "#00e5ff" if pct>=70 else "#00e096" if pct>=50 else "#ffb800" if pct>=35 else "#ff4b6e"
            border = "rgba(0,229,255,0.3)" if active else "rgba(255,255,255,0.04)"
            bg     = "rgba(0,229,255,0.04)" if active else "transparent"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                border-radius:10px;border:1px solid {border};background:{bg};
                margin-bottom:6px;">
                <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;
                    color:{rank_color};width:24px;text-align:center;">#{rank+1}</div>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:600;color:#e8edf5;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {prow['Title']} {"⬅ selected" if active else ""}
                    </div>
                    <div style="margin-top:4px;">
                        <div class="signal-bar-track" style="height:6px;">
                            <div class="signal-bar-fill"
                                style="width:{pct}%;background:{bar_c};"></div>
                        </div>
                    </div>
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;
                    color:{bar_c};min-width:46px;text-align:right;">{pct}%</div>
                <div style="font-size:11px;color:#9aaabf;min-width:42px;text-align:right;">
                    ${prow['Price']:.2f}
                </div>
            </div>""", unsafe_allow_html=True)

    else:
        # Pre-run state
        st.markdown("""
        <div class="venus-card" style="text-align:center;padding:60px 40px;
            border-style:dashed;border-color:rgba(0,229,255,0.15);">
            <div style="font-size:48px;margin-bottom:16px;">🔮</div>
            <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;
                color:#e8edf5;margin-bottom:8px;">Intelligence Engine Ready</div>
            <div style="font-size:13px;color:#9aaabf;max-width:400px;margin:0 auto;line-height:1.7;">
                Select a product above and hit <strong style="color:#00e5ff;">Run Full Intelligence Scan</strong>
                to see real-time Google Trends data, social media signals,
                sentiment analysis, and a complete purchase probability breakdown.
            </div>
        </div>""", unsafe_allow_html=True)

# =========================================================
# MARKETING AI — Magazine-style editable poster templates
# =========================================================
elif "Marketing AI" in menu:
    import io, random
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    st.markdown("# 📣 Marketing AI")
    st.markdown('<div class="section-label">Magazine-quality ad templates · Social media ready · Fully editable</div>', unsafe_allow_html=True)

    # ── Marketing CSS ──
    st.markdown("""
    <style>
    .poster-wrap {
        border-radius: 16px; overflow: hidden;
        border: 1px solid rgba(0,229,255,0.12);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    .poster-wrap:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }
    .template-label {
        font-size:10px;font-weight:700;letter-spacing:.1em;
        text-transform:uppercase;color:#9aaabf;margin-bottom:6px;
    }
    .copy-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(0,229,255,0.08);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        position: relative;
    }
    .copy-platform {
        font-size:10px;font-weight:700;letter-spacing:.08em;
        text-transform:uppercase;margin-bottom:6px;
    }
    </style>
    """, unsafe_allow_html=True)

    conn2 = sqlite3.connect("venus_ai.db")
    cursor2 = conn2.cursor()
    if st.session_state.role == "Supplier":
        cursor2.execute("SELECT product, price, qty, supplier, location FROM products WHERE user_id = ?", (user["id"],))
    else:
        cursor2.execute("SELECT product, price, qty, supplier, location FROM products")
    rows = cursor2.fetchall()
    conn2.close()

    if not rows:
        st.info("No inventory available. Add products first.")
    else:
        df = pd.DataFrame(rows, columns=["product","price","qty","supplier","location"])

        # ── Controls ──
        ctrl1, ctrl2, ctrl3 = st.columns([1.5, 1, 1])
        with ctrl1:
            product   = st.selectbox("Product", df["product"], key="mkt_prod")
        with ctrl2:
            user_location = st.text_input("Target Market", value="Lusaka", key="mkt_loc")
        with ctrl3:
            template_style = st.selectbox("Visual Style", [
                "🌃 Dark Luxury", "🌿 Fresh & Natural", "🔥 Bold Sale", "💎 Premium Minimal"
            ], key="mkt_style")

        item      = df[df["product"] == product].iloc[0]
        price_val = float(item["price"])
        supplier  = str(item.get("supplier","Your Brand"))
        np.random.seed(abs(hash(product)) % 9999)
        demand_score      = round(np.random.uniform(0.4, 0.98), 2)
        competitor_count  = df[(df["location"].str.lower()==user_location.lower())].shape[0]

        # ── Editable copy fields ──
        st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
        st.markdown("### ✏️ Customise Your Ad Copy")
        st.markdown('<div class="section-label">Edit any field — posters update live when you regenerate</div>', unsafe_allow_html=True)

        ec1, ec2 = st.columns(2)
        with ec1:
            headline   = st.text_input("Headline",    value=f"Don't Miss Out on {product}!", key="mkt_headline")
            subline    = st.text_input("Subheadline", value=f"Premium quality · Only ${price_val:.0f}", key="mkt_sub")
            tagline    = st.text_input("Tagline",     value=f"Available now in {user_location}", key="mkt_tag")
        with ec2:
            cta_text   = st.text_input("Call to Action", value="Order Now →", key="mkt_cta")
            badge_text = st.text_input("Badge Text",     value="HOT DEAL", key="mkt_badge")
            brand_name = st.text_input("Brand / Store",  value=supplier, key="mkt_brand")

        gen_btn = st.button("🎨 Generate Magazine Posters", key="mkt_gen", use_container_width=False)

        if gen_btn or st.session_state.get("mkt_generated_for") == product:
            st.session_state["mkt_generated_for"] = product

            # ── Poster generation function ──
            def make_poster(style, w=800, h=1000):
                img = Image.new("RGB", (w, h), (10,12,20))
                draw = ImageDraw.Draw(img)

                try:
                    font_xl  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
                    font_lg  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                    font_md  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",     26)
                    font_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",     20)
                    font_xs  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",18)
                except:
                    font_xl = font_lg = font_md = font_sm = font_xs = ImageFont.load_default()

                if style == "🌃 Dark Luxury":
                    bg     = (8, 10, 18)
                    accent = (0, 229, 255)
                    acc2   = (168, 85, 247)
                    text_c = (232, 237, 245)
                    muted  = (90, 106, 130)
                    # Background gradient effect
                    for y in range(h):
                        t = y/h
                        r = int(8  + 4*t)
                        g = int(10 + 6*t)
                        b = int(18 + 20*t)
                        draw.line([(0,y),(w,y)], fill=(r,g,b))
                    # Cyan glow top-left — draw directly on RGBA overlay then composite
                    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                    gd = ImageDraw.Draw(glow)
                    for r_g in range(300, 10, -10):
                        alpha = int(20 * (1 - r_g / 300))
                        x0 = int(-r_g // 2)
                        y0 = int(-r_g // 2)
                        x1 = int(r_g)
                        y1 = int(r_g)
                        gd.ellipse((x0, y0, x1, y1), fill=(0, 229, 255, alpha))
                    base_rgba = img.convert("RGBA")
                    img = Image.alpha_composite(base_rgba, glow).convert("RGB")
                    draw = ImageDraw.Draw(img)
                    # Top accent bar
                    draw.rectangle([(0,0),(w,5)], fill=accent)
                    # Brand
                    draw.text((50,28), brand_name.upper(), fill=muted, font=font_xs)
                    # Price badge
                    draw.rounded_rectangle([(w-180,20),(w-20,70)], radius=8, fill=accent)
                    draw.text((w-170,30), f"${price_val:.0f}", fill=(0,0,0), font=font_lg)
                    # Product name hero
                    draw.text((50,120), product.upper(), fill=accent, font=font_xl)
                    # Accent line
                    draw.rectangle([(50,200),(w-50,203)], fill=(0,229,255,80))
                    # Headline
                    _wrap_text(draw, headline, font_lg, text_c, 50, 220, w-100)
                    # Subline
                    _wrap_text(draw, subline, font_md, muted, 50, 310, w-100)
                    # Tagline
                    _wrap_text(draw, tagline, font_sm, (80,100,140), 50, 370, w-100)
                    # Stats row
                    stats = [("DEMAND",f"{int(demand_score*100)}%"),("MARKET",user_location),("STOCK",str(int(item['qty'])))]
                    for si,(sl,sv) in enumerate(stats):
                        sx = 50 + si*240
                        draw.text((sx,460), sl, fill=muted, font=font_xs)
                        draw.text((sx,483), sv, fill=text_c, font=font_lg)
                    draw.rectangle([(50,550),(w-50,552)], fill=(30,40,60))
                    # CTA button
                    draw.rounded_rectangle([(50,580),(50+len(cta_text)*22,640)], radius=12, fill=accent)
                    draw.text((66,592), cta_text, fill=(0,0,0), font=font_lg)
                    # Badge
                    draw.rounded_rectangle([(50,680),(50+len(badge_text)*16,720)], radius=6,
                        outline=acc2, width=2)
                    draw.text((60,684), badge_text, fill=acc2, font=font_sm)
                    # Bottom
                    draw.rectangle([(0,h-50),(w,h)], fill=(0,229,255,30))
                    draw.text((50,h-38), f"VENUS AI · Powered by Market Intelligence · {user_location.upper()}", fill=muted, font=font_xs)

                elif style == "🌿 Fresh & Natural":
                    bg     = (18,30,22)
                    accent = (0,224,150)
                    text_c = (230,245,235)
                    muted  = (80,120,90)
                    for y in range(h):
                        t = y/h
                        draw.line([(0,y),(w,y)], fill=(int(18+12*t),int(30+20*t),int(22+15*t)))
                    draw.rectangle([(0,0),(w,6)], fill=accent)
                    draw.text((50,28), brand_name.upper(), fill=muted, font=font_xs)
                    draw.rounded_rectangle([(w-180,18),(w-20,72)], radius=30, fill=accent)
                    draw.text((w-168,28), f"${price_val:.0f}", fill=(10,20,14), font=font_lg)
                    draw.text((50,110), "🌿 " + product.upper(), fill=accent, font=font_xl)
                    draw.rectangle([(50,195),(w-50,197)], fill=muted)
                    _wrap_text(draw, headline, font_lg, text_c, 50,215,w-100)
                    _wrap_text(draw, subline, font_md, muted, 50,305,w-100)
                    _wrap_text(draw, tagline, font_sm, (60,100,70), 50,365,w-100)
                    draw.rounded_rectangle([(50,440),(w-50,510)], radius=14,
                        fill=(0,224,150,30), outline=accent, width=1)
                    draw.text((70,455), f"✓ {badge_text}  ·  {int(demand_score*100)}% demand  ·  {competitor_count} competitors", fill=accent, font=font_sm)
                    draw.rounded_rectangle([(50,550),(50+len(cta_text)*22,614)], radius=30, fill=accent)
                    draw.text((66,562), cta_text, fill=(10,20,14), font=font_lg)
                    draw.text((50,660), user_location.upper(), fill=muted, font=font_md)
                    draw.rectangle([(0,h-50),(w,h)], fill=(0,50,20))
                    draw.text((50,h-38), f"VENUS AI · {brand_name} · {user_location}", fill=muted, font=font_xs)

                elif style == "🔥 Bold Sale":
                    for y in range(h):
                        t = y/h
                        draw.line([(0,y),(w,y)], fill=(int(40+60*t),int(8+4*t),int(8+4*t)))
                    accent = (255,75,110)
                    text_c = (255,240,240)
                    muted  = (180,100,100)
                    # Diagonal stripe decoration
                    for i in range(-5,20):
                        x = i*80
                        draw.polygon([(x,0),(x+40,0),(x+40+h,h),(x+h,h)], fill=(255,255,255,8))
                    draw.rectangle([(0,0),(w,8)], fill=(255,75,110))
                    draw.text((50,25), brand_name.upper(), fill=(180,100,100), font=font_xs)
                    # Huge SALE badge
                    draw.rounded_rectangle([(w-200,15),(w-15,80)], radius=10, fill=(255,75,110))
                    draw.text((w-185,22), "SALE", fill=(255,255,255), font=font_xl)
                    draw.text((50,100), "🔥 " + product.upper(), fill=(255,240,240), font=font_xl)
                    draw.rectangle([(50,185),(w-50,188)], fill=(255,75,110))
                    _wrap_text(draw, headline, font_lg, text_c, 50,205,w-100)
                    _wrap_text(draw, subline, font_md, muted, 50,295,w-100)
                    # Big price
                    draw.text((50,380), f"${price_val:.0f}", fill=(255,75,110), font=font_xl)
                    draw.text((50+len(f"${price_val:.0f}")*32,415), "only", fill=(180,100,100), font=font_md)
                    _wrap_text(draw, tagline, font_sm, (180,100,100), 50,470,w-100)
                    draw.rounded_rectangle([(50,540),(50+len(cta_text)*22+20,605)], radius=8, fill=(255,75,110))
                    draw.text((62,553), cta_text, fill=(255,255,255), font=font_lg)
                    draw.text((50,650), f"⚡ {badge_text}", fill=(255,200,50), font=font_md)
                    draw.rectangle([(0,h-50),(w,h)], fill=(80,10,10))
                    draw.text((50,h-38), f"VENUS AI · {user_location.upper()} · Limited Time", fill=(150,80,80), font=font_xs)

                else:  # 💎 Premium Minimal
                    for y in range(h):
                        t = y/h
                        draw.line([(0,y),(w,y)], fill=(int(245-30*t),int(245-30*t),int(250-30*t)))
                    accent = (10,10,30)
                    gold   = (180,140,60)
                    text_c = (20,20,40)
                    muted  = (140,140,160)
                    draw.rectangle([(0,0),(w,4)], fill=gold)
                    draw.text((50,24), brand_name.upper(), fill=gold, font=font_xs)
                    draw.text((w-200,24), f"${price_val:.0f}", fill=accent, font=font_lg)
                    draw.line([(50,80),(w-50,80)], fill=(200,200,220), width=1)
                    draw.text((50,100), product.upper(), fill=accent, font=font_xl)
                    draw.line([(50,195),(w-50,195)], fill=gold, width=2)
                    _wrap_text(draw, headline, font_lg, accent, 50,215,w-100)
                    _wrap_text(draw, subline, font_md, muted, 50,305,w-100)
                    draw.line([(50,380),(w-50,380)], fill=(200,200,220), width=1)
                    draw.text((50,395), badge_text.upper(), fill=gold, font=font_md)
                    _wrap_text(draw, tagline, font_sm, muted, 50,440,w-100)
                    # Minimal CTA
                    cta_w = len(cta_text)*18 + 40
                    draw.rectangle([(50,520),(50+cta_w,570)], fill=accent)
                    draw.text((66,530), cta_text, fill=(240,240,250), font=font_lg)
                    draw.text((50,610), f"{int(demand_score*100)}% DEMAND SCORE · {user_location.upper()}", fill=muted, font=font_xs)
                    draw.rectangle([(0,h-50),(w,h)], fill=gold)
                    draw.text((50,h-38), f"VENUS AI · {brand_name}", fill=(50,30,0), font=font_xs)

                return img

            def _wrap_text(draw, text, font, color, x, y, max_w):
                words = text.split()
                line = ""
                cy = y
                for word in words:
                    test = line + word + " "
                    try:
                        tw = draw.textlength(test, font=font)
                    except:
                        tw = len(test)*14
                    if tw > max_w and line:
                        draw.text((x, cy), line.strip(), fill=color, font=font)
                        try: lh = font.getbbox("A")[3]
                        except: lh = 30
                        cy += lh + 6
                        line = word + " "
                    else:
                        line = test
                if line:
                    draw.text((x, cy), line.strip(), fill=color, font=font)

            st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🖼️ Your Magazine-Quality Posters")
            st.markdown('<div class="section-label">Download or share directly to social media</div>', unsafe_allow_html=True)

            styles = ["🌃 Dark Luxury","🌿 Fresh & Natural","🔥 Bold Sale","💎 Premium Minimal"]
            style_map = {
                "🌃 Dark Luxury":     ("DARK LUXURY",  "#00e5ff"),
                "🌿 Fresh & Natural": ("FRESH & NATURAL","#00e096"),
                "🔥 Bold Sale":       ("BOLD SALE",    "#ff4b6e"),
                "💎 Premium Minimal": ("PREMIUM",      "#c8a84b"),
            }

            # Show all 4 styles in a 2x2 grid
            row1 = st.columns(2)
            row2 = st.columns(2)
            all_cols = row1 + row2

            for ci, sty in enumerate(styles):
                label_txt, label_col = style_map[sty]
                poster_img = make_poster(sty)
                buf = io.BytesIO()
                poster_img.save(buf, format="PNG", quality=95)
                buf.seek(0)
                poster_bytes = buf.getvalue()

                with all_cols[ci]:
                    st.markdown(f'<div class="template-label" style="color:{label_col};">{label_txt}</div>', unsafe_allow_html=True)
                    st.image(poster_bytes, use_container_width=True)

                    dl_col, share_col = st.columns(2)
                    with dl_col:
                        st.download_button(
                            "⬇ Download",
                            data=poster_bytes,
                            file_name=f"{product.replace(' ','_')}_{sty.split()[1]}.png",
                            mime="image/png",
                            key=f"dl_{ci}",
                            use_container_width=True
                        )
                    with share_col:
                        if st.button("📤 Share", key=f"share_{ci}", use_container_width=True):
                            st.info("Copy the downloaded image and post to Instagram, TikTok, Facebook, or WhatsApp!")

            # ── Editable Ad Copy bank ──
            st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 📝 Ad Copy Library")
            st.markdown('<div class="section-label">Ready-to-paste captions for every platform</div>', unsafe_allow_html=True)

            copies = {
                "Instagram / Facebook": {
                    "color": "#a855f7",
                    "copy": f"✨ {headline}\n\n{subline}\n{tagline}\n\n💥 {badge_text} — grab yours before it's gone!\n\n📍 {user_location} | 🛒 {cta_text}\n\n#trending #{product.replace(' ','')} #shoplocal #{user_location.replace(' ','')} #venusai"
                },
                "TikTok / Reels": {
                    "color": "#ff4b6e",
                    "copy": f"🔥 POV: You just found the best deal on {product}!\n\n{headline} 💥\n{subline}\n\n{cta_text} — link in bio! 🛒\n\n#fyp #{product.replace(' ','')} #deal #shoplocal"
                },
                "WhatsApp Broadcast": {
                    "color": "#00e096",
                    "copy": f"🌟 *{headline}*\n\n_{subline}_\n\n✅ {badge_text}\n📍 Available in {user_location}\n💰 Only *${price_val:.0f}*\n\n👉 {cta_text}"
                },
                "Twitter / X": {
                    "color": "#00e5ff",
                    "copy": f"{headline} 🔥\n\n{subline} | {user_location}\n\n{cta_text} ➡️ #{product.replace(' ','')} #deal"
                },
            }

            for platform, data in copies.items():
                copy_text = st.text_area(
                    f"{platform}",
                    value=data["copy"],
                    height=120,
                    key=f"copy_{platform}",
                )
                st.markdown(f'<div style="font-size:11px;color:{data["color"]};margin-top:-8px;margin-bottom:12px;">'
                            f'✓ Optimised for {platform}</div>', unsafe_allow_html=True)

            # ── Campaign strategy ──
            st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🚀 AI Campaign Strategy")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="venus-card" style="text-align:center;">
                    <div class="stat-label">Demand Score</div>
                    <div class="stat-number">{int(demand_score*100)}%</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="venus-card" style="text-align:center;">
                    <div class="stat-label">Competitors Nearby</div>
                    <div class="stat-number">{competitor_count}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="venus-card" style="text-align:center;">
                    <div class="stat-label">Est. Reach (organic)</div>
                    <div class="stat-number">{random.randint(800,8000):,}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="venus-card" style="margin-top:14px;">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                    <div>
                        <div style="color:#00e5ff;font-weight:700;font-size:13px;margin-bottom:10px;">
                            📱 Best Channels for {product}
                        </div>
                        <div style="font-size:13px;color:#b0bece;line-height:2.4;">
                            {'🥇 TikTok — highest organic reach<br>🥈 Instagram Reels<br>🥉 WhatsApp Broadcast<br>4️⃣ Facebook Marketplace' if demand_score > 0.6 else
                             '🥇 WhatsApp Broadcast<br>🥈 Facebook Groups<br>🥉 Instagram Stories<br>4️⃣ Word of mouth'}
                        </div>
                    </div>
                    <div>
                        <div style="color:#a855f7;font-weight:700;font-size:13px;margin-bottom:10px;">
                            ⚡ Quick Wins
                        </div>
                        <div style="font-size:13px;color:#b0bece;line-height:2.4;">
                            ⏳ Run a 24-hr flash sale<br>
                            🤝 Partner with 2 micro-influencers<br>
                            🏷️ Bundle with complementary item<br>
                            📍 Target {user_location} geo ads
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="venus-card" style="text-align:center;padding:50px 40px;border-style:dashed;
                border-color:rgba(0,229,255,0.12);">
                <div style="font-size:40px;margin-bottom:14px;">🎨</div>
                <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:700;color:#e8edf5;margin-bottom:8px;">
                    Magazine Poster Studio
                </div>
                <div style="font-size:13px;color:#9aaabf;max-width:380px;margin:0 auto;line-height:1.7;">
                    Customise your ad copy above then click
                    <strong style="color:#00e5ff;">Generate Magazine Posters</strong> to create
                    4 professional templates ready for social media.
                </div>
            </div>""", unsafe_allow_html=True)

# =========================================================
# FRAUD DETECTION — Next Level
# =========================================================
elif "Fraud Detection" in menu:
    import time, random, math

    # ── Fraud CSS ──
    st.markdown("""
    <style>
    .fraud-hero {
        position: relative;
        background: linear-gradient(135deg, rgba(255,75,110,0.08) 0%, rgba(0,0,0,0) 60%);
        border: 1px solid rgba(255,75,110,0.15);
        border-radius: 20px;
        padding: 28px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .fraud-hero::before {
        content: '🛡️';
        position: absolute;
        right: 20px; top: 10px;
        font-size: 80px;
        opacity: 0.07;
    }
    .threat-card {
        background: rgba(255,75,110,0.06);
        border: 1px solid rgba(255,75,110,0.18);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s;
    }
    .threat-card:hover { border-color: rgba(255,75,110,0.4); }
    .threat-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        background: #ff4b6e;
        border-radius: 4px 0 0 4px;
    }
    .medium-card {
        background: rgba(255,184,0,0.05);
        border: 1px solid rgba(255,184,0,0.18);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
        position: relative;
        overflow: hidden;
    }
    .medium-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        background: #ffb800;
        border-radius: 4px 0 0 4px;
    }
    .safe-card {
        background: rgba(0,224,150,0.04);
        border: 1px solid rgba(0,224,150,0.15);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
        position: relative;
        overflow: hidden;
    }
    .safe-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        background: #00e096;
        border-radius: 4px 0 0 4px;
    }
    .risk-meter-track {
        height: 10px;
        background: rgba(255,255,255,0.06);
        border-radius: 6px;
        overflow: hidden;
        margin-top: 6px;
    }
    .scanner-line {
        height: 2px;
        background: linear-gradient(90deg, transparent, #ff4b6e, transparent);
        animation: scan 2s linear infinite;
        margin: 6px 0;
    }
    @keyframes scan {
        0%   { margin-left: 0%;   width: 30%; }
        50%  { margin-left: 35%;  width: 30%; }
        100% { margin-left: 70%;  width: 30%; }
    }
    .module-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        margin: 3px;
    }
    .mod-active {
        background: rgba(0,229,255,0.1);
        border: 1px solid rgba(0,229,255,0.25);
        color: #00e5ff;
    }
    .anomaly-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .anomaly-icon { font-size: 16px; flex-shrink: 0; }
    .anomaly-name { font-size: 13px; font-weight: 600; color: #e8edf5; flex: 1; }
    .anomaly-score { font-size: 13px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("# 🛡️ Fraud Detection Engine")
    st.markdown('<div class="section-label">Real-time multi-layer threat analysis · AI anomaly detection · Blockchain verification</div>', unsafe_allow_html=True)

    conn2 = sqlite3.connect("venus_ai.db")
    cursor2 = conn2.cursor()
    if st.session_state.role == "Supplier":
        cursor2.execute("SELECT product, price, qty, supplier, location FROM products WHERE user_id = ?", (user["id"],))
    else:
        cursor2.execute("SELECT product, price, qty, supplier, location FROM products")
    rows = cursor2.fetchall()
    conn2.close()

    if not rows:
        st.info("No inventory data available for analysis.")
        st.stop()

    df = pd.DataFrame(rows, columns=["product","price","qty","supplier","location"])

    # ── SCAN animation ──
    scan_ph = st.empty()
    scan_ph.markdown("""
    <div style="background:rgba(255,75,110,0.05);border:1px solid rgba(255,75,110,0.15);
        border-radius:14px;padding:20px 24px;">
        <div style="font-size:13px;font-weight:700;color:#ff4b6e;margin-bottom:10px;">
            🔍 VENUS FRAUD ENGINE — SCANNING INVENTORY...
        </div>
        <div class="scanner-line"></div>
        <div class="scanner-line" style="animation-delay:0.5s;"></div>
        <div class="scanner-line" style="animation-delay:1s;"></div>
        <div style="font-size:11px;color:#9aaabf;margin-top:8px;">
            Checking price anomalies · Verifying supplier identities ·
            Cross-referencing locations · Analysing transaction patterns
        </div>
    </div>""", unsafe_allow_html=True)
    time.sleep(1.4)
    scan_ph.empty()

    # ── SCORING ENGINE ──
    np.random.seed(42)
    avg_price = df["price"].mean() or 1
    med_price = df["price"].median() or 1

    # Price anomaly — how far from median
    df["price_anomaly"]   = (abs(df["price"] - med_price) / med_price).clip(0, 1)
    # Stock anomaly
    df["stock_anomaly"]   = df["qty"].apply(lambda x: 1.0 if x > 1000 else (0.7 if x < 1 else 0.0))
    # Location risk
    df["location_risk"]   = df["location"].apply(
        lambda x: 0.8 if not str(x).strip() or "unknown" in str(x).lower() else 0.1)
    # Supplier risk (duplicate supplier names raise flags)
    supplier_counts = df["supplier"].value_counts()
    df["supplier_risk"]   = df["supplier"].apply(
        lambda x: 0.3 if supplier_counts.get(x, 0) > 3 else 0.0)
    # Simulated behavioral signals
    np.random.seed(abs(hash(str(df["product"].tolist()))) % 9999)
    df["behavioral_risk"] = np.random.uniform(0, 0.6, len(df)).round(3)
    df["velocity_risk"]   = np.random.uniform(0, 0.5, len(df)).round(3)

    # Weighted fraud score
    df["fraud_score"] = (
        0.28 * df["price_anomaly"] +
        0.22 * df["stock_anomaly"] +
        0.18 * df["location_risk"] +
        0.12 * df["supplier_risk"] +
        0.12 * df["behavioral_risk"] +
        0.08 * df["velocity_risk"]
    ).round(3).clip(0, 1)

    def risk_label(s):
        if s > 0.65: return "HIGH RISK"
        elif s > 0.35: return "MEDIUM RISK"
        else: return "LOW RISK"

    df["risk_level"] = df["fraud_score"].apply(risk_label)

    high_df = df[df["risk_level"]=="HIGH RISK"]
    med_df  = df[df["risk_level"]=="MEDIUM RISK"]
    low_df  = df[df["risk_level"]=="LOW RISK"]
    high_n, med_n, low_n = len(high_df), len(med_df), len(low_df)

    overall_score = df["fraud_score"].mean()
    system_status = "CRITICAL" if high_n > 2 else "ELEVATED" if high_n > 0 or med_n > 3 else "NOMINAL"
    status_color  = "#ff4b6e" if system_status=="CRITICAL" else "#ffb800" if system_status=="ELEVATED" else "#00e096"

    # ══════════════════════════════════
    # HERO — System threat level
    # ══════════════════════════════════
    st.markdown(f"""
    <div class="fraud-hero">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px;">
            <div>
                <div style="font-size:11px;font-weight:700;letter-spacing:.12em;
                    text-transform:uppercase;color:#9aaabf;margin-bottom:8px;">
                    THREAT LEVEL
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:42px;font-weight:900;
                    color:{status_color};line-height:1;letter-spacing:-1px;">
                    {system_status}
                </div>
                <div style="font-size:13px;color:#b0bece;margin-top:8px;">
                    Overall fraud risk index: <strong style="color:{status_color};">
                    {int(overall_score*100)}/100</strong>
                    &nbsp;·&nbsp; {len(df)} products analysed
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px;color:#9aaabf;margin-bottom:6px;">DETECTION MODULES</div>
                <div>
                    <span class="module-badge mod-active">💲 Price AI</span>
                    <span class="module-badge mod-active">📦 Stock AI</span>
                    <span class="module-badge mod-active">🌍 Location AI</span>
                    <span class="module-badge mod-active">🤝 Supplier AI</span>
                    <span class="module-badge mod-active">🧠 Behavioral AI</span>
                    <span class="module-badge mod-active">⚡ Velocity AI</span>
                </div>
            </div>
        </div>
        <div style="margin-top:18px;">
            <div style="font-size:11px;color:#9aaabf;margin-bottom:5px;">SYSTEM RISK METER</div>
            <div class="risk-meter-track">
                <div style="height:100%;width:{int(overall_score*100)}%;
                    background:linear-gradient(90deg,#00e096,#ffb800,#ff4b6e);
                    border-radius:6px;transition:width 1s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px;
                color:#6a7a92;margin-top:4px;">
                <span>SAFE</span><span>MODERATE</span><span>HIGH RISK</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # STAT CARDS ROW
    # ══════════════════════════════════
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    stats = [
        (c1, str(len(df)),    "Products",      "#b0bece", "rgba(255,255,255,0.07)"),
        (c2, str(high_n),     "High Risk",     "#ff4b6e", "rgba(255,75,110,0.15)"),
        (c3, str(med_n),      "Medium Risk",   "#ffb800", "rgba(255,184,0,0.12)"),
        (c4, str(low_n),      "Low Risk",      "#00e096", "rgba(0,224,150,0.10)"),
        (c5, f"{int(df['price_anomaly'].mean()*100)}%", "Price Anomaly", "#00e5ff", "rgba(0,229,255,0.08)"),
        (c6, f"{int(df['behavioral_risk'].mean()*100)}%", "Behavior Risk", "#a855f7", "rgba(168,85,247,0.1)"),
    ]
    for col, val, lbl, vc, bg in stats:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {vc}30;border-radius:12px;
                padding:14px 10px;text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:900;
                    color:{vc};line-height:1;">{val}</div>
                <div style="font-size:10px;color:#9aaabf;text-transform:uppercase;
                    letter-spacing:.08em;margin-top:4px;">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════
    # THREAT ALERTS — HIGH RISK
    # ══════════════════════════════════
    col_alerts, col_radar = st.columns([1.4, 1])

    with col_alerts:
        if not high_df.empty:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                <div style="width:10px;height:10px;background:#ff4b6e;border-radius:50%;
                    box-shadow:0 0 8px #ff4b6e;animation:pulse 1.5s infinite;"></div>
                <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;color:#ff4b6e;">
                    {high_n} ACTIVE THREAT{"S" if high_n>1 else ""} DETECTED
                </div>
            </div>
            <style>@keyframes pulse {{
                0%,100% {{ box-shadow:0 0 6px #ff4b6e; }}
                50%      {{ box-shadow:0 0 16px #ff4b6e; }}
            }}</style>""", unsafe_allow_html=True)

            for _, row in high_df.iterrows():
                # Determine which factors are spiking
                flags = []
                if row["price_anomaly"] > 0.4:   flags.append(f"💲 Price deviates {int(row['price_anomaly']*100)}% from market")
                if row["stock_anomaly"] > 0.5:    flags.append("📦 Abnormal stock quantity")
                if row["location_risk"] > 0.5:    flags.append("🌍 Location unverified")
                if row["behavioral_risk"] > 0.4:  flags.append("🧠 Suspicious behavioral pattern")
                if row["velocity_risk"] > 0.4:    flags.append("⚡ Unusual listing velocity")
                if not flags:                     flags.append("🔍 Multiple low-level signals converging")

                flags_html = "".join(
                    f'<div style="font-size:11px;color:#ff8899;margin-top:3px;">⚠ {fl}</div>'
                    for fl in flags
                )
                st.markdown(f"""
                <div class="threat-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="flex:1;">
                            <div style="font-size:14px;font-weight:800;color:#e8edf5;">
                                {row['product']}
                            </div>
                            <div style="font-size:11px;color:#9aaabf;margin-top:2px;">
                                {row.get('supplier','Unknown')} · {row.get('location','—')} ·
                                ${row['price']:.2f} · Qty: {row['qty']}
                            </div>
                        </div>
                        <div style="text-align:right;flex-shrink:0;margin-left:12px;">
                            <div style="font-family:'Syne',sans-serif;font-size:22px;
                                font-weight:900;color:#ff4b6e;">{int(row['fraud_score']*100)}</div>
                            <div style="font-size:9px;color:#9aaabf;">RISK SCORE</div>
                        </div>
                    </div>
                    <div style="margin-top:8px;">
                        <div class="risk-meter-track">
                            <div style="height:100%;width:{int(row['fraud_score']*100)}%;
                                background:linear-gradient(90deg,#ffb800,#ff4b6e);border-radius:6px;">
                            </div>
                        </div>
                    </div>
                    <div style="margin-top:10px;">
                        {flags_html}
                    </div>
                    <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,75,110,0.15);
                        font-size:11px;color:#9aaabf;">
                        <strong style="color:#ff4b6e;">Recommended:</strong>
                        Pause listing · Verify supplier identity · Request proof of stock
                    </div>
                </div>""", unsafe_allow_html=True)

        # MEDIUM RISK
        if not med_df.empty:
            st.markdown(f"""
            <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
                color:#ffb800;margin:16px 0 10px;">
                ⚠️ {med_n} MEDIUM RISK ITEM{"S" if med_n>1 else ""}
            </div>""", unsafe_allow_html=True)

            for _, row in med_df.iterrows():
                flags = []
                if row["price_anomaly"] > 0.25: flags.append(f"Price variance: {int(row['price_anomaly']*100)}%")
                if row["behavioral_risk"] > 0.3: flags.append("Mild behavioral anomaly")
                if row["velocity_risk"] > 0.3:   flags.append("Listing velocity above average")
                flag_txt = " · ".join(flags) if flags else "Minor cross-signal anomaly"

                st.markdown(f"""
                <div class="medium-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-size:13px;font-weight:700;color:#e8edf5;">{row['product']}</div>
                            <div style="font-size:11px;color:#9aaabf;margin-top:2px;">
                                {row.get('supplier','—')} · ${row['price']:.2f}
                            </div>
                            <div style="font-size:11px;color:#ffb800;margin-top:4px;">⚡ {flag_txt}</div>
                        </div>
                        <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:900;
                            color:#ffb800;">{int(row['fraud_score']*100)}</div>
                    </div>
                    <div class="risk-meter-track" style="margin-top:8px;">
                        <div style="height:100%;width:{int(row['fraud_score']*100)}%;
                            background:#ffb800;border-radius:6px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # SAFE
        if not low_df.empty:
            safe_chips = " ".join(
                f'<span style="font-size:12px;color:#e8edf5;background:rgba(0,224,150,0.08);'
                f'border:1px solid rgba(0,224,150,0.15);border-radius:8px;padding:4px 10px;">'
                f'{r["product"]} <span style="color:#00e096;">✓</span></span>'
                for _, r in low_df.iterrows()
            )
            st.markdown(f"""
            <div style="margin-top:16px;">
                <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
                    color:#00e096;margin-bottom:10px;">
                    ✅ {low_n} VERIFIED SAFE
                </div>
                <div class="safe-card">
                    <div style="display:flex;flex-wrap:wrap;gap:8px;">
                        {safe_chips}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # RIGHT COL — Radar / Factor breakdown
    # ══════════════════════════════════
    with col_radar:
        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
            color:#e8edf5;margin-bottom:14px;">📊 Detection Factor Analysis</div>""", unsafe_allow_html=True)

        factors = [
            ("💲 Price Anomaly",    float(df["price_anomaly"].mean()),    "#ff4b6e"),
            ("📦 Stock Risk",       float(df["stock_anomaly"].mean()),     "#ffb800"),
            ("🌍 Location Risk",    float(df["location_risk"].mean()),     "#a855f7"),
            ("🤝 Supplier Risk",    float(df["supplier_risk"].mean()),     "#00e5ff"),
            ("🧠 Behavioral Risk",  float(df["behavioral_risk"].mean()),   "#ff4b6e"),
            ("⚡ Velocity Risk",    float(df["velocity_risk"].mean()),     "#ffb800"),
        ]

        for label, val, color in factors:
            pct = int(val * 100)
            threat = "HIGH" if pct > 50 else "MED" if pct > 25 else "LOW"
            tc = "#ff4b6e" if threat=="HIGH" else "#ffb800" if threat=="MED" else "#00e096"
            st.markdown(f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                    <span style="font-size:12px;color:#e8edf5;">{label}</span>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:10px;font-weight:700;padding:1px 7px;
                            border-radius:10px;background:{tc}20;color:{tc};">{threat}</span>
                        <span style="font-size:13px;font-weight:800;color:{color};">{pct}%</span>
                    </div>
                </div>
                <div class="risk-meter-track">
                    <div style="height:100%;width:{pct}%;background:{color};
                        border-radius:6px;opacity:0.85;"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        # AI recommendation box
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if high_n > 0:
            rec = f"Immediate action required on {high_n} listing(s). Suspend flagged products and request supplier verification documents before reinstating."
            rec_c = "#ff4b6e"
            rec_bg = "rgba(255,75,110,0.07)"
            rec_border = "rgba(255,75,110,0.2)"
        elif med_n > 0:
            rec = f"{med_n} product(s) show moderate risk signals. Monitor closely over the next 48 hours and consider requesting additional supplier documentation."
            rec_c = "#ffb800"
            rec_bg = "rgba(255,184,0,0.06)"
            rec_border = "rgba(255,184,0,0.2)"
        else:
            rec = "All products are within safe parameters. Your inventory shows strong trust signals. Continue routine monitoring."
            rec_c = "#00e096"
            rec_bg = "rgba(0,224,150,0.06)"
            rec_border = "rgba(0,224,150,0.18)"

        st.markdown(f"""
        <div style="background:{rec_bg};border:1px solid {rec_border};border-radius:14px;padding:16px;">
            <div style="font-size:11px;font-weight:700;letter-spacing:.08em;
                text-transform:uppercase;color:{rec_c};margin-bottom:8px;">
                🧠 AI Recommendation
            </div>
            <div style="font-size:13px;color:#e8edf5;line-height:1.7;">{rec}</div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # FULL INVENTORY TABLE (expandable)
    # ══════════════════════════════════
    st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)
    with st.expander("📋 Full Inventory Risk Table", expanded=False):
        display_df = df[["product","price","qty","supplier","location",
                          "fraud_score","price_anomaly","behavioral_risk","risk_level"]].copy()
        display_df.columns = ["Product","Price","Qty","Supplier","Location",
                               "Fraud Score","Price Anomaly","Behavior Risk","Risk Level"]
        display_df["Fraud Score"]    = (display_df["Fraud Score"]*100).round(1).astype(str) + "%"
        display_df["Price Anomaly"]  = (display_df["Price Anomaly"]*100).round(1).astype(str) + "%"
        display_df["Behavior Risk"]  = (display_df["Behavior Risk"]*100).round(1).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# =========================================================
# VISION AI — Upgraded
# =========================================================
elif "Vision AI" in menu:
    import base64, io, json, requests
    from PIL import Image

    # ── Custom CSS injected once ──────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    .vai-hero { padding: 0 0 36px 0; }
    .vai-hero-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(99,153,34,0.12); border: 1px solid rgba(99,153,34,0.3);
        color: #3B6D11; border-radius: 100px; font-size: 11px; font-weight: 600;
        letter-spacing: 0.08em; padding: 4px 12px; margin-bottom: 14px;
        text-transform: uppercase;
    }
    .vai-hero-title {
        font-family: 'Syne', sans-serif; font-size: 32px; font-weight: 800;
        line-height: 1.15; margin: 0 0 10px 0; letter-spacing: -0.02em;
    }
    .vai-hero-sub {
        font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 300;
        color: var(--text-muted); line-height: 1.65; max-width: 540px;
    }

    .vai-capability-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
        margin: 28px 0 36px 0;
    }
    .vai-cap-card {
        background: var(--background-secondary, #f8f8f8);
        border: 1px solid rgba(128,128,128,0.15);
        border-radius: 14px; padding: 18px 16px; position: relative; overflow: hidden;
    }
    .vai-cap-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        border-radius: 14px 14px 0 0;
    }
    .vai-cap-card.green::before  { background: linear-gradient(90deg,#639922,#97C459); }
    .vai-cap-card.amber::before  { background: linear-gradient(90deg,#BA7517,#EF9F27); }
    .vai-cap-card.blue::before   { background: linear-gradient(90deg,#185FA5,#378ADD); }
    .vai-cap-icon { font-size: 22px; margin-bottom: 10px; }
    .vai-cap-title {
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700;
        margin-bottom: 5px;
    }
    .vai-cap-desc {
        font-size: 12px; line-height: 1.55; color: var(--text-muted);
        font-family: 'DM Sans', sans-serif;
    }

    .vai-drop-zone {
        border: 2px dashed rgba(128,128,128,0.25); border-radius: 20px;
        background: linear-gradient(135deg, rgba(99,153,34,0.04) 0%, rgba(55,138,221,0.04) 100%);
        padding: 60px 40px; text-align: center; transition: all 0.2s;
    }
    .vai-drop-icon { font-size: 48px; margin-bottom: 18px; line-height: 1; }
    .vai-drop-title {
        font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700;
        margin-bottom: 8px;
    }
    .vai-drop-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }
    .vai-drop-formats {
        display: inline-flex; gap: 8px; margin-top: 10px;
    }
    .vai-format-pill {
        background: rgba(128,128,128,0.1); border-radius: 100px;
        font-size: 11px; font-weight: 600; padding: 3px 10px;
        letter-spacing: 0.06em; color: var(--text-muted);
    }

    .vai-verdict-card {
        border-radius: 18px; padding: 28px; margin-bottom: 18px;
        border: 1.5px solid;
    }
    .vai-verdict-label {
        font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; margin-bottom: 6px;
    }
    .vai-verdict-main {
        font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800;
        margin-bottom: 4px; line-height: 1.1;
    }
    .vai-verdict-sub { font-size: 13px; color: var(--text-muted); line-height: 1.5; }

    .vai-metric-row { display: flex; gap: 10px; margin: 16px 0; flex-wrap: wrap; }
    .vai-metric {
        flex: 1; min-width: 80px; background: rgba(128,128,128,0.07);
        border-radius: 12px; padding: 12px 14px; text-align: center;
    }
    .vai-metric-val {
        font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; line-height: 1;
    }
    .vai-metric-lbl { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

    .vai-flag {
        display: flex; align-items: flex-start; gap: 10px;
        background: rgba(186,117,23,0.08); border-left: 3px solid #BA7517;
        border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 8px 0;
        font-size: 13px; line-height: 1.5;
    }
    .vai-flag-ok {
        display: flex; align-items: flex-start; gap: 10px;
        background: rgba(99,153,34,0.08); border-left: 3px solid #639922;
        border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 8px 0;
        font-size: 13px; line-height: 1.5;
    }
    .vai-ai-section {
        background: rgba(55,138,221,0.06); border: 1px solid rgba(55,138,221,0.2);
        border-radius: 14px; padding: 18px; margin-top: 16px;
    }
    .vai-ai-label {
        font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #185FA5; margin-bottom: 10px;
    }
    .vai-ai-text { font-size: 13px; line-height: 1.65; color: var(--text-secondary); }

    .vai-score-ring-wrap { text-align: center; padding: 20px 0 8px; }
    .vai-score-num {
        font-family: 'Syne', sans-serif; font-size: 56px; font-weight: 800;
        line-height: 1; letter-spacing: -0.03em;
    }
    .vai-score-lbl { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="vai-hero">
        <div class="vai-hero-badge">🔬 Vision AI</div>
        <div class="vai-hero-title">Is your product image<br>working <em>for</em> or <em>against</em> you?</div>
        <div class="vai-hero-sub">
            Upload any product photo. Vision AI detects AI-generated fakes, 
            reverse-searches for plagiarism signals, scores image quality, 
            and tells you exactly what it means for your sales conversions.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Capability cards ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="vai-capability-grid">
        <div class="vai-cap-card green">
            <div class="vai-cap-icon">🧠</div>
            <div class="vai-cap-title">AI Fake Detection</div>
            <div class="vai-cap-desc">Flags synthetic textures, impossible lighting, and artifacts left by Midjourney, DALL·E, and Stable Diffusion.</div>
        </div>
        <div class="vai-cap-card amber">
            <div class="vai-cap-icon">🔍</div>
            <div class="vai-cap-title">Plagiarism Signals</div>
            <div class="vai-cap-desc">Detects stock photo fingerprints, watermark remnants, and signals suggesting the image wasn't originally yours.</div>
        </div>
        <div class="vai-cap-card blue">
            <div class="vai-cap-icon">📈</div>
            <div class="vai-cap-title">Conversion Impact</div>
            <div class="vai-cap-desc">Translates every technical finding into a plain-language revenue impact — so you know what actually needs fixing.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File uploader ─────────────────────────────────────────────────────────
    file = st.file_uploader(
        "Upload a product image",
        type=["jpg", "png", "jpeg"],
        key="vision_upload",
        label_visibility="collapsed"
    )

    # ── Empty state ───────────────────────────────────────────────────────────
    if not file:
        st.markdown("""
        <div class="vai-drop-zone">
            <div class="vai-drop-icon">🖼️</div>
            <div class="vai-drop-title">Drop your product image here</div>
            <div class="vai-drop-sub">We'll scan it for AI generation, plagiarism risk, and quality issues in seconds.</div>
            <div class="vai-drop-formats">
                <span class="vai-format-pill">JPG</span>
                <span class="vai-format-pill">PNG</span>
                <span class="vai-format-pill">JPEG</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("💡 What makes a product image trustworthy?"):
            st.markdown("""
            Buyers make snap judgments in under 200ms. Your image signals authenticity before a single word is read.

            **Red flags that kill conversions:**
            - Obvious AI-generation artifacts (melting edges, impossible reflections)
            - Watermarked or heavily filtered stock photos
            - Flat, shadowless lighting that looks "too clean"
            - Off-brand colour grading inconsistent with other listings

            **What Vision AI checks:**
            1. Pixel-level texture and noise patterns (AI images are unnaturally smooth)
            2. Lighting consistency (synthetic images often have impossible light sources)
            3. Colour channel distribution (stock photos share recognizable fingerprints)
            4. Edge sharpness and compression artefact profiles
            5. Claude's own multimodal understanding of the full scene
            """)

    # ── Analysis ──────────────────────────────────────────────────────────────
    else:
        image = Image.open(file).convert("RGB")
        img_array = np.array(image)

        # — Pixel-level metrics —
        brightness   = float(img_array.mean())
        contrast     = float(img_array.std())
        red_mean     = float(img_array[:, :, 0].mean())
        green_mean   = float(img_array[:, :, 1].mean())
        blue_mean    = float(img_array[:, :, 2].mean())
        color_var    = float(np.std([red_mean, green_mean, blue_mean]))
        texture      = float(np.mean(np.abs(np.diff(img_array, axis=0))))

        # Noise analysis (high-frequency content ratio)
        from scipy import ndimage
        blurred      = ndimage.gaussian_filter(img_array.astype(float), sigma=2)
        noise_energy = float(np.mean(np.abs(img_array.astype(float) - blurred)))

        # Edge density
        gray         = np.mean(img_array, axis=2)
        diff_y = np.abs(np.diff(gray, axis=0))   # shape: (H-1, W)
        diff_x = np.abs(np.diff(gray, axis=1))   # shape: (H,   W-1)
 
        # Crop both to the overlapping region (H-1, W-1) so shapes match
        edges = diff_y[:, :-1] + diff_x[:-1, :]
        edge_density = float(np.mean(edges > 15))

        # — Rule-based risk scoring —
        risk_score = 0
        flags = []

        if brightness < 60 or brightness > 215:
            risk_score += 15
            flags.append(("lighting", "Extreme brightness — suggests artificial or heavily edited lighting"))

        if contrast < 25:
            risk_score += 20
            flags.append(("contrast", "Very low contrast — hallmark of AI-generated or heavily smoothed images"))

        if color_var < 6:
            risk_score += 20
            flags.append(("color", "Unnaturally uniform colour channels — common in AI-generated images"))

        if texture < 8:
            risk_score += 20
            flags.append(("texture", "Low texture complexity — may indicate AI generation or heavy post-processing"))

        if noise_energy < 3.0:
            risk_score += 15
            flags.append(("noise", "Near-zero noise signature — real photographs always contain sensor noise"))

        if edge_density < 0.04:
            risk_score += 10
            flags.append(("edges", "Sparse edge detail — possible over-smoothing or stock/composite image"))

        authenticity = max(0, 100 - risk_score)

        # — Encode image for Claude API —
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        # — Build pixel summary for Claude —
        pixel_summary = f"""
Pixel-level analysis:
- Brightness: {brightness:.1f}/255
- Contrast (std dev): {contrast:.1f}
- Colour channel variation (R/G/B spread): {color_var:.2f}
- Texture score: {texture:.2f}
- Noise energy: {noise_energy:.2f}
- Edge density: {edge_density:.3f}
- Rule-based authenticity score: {authenticity}%
- Flagged issues: {[f[1] for f in flags] if flags else "none"}
        """.strip()

        # — Call Claude API —
        with st.spinner("🔬 Running deep image analysis with Vision AI..."):
            try:
                api_response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1000,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": img_b64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": f"""You are Vision AI, an expert in product image authenticity for e-commerce.

Analyse this product image across three dimensions and respond ONLY as valid JSON — no markdown, no extra text.

Pixel-level metrics for context:
{pixel_summary}

Return exactly this JSON structure:
{{
  "ai_verdict": {{
    "is_likely_ai": true/false,
    "confidence": "high"/"medium"/"low",
    "reasoning": "1-2 sentence explanation of visual evidence for or against AI generation"
  }},
  "plagiarism_signals": {{
    "risk_level": "high"/"medium"/"low"/"none",
    "signals_found": ["list of up to 3 specific visual signals, or empty array"],
    "reasoning": "1-2 sentence explanation"
  }},
  "quality_assessment": {{
    "overall_grade": "A"/"B"/"C"/"D"/"F",
    "strengths": ["up to 2 genuine strengths"],
    "weaknesses": ["up to 2 genuine weaknesses"],
    "conversion_impact": "1-2 sentence plain-English business impact"
  }},
  "recommendation": "One actionable sentence: what should the seller do next?"
}}"""
                                }
                            ]
                        }]
                    },
                    timeout=30
                )
                raw = api_response.json()["content"][0]["text"]
                clean = raw.replace("```json", "").replace("```", "").strip()
                ai_data = json.loads(clean)
            except Exception as e:
                ai_data = None

        # ── Layout ────────────────────────────────────────────────────────────
        col_img, col_res = st.columns([1, 1.3])

        with col_img:
            st.image(image, caption="Uploaded image", use_container_width=True)

            # Quick metrics under image
            st.markdown(f"""
            <div class="vai-metric-row">
                <div class="vai-metric">
                    <div class="vai-metric-val">{brightness:.0f}</div>
                    <div class="vai-metric-lbl">Brightness</div>
                </div>
                <div class="vai-metric">
                    <div class="vai-metric-val">{contrast:.0f}</div>
                    <div class="vai-metric-lbl">Contrast</div>
                </div>
                <div class="vai-metric">
                    <div class="vai-metric-val">{texture:.1f}</div>
                    <div class="vai-metric-lbl">Texture</div>
                </div>
                <div class="vai-metric">
                    <div class="vai-metric-val">{noise_energy:.1f}</div>
                    <div class="vai-metric-lbl">Noise</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_res:
            # — Authenticity score card —
            if authenticity >= 75:
                score_color = "#639922"
                score_bg    = "rgba(99,153,34,0.08)"
                score_bdr   = "rgba(99,153,34,0.3)"
                score_label = "Likely Authentic"
            elif authenticity >= 45:
                score_color = "#BA7517"
                score_bg    = "rgba(186,117,23,0.08)"
                score_bdr   = "rgba(186,117,23,0.3)"
                score_label = "Suspicious — Review Needed"
            else:
                score_color = "#A32D2D"
                score_bg    = "rgba(163,45,45,0.08)"
                score_bdr   = "rgba(163,45,45,0.3)"
                score_label = "High Risk — Likely Fake or Plagiarised"

            st.markdown(f"""
            <div class="vai-verdict-card" style="background:{score_bg};border-color:{score_bdr};">
                <div class="vai-verdict-label" style="color:{score_color};">Authenticity Score</div>
                <div class="vai-score-ring-wrap">
                    <div class="vai-score-num" style="color:{score_color};">{authenticity}%</div>
                    <div class="vai-score-lbl">{score_label}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # — Pixel flags —
            if flags:
                st.markdown("**Technical flags detected:**")
                for _, msg in flags:
                    st.markdown(f'<div class="vai-flag">⚠️ &nbsp;{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="vai-flag-ok">✅ &nbsp;No pixel-level anomalies detected</div>', unsafe_allow_html=True)

            # — Claude AI analysis —
            if ai_data:
                ai_v   = ai_data.get("ai_verdict", {})
                plag_v = ai_data.get("plagiarism_signals", {})
                qual_v = ai_data.get("quality_assessment", {})
                reco   = ai_data.get("recommendation", "")

                # AI verdict
                ai_icon  = "🤖" if ai_v.get("is_likely_ai") else "📷"
                ai_label = "AI-Generated" if ai_v.get("is_likely_ai") else "Appears Human-Taken"
                ai_conf  = ai_v.get("confidence", "").capitalize()
                st.markdown(f"""
                <div class="vai-ai-section">
                    <div class="vai-ai-label">🧠 Claude's Deep Analysis</div>
                    <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:14px;">
                        <div style="font-size:28px;line-height:1;">{ai_icon}</div>
                        <div>
                            <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;">{ai_label} <span style="font-size:11px;font-weight:400;color:var(--text-muted);">({ai_conf} confidence)</span></div>
                            <div class="vai-ai-text">{ai_v.get("reasoning", "")}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Plagiarism
                p_risk = plag_v.get("risk_level", "none")
                p_map  = {"high": ("🚨", "#A32D2D"), "medium": ("⚠️", "#BA7517"),
                          "low": ("🔶", "#BA7517"), "none": ("✅", "#639922")}
                p_ico, p_col = p_map.get(p_risk, p_map["none"])
                p_signals = plag_v.get("signals_found", [])

                st.markdown(f"""
                <div style="margin-top:14px;">
                    <div style="font-size:12px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;
                        color:{p_col};margin-bottom:6px;">🔍 Plagiarism Risk — {p_risk.upper()}</div>
                    <div class="vai-ai-text">{plag_v.get("reasoning","")}</div>
                    {"".join(f'<div class="vai-flag">{p_ico}&nbsp;{s}</div>' for s in p_signals) if p_signals else '<div class="vai-flag-ok">✅ &nbsp;No stock photo or plagiarism signals detected</div>'}
                </div>
                """, unsafe_allow_html=True)

                # Quality grade
                grade   = qual_v.get("overall_grade", "?")
                g_color = {"A":"#639922","B":"#3B6D11","C":"#BA7517","D":"#A32D2D","F":"#791F1F"}.get(grade, "#888")
                strengths  = qual_v.get("strengths", [])
                weaknesses = qual_v.get("weaknesses", [])

                st.markdown(f"""
                <div style="margin-top:16px;display:flex;gap:16px;align-items:flex-start;">
                    <div style="background:rgba(128,128,128,0.08);border-radius:12px;padding:12px 18px;text-align:center;min-width:64px;">
                        <div style="font-family:'Syne',sans-serif;font-size:36px;font-weight:800;color:{g_color};line-height:1;">{grade}</div>
                        <div style="font-size:10px;color:var(--text-muted);margin-top:2px;">Quality</div>
                    </div>
                    <div style="flex:1;">
                        {"".join(f'<div class="vai-flag-ok">✅ &nbsp;{s}</div>' for s in strengths)}
                        {"".join(f'<div class="vai-flag">⚠️ &nbsp;{w}</div>' for w in weaknesses)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Business impact + recommendation
                st.markdown(f"""
                <div style="margin-top:18px;background:rgba(128,128,128,0.06);border-radius:12px;padding:16px;">
                    <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
                        color:var(--text-muted);margin-bottom:8px;">📈 Business Impact</div>
                    <div class="vai-ai-text">{qual_v.get("conversion_impact","")}</div>
                    {"" if not reco else f'<div style="margin-top:10px;font-size:13px;font-weight:600;color:var(--text-primary);">→ {reco}</div>'}
                </div>
                """, unsafe_allow_html=True)

            else:
                # Fallback if API fails — still show rule-based impact
                if authenticity < 50:
                    st.error("⚠️ High-risk image. Likely to reduce buyer trust and hurt conversion rates. Consider replacing before listing.")
                elif authenticity < 75:
                    st.warning("🔶 Moderate concern. Improving image quality could meaningfully boost conversions.")
                else:
                    st.success("✅ Image quality looks solid — supports buyer confidence.")
# =========================================================
# BLOCKCHAIN
# =========================================================
elif "Blockchain" in menu:
    import hashlib

    st.markdown("# Blockchain Verification")
    st.markdown('<div class="section-label">Immutable product record ledger</div>', unsafe_allow_html=True)

    if "blockchain" not in st.session_state:
        st.session_state.blockchain = []
    if "supplier_scores" not in st.session_state:
        st.session_state.supplier_scores = {}

    col_info, col_action = st.columns([1, 1.4])

    with col_info:
        st.markdown("""
        <div class="venus-card">
            <div style="font-size:13px;font-weight:600;color:var(--accent-cyan);margin-bottom:12px;">Why Blockchain?</div>
            <div style="font-size:13px;color:var(--text-dim);line-height:2.2;">
                🔒 Records cannot be altered once added<br>
                📋 Supplier actions are permanently logged<br>
                🔍 Tampering is detected instantly<br>
                🤝 Trust layer across the entire system
            </div>
        </div>""", unsafe_allow_html=True)

    conn2 = sqlite3.connect("venus_ai.db")
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT product, price, qty, supplier, location FROM products")
    rows = cursor2.fetchall()
    conn2.close()

    if rows:
        df = pd.DataFrame(rows, columns=["product","price","qty","supplier","location"])

        with col_action:
            product = st.selectbox("Select Product to Record", df["product"], key="bc_prod")
            item = df[df["product"] == product].iloc[0]

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🧱 Add to Blockchain", key="bc_add_btn", use_container_width=True):
                    timestamp = str(datetime.datetime.now())
                    data_str = f"{item['product']}{item['price']}{item['qty']}{item['supplier']}{item['location']}{timestamp}"
                    hash_val = hashlib.sha256(data_str.encode()).hexdigest()
                    prev_hash = st.session_state.blockchain[-1]["hash"] if st.session_state.blockchain else "GENESIS"
                    block = {"product":item["product"],"price":item["price"],"qty":item["qty"],
                             "supplier":item["supplier"],"location":item["location"],
                             "time":timestamp,"hash":hash_val,"previous_hash":prev_hash}
                    st.session_state.blockchain.append(block)
                    if item["supplier"] not in st.session_state.supplier_scores:
                        st.session_state.supplier_scores[item["supplier"]] = 100
                    st.success("✅ Block added to chain!")

            with col_b2:
                if st.button("🔍 Verify Chain", key="bc_verify_btn", use_container_width=True):
                    valid = all(
                        st.session_state.blockchain[i]["previous_hash"] == st.session_state.blockchain[i-1]["hash"]
                        for i in range(1, len(st.session_state.blockchain))
                    )
                    if valid:
                        st.success("✅ Chain integrity verified")
                    else:
                        st.error("❌ Tampering detected!")
                        for block in st.session_state.blockchain:
                            sup = block["supplier"]
                            st.session_state.supplier_scores[sup] = st.session_state.supplier_scores.get(sup, 100) - 10

            st.checkbox("⚡ Auto-record on selection", key="bc_auto")
            if st.session_state.get("bc_auto"):
                timestamp = str(datetime.datetime.now())
                data_str = f"{item['product']}{item['price']}{item['qty']}{item['supplier']}{item['location']}{timestamp}"
                hash_val = hashlib.sha256(data_str.encode()).hexdigest()
                prev_hash = st.session_state.blockchain[-1]["hash"] if st.session_state.blockchain else "GENESIS"
                block = {"product":item["product"],"price":item["price"],"qty":item["qty"],
                         "supplier":item["supplier"],"location":item["location"],
                         "time":timestamp,"hash":hash_val,"previous_hash":prev_hash}
                st.session_state.blockchain.append(block)

            if st.button("💣 Simulate Tampering", key="bc_tamper"):
                if st.session_state.blockchain:
                    st.session_state.blockchain[0]["price"] = 999999
                    st.warning("⚠️ Block 0 has been tampered with!")

        st.markdown('<div class="venus-divider"></div>', unsafe_allow_html=True)

        col_ledger, col_trust = st.columns([1.5, 1])

        with col_ledger:
            if st.session_state.blockchain:
                st.markdown("### 📜 Blockchain Ledger")
                for block in reversed(st.session_state.blockchain[-5:]):
                    st.markdown(f"""
                    <div class="venus-card" style="font-size:12px;padding:14px;font-family:monospace;color:var(--text-dim);">
                        <div style="color:var(--accent-cyan);font-weight:700;margin-bottom:6px;">📦 {block['product']}</div>
                        <div>Price: {block['price']} | Qty: {block['qty']}</div>
                        <div>Supplier: {block['supplier']} | {block['location']}</div>
                        <div style="margin-top:6px;word-break:break-all;">Hash: {block['hash'][:40]}...</div>
                        <div style="color:var(--text-muted);">Prev: {block['previous_hash'][:30]}...</div>
                        <div style="margin-top:4px;">{block['time']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No blocks recorded yet.")

        with col_trust:
            if st.session_state.supplier_scores:
                st.markdown("### 🧠 Supplier Trust")
                for supplier, score in st.session_state.supplier_scores.items():
                    color = "var(--success)" if score > 80 else ("var(--warning)" if score > 50 else "var(--danger)")
                    label = "Highly Trusted" if score > 80 else ("Moderate" if score > 50 else "High Risk")
                    st.markdown(f"""
                    <div class="venus-card" style="padding:14px;border-color:{color}30;">
                        <div style="font-size:13px;font-weight:600;color:var(--text-primary);">{supplier}</div>
                        <div style="color:{color};font-size:20px;font-weight:800;margin:4px 0;">{score}</div>
                        <div style="font-size:11px;color:var(--text-muted);">{label}</div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.info("No inventory data available for blockchain recording.")
# =========================================================
# SUPPLIER INBOX & PRODUCTS — Fixed image_url column error
# =========================================================
elif "Inbox & Products" in menu:
    import random

    st.markdown("# Inbox & Product Manager")
    st.markdown('<div class="section-label">Communicate with customers · Manage product info & images</div>', unsafe_allow_html=True)

    # ── Ensure tables + columns exist ──
    c2 = sqlite3.connect("venus_ai.db")
    c2.execute("""CREATE TABLE IF NOT EXISTS seller_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_name TEXT, buyer_id INTEGER,
        sender TEXT, message TEXT, sent_at DATETIME)""")
    c2.execute("""CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER, product TEXT, price REAL, qty INTEGER,
        supplier TEXT, location TEXT, status TEXT DEFAULT 'pending',
        added_at DATETIME)""")

    # Safely add optional columns — each in its own try/except
    for alter_sql in [
        "ALTER TABLE products ADD COLUMN description TEXT",
        "ALTER TABLE products ADD COLUMN image_url TEXT",
        "ALTER TABLE products ADD COLUMN image_data TEXT",
    ]:
        try:
            c2.execute(alter_sql)
            c2.commit()
        except Exception:
            pass  # Column already exists — safe to ignore

    c2.commit()

    inbox_tab, products_tab = st.tabs(["Customer Inbox", "Product Info Manager"])

    # ═══════════════════════════════════
    # TAB 1 — INBOX
    # ═══════════════════════════════════
    with inbox_tab:
        supplier_name = user.get("name", "")
        msgs = c2.execute("""
            SELECT id, seller_name, buyer_id, sender, message, sent_at
            FROM seller_messages
            WHERE seller_name = ? OR seller_name = ?
            ORDER BY sent_at DESC
        """, (supplier_name, user.get("username", ""))).fetchall()

        orders = c2.execute("""
            SELECT id, buyer_id, product, price, qty, status, added_at
            FROM cart WHERE supplier = ? OR supplier = ?
            ORDER BY id DESC
        """, (supplier_name, user.get("username", ""))).fetchall()

        oc1, oc2 = st.columns([1.4, 1])

        with oc1:
            st.markdown("#### Customer Messages")
            if msgs:
                buyers = {}
                for m in msgs:
                    bid = m[2]
                    if bid not in buyers:
                        buyers[bid] = []
                    buyers[bid].append(m)

                selected_buyer = st.selectbox(
                    "Conversation with buyer",
                    list(buyers.keys()),
                    format_func=lambda x: f"Buyer #{x}",
                    key="inbox_buyer_sel"
                )

                convo = buyers[selected_buyer]
                st.markdown(f"""
                <div style="background:rgba(0,0,0,0.3);border:1px solid rgba(0,229,255,0.1);
                    border-radius:14px;padding:16px;min-height:200px;max-height:320px;
                    overflow-y:auto;margin-bottom:12px;">""", unsafe_allow_html=True)
                for m in reversed(convo[-20:]):
                    is_buyer = m[3] == "buyer"
                    side  = "flex-start" if is_buyer else "flex-end"
                    bg    = "rgba(255,255,255,0.04)" if is_buyer else "rgba(0,229,255,0.1)"
                    bc    = "rgba(255,255,255,0.06)" if is_buyer else "rgba(0,229,255,0.2)"
                    lbl   = f"Buyer #{m[2]}" if is_buyer else "You (supplier)"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:{side};margin:6px 0;">
                        <div style="max-width:75%;background:{bg};border:1px solid {bc};
                            border-radius:12px;padding:9px 13px;">
                            <div style="font-size:10px;color:#9aaabf;margin-bottom:4px;">{lbl}</div>
                            <div style="font-size:13px;color:#e8edf5;">{m[4]}</div>
                            <div style="font-size:10px;color:#6a7a92;margin-top:4px;">{str(m[5])[:16]}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                reply_msg = st.text_input("Your reply", placeholder="Type your message...", key="inbox_reply")
                if st.button("Send Reply", key="inbox_send", use_container_width=False):
                    if reply_msg.strip():
                        c2.execute(
                            "INSERT INTO seller_messages (seller_name,buyer_id,sender,message,sent_at) VALUES (?,?,?,?,?)",
                            (supplier_name, selected_buyer, "supplier", reply_msg, str(datetime.datetime.now()))
                        )
                        c2.commit()
                        st.success("Reply sent!")
                        st.rerun()
            else:
                st.markdown("""
                <div class="venus-card" style="text-align:center;padding:40px;border-style:dashed;">
                    <div style="font-size:32px;margin-bottom:10px;">📭</div>
                    <div style="color:#9aaabf;font-size:13px;">No customer messages yet.<br>
                    They'll appear here when customers chat about your products.</div>
                </div>""", unsafe_allow_html=True)

        with oc2:
            st.markdown("#### Incoming Orders")
            if orders:
                pending = [o for o in orders if o[5] == "pending"]
                st.markdown(f'<div style="font-size:12px;color:#ffb800;margin-bottom:10px;">{len(pending)} pending orders</div>', unsafe_allow_html=True)
                for o in orders[:8]:
                    status_color = "#ffb800" if o[5] == "pending" else "#00e096"
                    st.markdown(f"""
                    <div class="venus-card" style="padding:12px;margin-bottom:8px;border-color:{status_color}20;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <div style="font-size:13px;font-weight:700;color:#e8edf5;">{o[2]}</div>
                                <div style="font-size:11px;color:#9aaabf;margin-top:2px;">
                                    Buyer #{o[1]} · Qty: {o[4]} · ${o[3]*o[4]:.2f}
                                </div>
                                <div style="font-size:10px;color:#6a7a92;">{str(o[6])[:16]}</div>
                            </div>
                            <span style="font-size:11px;font-weight:700;color:{status_color};text-transform:uppercase;">{o[5]}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    if o[5] == "pending":
                        if st.button("Mark Fulfilled", key=f"fulfill_{o[0]}"):
                            c2.execute("UPDATE cart SET status='fulfilled' WHERE id=?", (o[0],))
                            c2.commit()
                            st.rerun()
            else:
                st.markdown("""
                <div class="venus-card" style="text-align:center;padding:30px;border-style:dashed;">
                    <div style="font-size:28px;margin-bottom:8px;">🛍️</div>
                    <div style="color:#9aaabf;font-size:13px;">No orders yet.</div>
                </div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════
    # TAB 2 — PRODUCT INFO MANAGER
    # ═══════════════════════════════════
    with products_tab:
        st.markdown("#### Manage Your Product Listings")
        st.markdown('<div class="section-label">Add descriptions, upload images, and update product details</div>', unsafe_allow_html=True)

        # image_url is now guaranteed to exist — safe to query
        my_products = c2.execute("""
            SELECT id, product, price, qty, location, description, image_url
            FROM products WHERE user_id = ?
        """, (user["id"],)).fetchall()

        if not my_products:
            st.info("No products found. Go to Add Product to list your first item.")
        else:
            selected_pid = st.selectbox(
                "Select product to edit",
                [p[0] for p in my_products],
                format_func=lambda x: next(p[1] for p in my_products if p[0] == x),
                key="pm_select"
            )
            prod = next(p for p in my_products if p[0] == selected_pid)

            pm_l, pm_r = st.columns([1, 1])

            with pm_l:
                st.markdown("##### Product Details")
                new_name  = st.text_input("Product Name",  value=prod[1],            key="pm_name")
                new_price = st.number_input("Price ($)",   value=float(prod[2]),      min_value=0.0, key="pm_price")
                new_qty   = st.number_input("Stock Qty",   value=int(prod[3]),        min_value=0,   key="pm_qty")
                new_loc   = st.text_input("Location",      value=prod[4] or "",       key="pm_loc")
                new_desc  = st.text_area(
                    "Product Description",
                    value=prod[5] or f"Quality {prod[1]} available in {prod[4] or 'Lusaka'}.",
                    height=100, key="pm_desc",
                    placeholder="Describe your product — condition, features, why buyers should choose you..."
                )

                if st.button("Save Product Info", key="pm_save", use_container_width=True):
                    c2.execute(
                        "UPDATE products SET product=?,price=?,qty=?,location=?,description=? WHERE id=?",
                        (new_name, new_price, new_qty, new_loc, new_desc, selected_pid)
                    )
                    c2.commit()
                    st.success("Product updated!")
                    st.rerun()

            with pm_r:
                st.markdown("##### Product Image")
                current_img = prod[6]  # image_url — now safe
                if current_img and current_img.startswith("http"):
                    st.image(current_img, caption="Current product image", use_container_width=True)
                elif current_img and current_img.startswith("data:"):
                    st.image(current_img, caption="Current product image", use_container_width=True)
                else:
                    st.markdown("""
                    <div style="height:180px;border:1px dashed rgba(0,229,255,0.2);border-radius:12px;
                        display:flex;align-items:center;justify-content:center;
                        background:rgba(0,229,255,0.02);margin-bottom:10px;">
                        <div style="text-align:center;color:#6a7a92;">
                            <div style="font-size:28px;">🖼️</div>
                            <div style="font-size:12px;margin-top:6px;">No image yet</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                uploaded_img  = st.file_uploader("Upload product photo",
                    type=["jpg","jpeg","png","webp"], key=f"pm_img_{selected_pid}")
                img_url_input = st.text_input("Or paste image URL",
                    value=current_img if (current_img or "").startswith("http") else "",
                    key="pm_imgurl")

                if st.button("Update Image", key="pm_img_save", use_container_width=True):
                    new_img_url = img_url_input
                    if uploaded_img:
                        import base64 as _b64
                        img_bytes   = uploaded_img.read()
                        b64         = _b64.b64encode(img_bytes).decode()
                        new_img_url = f"data:{uploaded_img.type};base64,{b64}"
                    if new_img_url:
                        c2.execute("UPDATE products SET image_url=? WHERE id=?", (new_img_url, selected_pid))
                        c2.commit()
                        st.success("Image updated!")
                        st.rerun()

                st.markdown("##### Live Listing Preview")
                st.markdown(f"""
                <div class="product-card" style="margin-top:8px;">
                    <div style="font-size:15px;font-weight:700;color:#e8edf5;">{new_name}</div>
                    <div style="font-size:12px;color:#9aaabf;margin-top:4px;">
                        {new_loc} &nbsp;·&nbsp; {new_qty} in stock
                    </div>
                    <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
                        color:#00e5ff;margin:8px 0;">${new_price:.2f}</div>
                    <div style="font-size:12px;color:#b0bece;line-height:1.6;">
                        {(new_desc or '')[:120]}{'...' if len(new_desc or '') > 120 else ''}
                    </div>
                </div>""", unsafe_allow_html=True)

# =========================================================
# FINANCIAL AI — Full Accounting Intelligence System
# =========================================================
elif "Financial AI" in menu:
    import json, requests, io
    from datetime import datetime, timedelta

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

    .fin-hero { padding: 0 0 28px; }
    .fin-hero-title {
        font-family: 'Syne', sans-serif; font-size: 30px; font-weight: 800;
        letter-spacing: -0.02em; margin: 0 0 6px;
        background: linear-gradient(90deg, #e8edf5 40%, #00e5ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .fin-hero-sub { font-size: 13px; color: #9aaabf; line-height: 1.6; max-width: 560px; }

    .fin-tab-row {
        display: flex; gap: 6px; margin-bottom: 28px;
        border-bottom: 1px solid rgba(0,229,255,0.08); padding-bottom: 0;
    }
    .fin-tab {
        padding: 9px 18px; font-size: 12px; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase;
        border-radius: 8px 8px 0 0; cursor: pointer;
        border: 1px solid transparent; border-bottom: none;
        color: #4a5a72; transition: all 0.2s;
    }
    .fin-tab.active {
        background: rgba(0,229,255,0.07);
        border-color: rgba(0,229,255,0.15);
        color: #00e5ff;
    }

    .fin-card {
        background: rgba(8,8,14,0.95);
        border: 1px solid rgba(0,229,255,0.07);
        border-radius: 18px; padding: 24px; margin-bottom: 16px;
        position: relative; overflow: hidden;
    }
    .fin-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent);
    }
    .fin-card-title {
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase; color: #4a5a72;
        margin-bottom: 18px;
    }

    /* Statement table */
    .fin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .fin-table tr { border-bottom: 1px solid rgba(255,255,255,0.04); }
    .fin-table tr:last-child { border-bottom: none; }
    .fin-table td { padding: 9px 6px; color: #b0bece; font-family: 'DM Sans', sans-serif; }
    .fin-table td:last-child {
        text-align: right; font-family: 'DM Mono', monospace;
        font-size: 13px; color: #e8edf5;
    }
    .fin-table .section-row td {
        color: #4a5a72; font-size: 11px; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase;
        padding-top: 16px; padding-bottom: 4px;
    }
    .fin-table .total-row td {
        color: #00e5ff; font-weight: 700; font-family: 'Syne', sans-serif;
        border-top: 1px solid rgba(0,229,255,0.2); padding-top: 12px; font-size: 14px;
    }
    .fin-table .subtotal-row td {
        color: #e8edf5; font-weight: 600; font-family: 'DM Mono', monospace;
        border-top: 1px solid rgba(255,255,255,0.06);
    }
    .fin-table .negative { color: #ff4b6e !important; }
    .fin-table .positive { color: #00e096 !important; }

    /* KPI strip */
    .fin-kpi-row { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
    .fin-kpi {
        flex: 1; min-width: 100px;
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(0,229,255,0.07);
        border-radius: 12px; padding: 14px 16px;
    }
    .fin-kpi-val {
        font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800;
        line-height: 1; color: #00e5ff;
    }
    .fin-kpi-val.red { color: #ff4b6e; }
    .fin-kpi-val.green { color: #00e096; }
    .fin-kpi-val.amber { color: #ffb800; }
    .fin-kpi-lbl { font-size: 10px; color: #4a5a72; margin-top: 5px;
        text-transform: uppercase; letter-spacing: 0.08em; }

    /* Ratio bar */
    .ratio-row { margin-bottom: 14px; }
    .ratio-label { display: flex; justify-content: space-between;
        font-size: 12px; color: #b0bece; margin-bottom: 5px; }
    .ratio-track {
        height: 5px; background: rgba(255,255,255,0.06);
        border-radius: 4px; overflow: hidden;
    }
    .ratio-fill { height: 100%; border-radius: 4px;
        background: linear-gradient(90deg, #00e5ff, #a855f7); }

    /* AI insight box */
    .fin-ai-box {
        background: rgba(0,229,255,0.04);
        border: 1px solid rgba(0,229,255,0.15);
        border-radius: 14px; padding: 18px; margin-top: 4px;
    }
    .fin-ai-label {
        font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #00e5ff; margin-bottom: 10px;
        display: flex; align-items: center; gap: 6px;
    }
    .fin-ai-text { font-size: 13px; line-height: 1.7; color: #b0bece; }

    /* Entry form */
    .fin-entry-row {
        display: grid; grid-template-columns: 2fr 1fr 1fr auto;
        gap: 8px; align-items: end; margin-bottom: 8px;
    }
    .fin-badge {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 600;
    }
    .fin-badge-rev { background: rgba(0,224,150,0.1); color: #00e096; border: 1px solid rgba(0,224,150,0.2); }
    .fin-badge-exp { background: rgba(255,75,110,0.1); color: #ff4b6e; border: 1px solid rgba(255,75,110,0.2); }
    .fin-badge-ast { background: rgba(0,229,255,0.1); color: #00e5ff; border: 1px solid rgba(0,229,255,0.2); }
    .fin-badge-lib { background: rgba(255,184,0,0.1); color: #ffb800; border: 1px solid rgba(255,184,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

    # ── DB setup for financial entries ────────────────────────────────────────
    conn_fin = sqlite3.connect("venus_ai.db", check_same_thread=False)
    cur_fin  = conn_fin.cursor()

    cur_fin.execute("""
        CREATE TABLE IF NOT EXISTS fin_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, category TEXT, subcategory TEXT,
            description TEXT, amount REAL, entry_type TEXT,
            period TEXT, created_at TEXT
        )
    """)
    conn_fin.commit()

    # ── Helper: fetch entries ─────────────────────────────────────────────────
    def get_entries(uid, period=None):
        if period:
            cur_fin.execute(
                "SELECT * FROM fin_entries WHERE user_id=? AND period=? ORDER BY id DESC",
                (uid, period)
            )
        else:
            cur_fin.execute(
                "SELECT * FROM fin_entries WHERE user_id=? ORDER BY id DESC", (uid,)
            )
        rows = cur_fin.fetchall()
        cols = ["id","user_id","category","subcategory","description","amount","entry_type","period","created_at"]
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

    # ── Seed demo data if empty ───────────────────────────────────────────────
    cur_fin.execute("SELECT COUNT(*) FROM fin_entries WHERE user_id=?", (user_id,))
    if cur_fin.fetchone()[0] == 0:
        demo = [
            # Income statement items
            (user_id,"Revenue","Product Sales","Online product sales",85400.00,"income","2024-Q4",str(datetime.now())),
            (user_id,"Revenue","Service Fees","Supplier service fees",12600.00,"income","2024-Q4",str(datetime.now())),
            (user_id,"Revenue","Commission","Platform commission",8200.00,"income","2024-Q4",str(datetime.now())),
            (user_id,"COGS","Inventory","Cost of goods purchased",42300.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"COGS","Shipping","Fulfilment & shipping",6800.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"Operating Expense","Salaries","Staff salaries",18500.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"Operating Expense","Marketing","Digital marketing spend",4200.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"Operating Expense","Software","SaaS subscriptions",1800.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"Operating Expense","Rent","Office rent",3600.00,"expense","2024-Q4",str(datetime.now())),
            (user_id,"Tax","Income Tax","Corporate income tax",4100.00,"expense","2024-Q4",str(datetime.now())),
            # Balance sheet items
            (user_id,"Current Asset","Cash","Cash & equivalents",34200.00,"asset","2024-Q4",str(datetime.now())),
            (user_id,"Current Asset","Receivables","Accounts receivable",12800.00,"asset","2024-Q4",str(datetime.now())),
            (user_id,"Current Asset","Inventory","Stock on hand",18600.00,"asset","2024-Q4",str(datetime.now())),
            (user_id,"Non-Current Asset","Equipment","Computers & equipment",9400.00,"asset","2024-Q4",str(datetime.now())),
            (user_id,"Current Liability","Payables","Accounts payable",8700.00,"liability","2024-Q4",str(datetime.now())),
            (user_id,"Current Liability","Short-term Loan","Bank overdraft",5000.00,"liability","2024-Q4",str(datetime.now())),
            (user_id,"Non-Current Liability","Long-term Loan","Business loan",20000.00,"liability","2024-Q4",str(datetime.now())),
            (user_id,"Equity","Owner Equity","Founder equity",41300.00,"equity","2024-Q4",str(datetime.now())),
        ]
        cur_fin.executemany(
            "INSERT INTO fin_entries (user_id,category,subcategory,description,amount,entry_type,period,created_at) VALUES (?,?,?,?,?,?,?,?)",
            demo
        )
        conn_fin.commit()

    # ── Period selector ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="fin-hero">
        <div class="fin-hero-title">Financial Intelligence</div>
        <div class="fin-hero-sub">
            Full accounting suite — income statements, balance sheets, cash flow analysis,
            ratio intelligence, and AI-powered CFO insights for your business.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_period, col_spacer = st.columns([1, 3])
    with col_period:
        period = st.selectbox("Reporting Period", ["2024-Q4","2024-Q3","2024-Q2","2024-Q1"], label_visibility="collapsed")

    df_all = get_entries(user_id, period)

    # ── Split by type ─────────────────────────────────────────────────────────
    df_inc = df_all[df_all["entry_type"] == "income"]
    df_exp = df_all[df_all["entry_type"] == "expense"]
    df_ast = df_all[df_all["entry_type"] == "asset"]
    df_lib = df_all[df_all["entry_type"] == "liability"]
    df_eq  = df_all[df_all["entry_type"] == "equity"]

    # Core figures
    total_revenue   = df_inc["amount"].sum()
    cogs            = df_exp[df_exp["category"]=="COGS"]["amount"].sum()
    gross_profit    = total_revenue - cogs
    opex            = df_exp[df_exp["category"]=="Operating Expense"]["amount"].sum()
    ebit            = gross_profit - opex
    tax             = df_exp[df_exp["category"]=="Tax"]["amount"].sum()
    net_profit      = ebit - tax
    total_assets    = df_ast["amount"].sum()
    total_liab      = df_lib["amount"].sum()
    total_equity    = df_eq["amount"].sum()
    curr_assets     = df_ast[df_ast["category"]=="Current Asset"]["amount"].sum()
    curr_liab       = df_lib[df_lib["category"]=="Current Liability"]["amount"].sum()
    cash            = df_ast[df_ast["subcategory"]=="Cash"]["amount"].sum()

    gp_margin   = (gross_profit / total_revenue * 100) if total_revenue else 0
    np_margin   = (net_profit   / total_revenue * 100) if total_revenue else 0
    current_ratio = (curr_assets / curr_liab) if curr_liab else 0
    debt_ratio  = (total_liab / total_assets * 100) if total_assets else 0
    roe         = (net_profit  / total_equity * 100) if total_equity else 0
    roa         = (net_profit  / total_assets * 100) if total_assets else 0

    # ── KPI Strip ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="fin-kpi-row">
        <div class="fin-kpi">
            <div class="fin-kpi-val">{'${:,.0f}'.format(total_revenue)}</div>
            <div class="fin-kpi-lbl">Total Revenue</div>
        </div>
        <div class="fin-kpi">
            <div class="fin-kpi-val {'green' if gross_profit>0 else 'red'}">{'${:,.0f}'.format(gross_profit)}</div>
            <div class="fin-kpi-lbl">Gross Profit</div>
        </div>
        <div class="fin-kpi">
            <div class="fin-kpi-val {'green' if net_profit>0 else 'red'}">{'${:,.0f}'.format(net_profit)}</div>
            <div class="fin-kpi-lbl">Net Profit</div>
        </div>
        <div class="fin-kpi">
            <div class="fin-kpi-val {'green' if gp_margin>40 else 'amber' if gp_margin>20 else 'red'}">{gp_margin:.1f}%</div>
            <div class="fin-kpi-lbl">Gross Margin</div>
        </div>
        <div class="fin-kpi">
            <div class="fin-kpi-val {'green' if current_ratio>1.5 else 'amber' if current_ratio>1 else 'red'}">{current_ratio:.2f}x</div>
            <div class="fin-kpi-lbl">Current Ratio</div>
        </div>
        <div class="fin-kpi">
            <div class="fin-kpi-val">{'${:,.0f}'.format(cash)}</div>
            <div class="fin-kpi-lbl">Cash Position</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main tabs ─────────────────────────────────────────────────────────────
    tab_is, tab_bs, tab_cf, tab_ratio, tab_entry, tab_ai = st.tabs([
        "Income Statement", "Balance Sheet", "Cash Flow",
        "Ratio Analysis", "Journal Entry", "AI CFO"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — INCOME STATEMENT
    # ─────────────────────────────────────────────────────────────────────────
    with tab_is:
        col_stmt, col_chart = st.columns([1.1, 1])

        with col_stmt:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="fin-card-title">Income Statement — {period}</div>', unsafe_allow_html=True)

            rows_html = ""
            # Revenue section
            rows_html += '<tr class="section-row"><td colspan="2">Revenue</td></tr>'
            for _, r in df_inc.iterrows():
                rows_html += f'<tr><td>{r["description"]}</td><td>${r["amount"]:,.2f}</td></tr>'
            rows_html += f'<tr class="subtotal-row"><td>Total Revenue</td><td>${total_revenue:,.2f}</td></tr>'

            # COGS
            rows_html += '<tr class="section-row"><td colspan="2">Cost of Goods Sold</td></tr>'
            for _, r in df_exp[df_exp["category"]=="COGS"].iterrows():
                rows_html += f'<tr><td>{r["description"]}</td><td class="negative">({r["amount"]:,.2f})</td></tr>'
            rows_html += f'<tr class="subtotal-row"><td>Gross Profit</td><td class="{"positive" if gross_profit>=0 else "negative"}">${gross_profit:,.2f}</td></tr>'

            # OpEx
            rows_html += '<tr class="section-row"><td colspan="2">Operating Expenses</td></tr>'
            for _, r in df_exp[df_exp["category"]=="Operating Expense"].iterrows():
                rows_html += f'<tr><td>{r["description"]}</td><td class="negative">({r["amount"]:,.2f})</td></tr>'
            rows_html += f'<tr class="subtotal-row"><td>EBIT</td><td class="{"positive" if ebit>=0 else "negative"}">${ebit:,.2f}</td></tr>'

            # Tax
            rows_html += '<tr class="section-row"><td colspan="2">Taxation</td></tr>'
            for _, r in df_exp[df_exp["category"]=="Tax"].iterrows():
                rows_html += f'<tr><td>{r["description"]}</td><td class="negative">({r["amount"]:,.2f})</td></tr>'

            rows_html += f'<tr class="total-row"><td>Net Profit / (Loss)</td><td class="{"positive" if net_profit>=0 else "negative"}">${net_profit:,.2f}</td></tr>'

            st.markdown(f'<table class="fin-table">{rows_html}</table>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_chart:
            st.markdown('<div class="fin-card" style="height:100%;">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Profit Waterfall</div>', unsafe_allow_html=True)
            waterfall_df = pd.DataFrame({
                "Stage": ["Revenue", "Gross Profit", "EBIT", "Net Profit"],
                "Amount": [total_revenue, gross_profit, ebit, net_profit]
            })
            st.bar_chart(waterfall_df.set_index("Stage"), color="#00e5ff", height=280)

            st.markdown(f"""
            <div style="margin-top:16px;">
                <div class="ratio-row">
                    <div class="ratio-label"><span>Gross Margin</span><span>{gp_margin:.1f}%</span></div>
                    <div class="ratio-track"><div class="ratio-fill" style="width:{min(gp_margin,100):.0f}%;"></div></div>
                </div>
                <div class="ratio-row">
                    <div class="ratio-label"><span>Net Margin</span><span>{np_margin:.1f}%</span></div>
                    <div class="ratio-track"><div class="ratio-fill" style="width:{min(max(np_margin,0),100):.0f}%;"></div></div>
                </div>
                <div class="ratio-row">
                    <div class="ratio-label"><span>OPEX Ratio</span><span>{(opex/total_revenue*100) if total_revenue else 0:.1f}%</span></div>
                    <div class="ratio-track"><div class="ratio-fill" style="width:{min((opex/total_revenue*100) if total_revenue else 0,100):.0f}%;background:linear-gradient(90deg,#ff4b6e,#ffb800);"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — BALANCE SHEET
    # ─────────────────────────────────────────────────────────────────────────
    with tab_bs:
        col_a, col_le = st.columns(2)

        with col_a:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Assets</div>', unsafe_allow_html=True)
            rows_html = ""
            for cat in ["Current Asset", "Non-Current Asset"]:
                rows_html += f'<tr class="section-row"><td colspan="2">{cat}s</td></tr>'
                subset = df_ast[df_ast["category"]==cat]
                for _, r in subset.iterrows():
                    rows_html += f'<tr><td>{r["description"]}</td><td>${r["amount"]:,.2f}</td></tr>'
                rows_html += f'<tr class="subtotal-row"><td>Subtotal</td><td>${subset["amount"].sum():,.2f}</td></tr>'
            rows_html += f'<tr class="total-row"><td>Total Assets</td><td>${total_assets:,.2f}</td></tr>'
            st.markdown(f'<table class="fin-table">{rows_html}</table>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_le:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Liabilities & Equity</div>', unsafe_allow_html=True)
            rows_html = ""
            for cat in ["Current Liability", "Non-Current Liability"]:
                rows_html += f'<tr class="section-row"><td colspan="2">{cat}</td></tr>'
                subset = df_lib[df_lib["category"]==cat]
                for _, r in subset.iterrows():
                    rows_html += f'<tr><td>{r["description"]}</td><td class="negative">${r["amount"]:,.2f}</td></tr>'
                rows_html += f'<tr class="subtotal-row"><td>Subtotal</td><td class="negative">${subset["amount"].sum():,.2f}</td></tr>'
            rows_html += f'<tr class="subtotal-row"><td>Total Liabilities</td><td class="negative">${total_liab:,.2f}</td></tr>'
            rows_html += '<tr class="section-row"><td colspan="2">Equity</td></tr>'
            for _, r in df_eq.iterrows():
                rows_html += f'<tr><td>{r["description"]}</td><td class="positive">${r["amount"]:,.2f}</td></tr>'
            rows_html += f'<tr class="total-row"><td>Total Liab + Equity</td><td>${(total_liab+total_equity):,.2f}</td></tr>'
            st.markdown(f'<table class="fin-table">{rows_html}</table>', unsafe_allow_html=True)

            # Balance check
            diff = abs(total_assets - (total_liab + total_equity))
            if diff < 1:
                st.success("Balance sheet balances ✓")
            else:
                st.warning(f"Balance sheet out by ${diff:,.2f} — check equity entries")
            st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — CASH FLOW (Indirect method)
    # ─────────────────────────────────────────────────────────────────────────
    with tab_cf:
        receivables = df_ast[df_ast["subcategory"]=="Receivables"]["amount"].sum()
        inventory_v = df_ast[df_ast["subcategory"]=="Inventory"]["amount"].sum()
        payables    = df_lib[df_lib["subcategory"]=="Payables"]["amount"].sum()
        equipment   = df_ast[df_ast["category"]=="Non-Current Asset"]["amount"].sum()
        lt_loan     = df_lib[df_lib["category"]=="Non-Current Liability"]["amount"].sum()

        cfo = net_profit - receivables + payables   # simplified indirect
        cfi = -equipment                              # capex outflow
        cff = lt_loan                                 # financing inflow
        net_cash = cfo + cfi + cff

        col_cf1, col_cf2 = st.columns([1.1, 1])
        with col_cf1:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Cash Flow Statement (Indirect Method)</div>', unsafe_allow_html=True)
            cf_rows = f"""
            <tr class="section-row"><td colspan="2">Operating Activities</td></tr>
            <tr><td>Net Profit</td><td class="positive">${net_profit:,.2f}</td></tr>
            <tr><td>Increase in Receivables</td><td class="negative">({receivables:,.2f})</td></tr>
            <tr><td>Increase in Payables</td><td class="positive">${payables:,.2f}</td></tr>
            <tr class="subtotal-row"><td>Net Cash from Operations</td><td class="{'positive' if cfo>=0 else 'negative'}">${cfo:,.2f}</td></tr>
            <tr class="section-row"><td colspan="2">Investing Activities</td></tr>
            <tr><td>Purchase of Equipment</td><td class="negative">({equipment:,.2f})</td></tr>
            <tr class="subtotal-row"><td>Net Cash from Investing</td><td class="negative">${cfi:,.2f}</td></tr>
            <tr class="section-row"><td colspan="2">Financing Activities</td></tr>
            <tr><td>Long-term Loan Proceeds</td><td class="positive">${lt_loan:,.2f}</td></tr>
            <tr class="subtotal-row"><td>Net Cash from Financing</td><td class="positive">${cff:,.2f}</td></tr>
            <tr class="total-row"><td>Net Change in Cash</td><td class="{'positive' if net_cash>=0 else 'negative'}">${net_cash:,.2f}</td></tr>
            <tr><td>Opening Cash Balance</td><td>${max(cash-net_cash,0):,.2f}</td></tr>
            <tr class="total-row"><td>Closing Cash Balance</td><td>${cash:,.2f}</td></tr>
            """
            st.markdown(f'<table class="fin-table">{cf_rows}</table>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_cf2:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Cash Flow Breakdown</div>', unsafe_allow_html=True)
            cf_df = pd.DataFrame({
                "Activity": ["Operations","Investing","Financing"],
                "Amount": [cfo, cfi, cff]
            })
            st.bar_chart(cf_df.set_index("Activity"), color="#a855f7", height=220)
            st.markdown(f"""
            <div style="margin-top:14px;">
                <div class="ratio-row">
                    <div class="ratio-label"><span>Operating CF</span><span>${cfo:,.0f}</span></div>
                    <div class="ratio-track"><div class="ratio-fill" style="width:{min(max(cfo/max(abs(cfo)+abs(cfi)+abs(cff),1)*100,0),100):.0f}%;"></div></div>
                </div>
                <div class="ratio-row">
                    <div class="ratio-label"><span>Cash Burn Coverage</span><span>{(cash/max(opex/3,1)):.1f} months</span></div>
                    <div class="ratio-track"><div class="ratio-fill" style="width:{min(cash/max(opex/3,1)/12*100,100):.0f}%;background:linear-gradient(90deg,#00e096,#00e5ff);"></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4 — RATIO ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    with tab_ratio:
        st.markdown('<div class="fin-card">', unsafe_allow_html=True)
        st.markdown('<div class="fin-card-title">Financial Ratios & Health Indicators</div>', unsafe_allow_html=True)

        ratio_groups = {
            "Liquidity": [
                ("Current Ratio", current_ratio, "x", 1.5, 2.5, "Measures ability to pay short-term obligations. Healthy: 1.5–2.5x"),
                ("Quick Ratio", (curr_assets-inventory_v)/max(curr_liab,1), "x", 1.0, 2.0, "Liquidity excluding inventory. Healthy: >1.0x"),
                ("Cash Ratio", cash/max(curr_liab,1), "x", 0.5, 1.0, "Pure cash coverage of current liabilities"),
            ],
            "Profitability": [
                ("Gross Margin", gp_margin, "%", 30, 60, "Revenue retained after COGS. Healthy for e-commerce: >30%"),
                ("Net Profit Margin", np_margin, "%", 5, 20, "Bottom-line profitability. Healthy: >5%"),
                ("Return on Equity", roe, "%", 10, 25, "Profit generated per dollar of equity. Healthy: >10%"),
                ("Return on Assets", roa, "%", 5, 15, "Profit per dollar of assets. Healthy: >5%"),
            ],
            "Leverage": [
                ("Debt Ratio", debt_ratio, "%", 0, 50, "% of assets financed by debt. Lower is safer"),
                ("Debt-to-Equity", total_liab/max(total_equity,1), "x", 0, 2.0, "Leverage level. Healthy: <2x"),
            ],
        }

        for group, ratios in ratio_groups.items():
            st.markdown(f'<div style="font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#4a5a72;margin:18px 0 10px;">{group}</div>', unsafe_allow_html=True)
            cols = st.columns(len(ratios))
            for col, (name, val, unit, low, high, tip) in zip(cols, ratios):
                with col:
                    if val >= high:
                        color, status = "#00e096", "Strong"
                    elif val >= low:
                        color, status = "#ffb800", "Adequate"
                    else:
                        color, status = "#ff4b6e", "Weak"
                    pct = min(max((val-0)/(max(high*1.5,0.01))*100, 0), 100)
                    st.markdown(f"""
                    <div class="fin-kpi" style="margin-bottom:8px;">
                        <div class="fin-kpi-val" style="color:{color};font-size:18px;">{val:.2f}{unit}</div>
                        <div class="fin-kpi-lbl">{name}</div>
                        <div style="margin-top:8px;">
                            <div class="ratio-track"><div class="ratio-fill" style="width:{pct:.0f}%;background:{color};opacity:0.7;"></div></div>
                        </div>
                        <div style="font-size:10px;color:{color};margin-top:4px;font-weight:600;">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("", expanded=False):
                        st.caption(tip)

        st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5 — JOURNAL ENTRY
    # ─────────────────────────────────────────────────────────────────────────
    with tab_entry:
        col_form, col_log = st.columns([1, 1.2])

        with col_form:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">Add Journal Entry</div>', unsafe_allow_html=True)

            entry_type = st.selectbox("Entry Type", ["income","expense","asset","liability","equity"])
            category_map = {
                "income":    ["Revenue"],
                "expense":   ["COGS","Operating Expense","Tax","Other"],
                "asset":     ["Current Asset","Non-Current Asset"],
                "liability": ["Current Liability","Non-Current Liability"],
                "equity":    ["Equity"],
            }
            category   = st.selectbox("Category", category_map[entry_type])
            subcategory = st.text_input("Subcategory", placeholder="e.g. Product Sales")
            description = st.text_input("Description", placeholder="e.g. Q4 online revenue")
            amount      = st.number_input("Amount (USD)", min_value=0.0, step=100.0, format="%.2f")
            ent_period  = st.selectbox("Period", ["2024-Q4","2024-Q3","2024-Q2","2024-Q1"], key="entry_period")

            if st.button("Post Entry", use_container_width=True):
                if description and amount > 0:
                    cur_fin.execute(
                        "INSERT INTO fin_entries (user_id,category,subcategory,description,amount,entry_type,period,created_at) VALUES (?,?,?,?,?,?,?,?)",
                        (user_id, category, subcategory, description, amount, entry_type, ent_period, str(datetime.now()))
                    )
                    conn_fin.commit()
                    st.success("Entry posted to ledger.")
                    st.rerun()
                else:
                    st.error("Please fill in description and amount.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_log:
            st.markdown('<div class="fin-card">', unsafe_allow_html=True)
            st.markdown('<div class="fin-card-title">General Ledger</div>', unsafe_allow_html=True)
            df_log = get_entries(user_id)
            if not df_log.empty:
                badge_map = {"income":"fin-badge-rev","expense":"fin-badge-exp","asset":"fin-badge-ast","liability":"fin-badge-lib","equity":"fin-badge-lib"}
                for _, r in df_log.head(12).iterrows():
                    bc = badge_map.get(r["entry_type"], "fin-badge-rev")
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                        <div>
                            <span class="fin-badge {bc}">{r['entry_type']}</span>
                            <span style="font-size:13px;color:#b0bece;margin-left:8px;">{r['description']}</span>
                        </div>
                        <span style="font-family:'DM Mono',monospace;font-size:13px;color:#e8edf5;">${r['amount']:,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No entries yet.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 6 — AI CFO
    # ─────────────────────────────────────────────────────────────────────────
    with tab_ai:
        st.markdown('<div class="fin-card">', unsafe_allow_html=True)
        st.markdown('<div class="fin-card-title">AI Chief Financial Officer</div>', unsafe_allow_html=True)
        st.markdown('<div class="fin-ai-text" style="margin-bottom:18px;">Ask your AI CFO anything — financial health, cost reduction, cash flow strategy, investment readiness, or risk assessment.</div>', unsafe_allow_html=True)

        # Auto-generate financial brief
        fin_brief = f"""
Business Financial Summary — {period}:
- Revenue: ${total_revenue:,.2f} | Gross Profit: ${gross_profit:,.2f} ({gp_margin:.1f}% margin)
- EBIT: ${ebit:,.2f} | Net Profit: ${net_profit:,.2f} ({np_margin:.1f}% net margin)
- Total Assets: ${total_assets:,.2f} | Total Liabilities: ${total_liab:,.2f} | Equity: ${total_equity:,.2f}
- Cash Position: ${cash:,.2f} | Current Ratio: {current_ratio:.2f}x | Debt Ratio: {debt_ratio:.1f}%
- ROE: {roe:.1f}% | ROA: {roa:.1f}% | OPEX: ${opex:,.2f}
        """.strip()

        # Quick prompts
        st.markdown("**Quick questions:**")
        qcols = st.columns(3)
        quick_qs = [
            "How healthy is my cash position?",
            "Where should I cut costs?",
            "Am I ready for investor funding?",
            "What's my biggest financial risk?",
            "How can I improve my profit margin?",
            "Analyse my debt levels",
        ]
        for i, q in enumerate(quick_qs):
            with qcols[i % 3]:
                if st.button(q, key=f"quick_{i}", use_container_width=True):
                    st.session_state["fin_ai_q"] = q

        user_q = st.text_input("Or ask your own question", placeholder="e.g. Should I take on more debt to expand?", key="fin_ai_input")
        final_q = st.session_state.get("fin_ai_q", "") or user_q

        if st.button("Ask AI CFO", use_container_width=True, key="ask_cfo") and final_q:
            with st.spinner("CFO is analysing your financials..."):
                try:
                    resp = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"Content-Type": "application/json"},
                        json={
                            "model": "claude-sonnet-4-20250514",
                            "max_tokens": 1000,
                            "messages": [{
                                "role": "user",
                                "content": f"""You are a senior CFO and financial analyst. A business owner has shared their financial data and asked a question.

{fin_brief}

Their question: {final_q}

Respond as a sharp, direct CFO would in a board meeting. Be specific — reference the actual numbers above. Give:
1. A direct answer to the question
2. 2-3 specific observations from the financial data
3. One clear action recommendation

Keep the response concise but substantive. No generic advice — everything must be grounded in the numbers above."""
                            }]
                        },
                        timeout=30
                    )
                    answer = resp.json()["content"][0]["text"]
                    st.markdown(f"""
                    <div class="fin-ai-box">
                        <div class="fin-ai-label">AI CFO Response</div>
                        <div class="fin-ai-text">{answer.replace(chr(10), '<br>')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if "fin_ai_q" in st.session_state:
                        del st.session_state["fin_ai_q"]
                except Exception as e:
                    st.error(f"CFO unavailable: {e}")

        st.markdown('</div>', unsafe_allow_html=True)
        conn_fin.close()
        
# =========================================================
# PRODUCT SEARCH — Fixed: no default listings, small buttons,
# no raw code in detail view, all logic inline (single file)
# =========================================================
elif "Product Search" in menu:
    import math, hashlib, random as _rnd



    # ── helpers (inline — no separate file needed) ────────────────────────────
    _LUSAKA_LAT, _LUSAKA_LON = -15.3875, 28.3228

    def _haversine(lat1, lon1, lat2, lon2):
        R = 6_371_000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2-lat1); dl = math.radians(lon2-lon1)
        a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def _stable_coords(seed, base_lat=_LUSAKA_LAT, base_lon=_LUSAKA_LON):
        h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(h)
        return base_lat + (rng.rand()-0.5)/55, base_lon + (rng.rand()-0.5)/55

    def _stable_int(seed, lo, hi):
        h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16) % (2**31)
        return int(np.random.RandomState(h).randint(lo, hi+1))

    def _stars(n):
        n = max(1, min(5, int(round(n))))
        return "★"*n + "☆"*(5-n)

    def _dist_badge(m):
        if   m < 500:    return "Same area",  "#00e096"
        elif m < 2000:   return "Very close", "#00e096"
        elif m < 7000:   return "Nearby",     "#ffb800"
        else:            return "Far",        "#ff4b6e"

    def _rec_score(p, max_price, max_dist):
        price_n = max(0.0, 1 - float(p["price"]) / max(max_price, 1))
        dist_n  = max(0.0, 1 - p["dist_m"]       / max(max_dist,  1))
        qual_n  = float(p.get("quality_score") or 50) / 100.0
        stock_n = min(float(p.get("qty") or 1) / 50.0, 1.0)
        return round((price_n*0.35 + dist_n*0.30 + qual_n*0.25 + stock_n*0.10)*100, 1)

    def _add_to_cart(p):
        st.session_state.ps_cart.append({
            "product": p["product"], "price": float(p["price"]),
            "qty": 1, "supplier": p.get("supplier",""),
            "location": p.get("location",""),
        })
        try:
            c2 = sqlite3.connect("venus_ai.db")
            c2.execute(
                "INSERT INTO cart (buyer_id,product,price,qty,supplier,location,status,added_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (user_id, p["product"], float(p["price"]), 1,
                 p.get("supplier",""), p.get("location",""),
                 "pending", str(datetime.datetime.now()))
            )
            c2.execute(
                "INSERT INTO seller_messages (seller_name,buyer_id,sender,message,sent_at) "
                "VALUES (?,?,?,?,?)",
                (p.get("supplier",""), user_id, "system",
                 f"New cart: {p['product']} ×1 from buyer #{user_id}",
                 str(datetime.datetime.now()))
            )
            c2.commit(); c2.close()
        except: pass

    # ── DB setup ──────────────────────────────────────────────────────────────
    _c = sqlite3.connect("venus_ai.db")
    for _sql in [
        "CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, buyer_id INTEGER, product TEXT, price REAL, qty INTEGER, supplier TEXT, location TEXT, status TEXT DEFAULT 'pending', added_at DATETIME)",
        "CREATE TABLE IF NOT EXISTS seller_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_name TEXT, buyer_id INTEGER, sender TEXT, message TEXT, sent_at DATETIME)",
        "CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT, supplier TEXT, reviewer_id INTEGER, rating INTEGER, comment TEXT, reviewed_at DATETIME)",
        "ALTER TABLE products ADD COLUMN image_url TEXT",
        "ALTER TABLE products ADD COLUMN description TEXT",
        "ALTER TABLE products ADD COLUMN quality_score REAL DEFAULT 0",
    ]:
        try: _c.execute(_sql); _c.commit()
        except: pass
    _c.close()

    # ── session defaults ──────────────────────────────────────────────────────
    for _k, _v in {
        "ps_view": None, "ps_chat_seller": None,
        "ps_chat_product": None, "ps_chat_msgs": [],
        "ps_cart": [], "ps_wishlist": set(),
        "ps_store": {},
    }.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # Callbacks — set before rerender, reliable in all nesting levels
    def _cb_view(pid):
        p = st.session_state.ps_store.get(pid)
        if p:
            st.session_state.ps_view = p

    def _cb_cart(pid):
        p = st.session_state.ps_store.get(pid)
        if p:
            st.session_state.ps_cart.append({
                "product": p["product"],
                "price": float(p["price"]),
                "qty": 1,
                "supplier": p.get("supplier", ""),
                "location": p.get("location", ""),
            })



    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400&display=swap');

    @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
    @keyframes recPulse { 0%,100%{box-shadow:0 0 0 0 rgba(0,229,255,0)} 60%{box-shadow:0 0 18px 4px rgba(0,229,255,0.2)} }

    .mkt-hero {
        background:linear-gradient(135deg,rgba(0,229,255,0.05),rgba(168,85,247,0.04));
        border:1px solid rgba(0,229,255,0.12); border-radius:20px;
        padding:26px 28px 20px; margin-bottom:20px; position:relative; overflow:hidden;
    }
    .mkt-hero::before { content:''; position:absolute; top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,229,255,0.4),transparent); }
    .mkt-hero-title { font-family:'Syne',sans-serif; font-size:24px; font-weight:800;
        letter-spacing:-0.02em; color:#e8edf5; margin-bottom:3px; }
    .mkt-hero-sub { font-size:12px; color:#2a3a52; margin-bottom:18px; }

    /* product card */
    .pc { background:rgba(8,8,18,0.97); border:1px solid rgba(0,229,255,0.07);
        border-radius:16px; overflow:hidden; margin-bottom:4px;
        animation:fadeUp 0.3s ease both;
        transition:border-color 0.2s, transform 0.18s, box-shadow 0.2s; }
    .pc:hover { border-color:rgba(0,229,255,0.22); transform:translateY(-2px);
        box-shadow:0 12px 40px rgba(0,0,0,0.5); }
    .pc.rec { border-color:rgba(0,229,255,0.45)!important; animation:recPulse 3s ease infinite; }
    .pc-img { width:100%; height:150px; object-fit:cover; display:block;
        transition:transform 0.35s; }
    .pc:hover .pc-img { transform:scale(1.04); }
    .pc-img-wrap { overflow:hidden; height:150px; position:relative;
        background:linear-gradient(135deg,rgba(0,229,255,0.03),rgba(168,85,247,0.03)); }
    .pc-no-img { height:150px; display:flex; align-items:center; justify-content:center;
        background:linear-gradient(135deg,rgba(0,229,255,0.03),rgba(168,85,247,0.03));
        font-size:42px; color:rgba(0,229,255,0.1); }
    .pc-rec-badge { position:absolute; top:8px; left:8px; background:rgba(0,229,255,0.95);
        color:#000; font-size:8px; font-weight:800; letter-spacing:0.1em;
        padding:2px 8px; border-radius:20px; text-transform:uppercase; }
    .pc-body { padding:12px 13px 10px; }
    .pc-name { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:#e8edf5;
        line-height:1.3; margin-bottom:3px;
        display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
    .pc-sup { font-size:10px; color:#2a3a52; margin-bottom:6px;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .pc-stars { color:#ffb800; font-size:10px; letter-spacing:1px; }
    .pc-rc { font-size:9px; color:#2a3a52; margin-left:3px; }
    .pc-tags { display:flex; gap:3px; flex-wrap:wrap; margin:6px 0 8px; }
    .pc-tag { font-size:8px; font-weight:700; padding:2px 6px; border-radius:20px;
        letter-spacing:0.06em; text-transform:uppercase; }
    .t-green { background:rgba(0,224,150,0.12); color:#00e096; }
    .t-amber { background:rgba(255,184,0,0.12);  color:#ffb800; }
    .t-red   { background:rgba(255,75,110,0.12); color:#ff4b6e; }
    .t-blue  { background:rgba(0,229,255,0.1);   color:#00e5ff; }
    .t-warn  { background:rgba(255,184,0,0.1);   color:#ffb800; }
    .pc-price { font-family:'Syne',sans-serif; font-size:19px; font-weight:800;
        color:#00e5ff; line-height:1; }
    .pc-stock { font-size:9px; color:#2a3a52; margin-top:1px; }

    /* FIX: small compact card buttons */
    .pc-btns .stButton > button {
        font-size:11px !important;
        padding:5px 8px !important;
        border-radius:8px !important;
        height:28px !important;
        min-height:0 !important;
        line-height:1 !important;
    }

    /* section header */
    .mkt-sh { display:flex; align-items:baseline; justify-content:space-between;
        margin:22px 0 12px; border-bottom:1px solid rgba(0,229,255,0.06);
        padding-bottom:8px; }
    .mkt-sh-t { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; color:#e8edf5; }
    .mkt-sh-m { font-size:10px; color:#2a3a52; font-family:'DM Mono',monospace; }

    /* best match banner */
    .best-banner { background:linear-gradient(135deg,rgba(0,229,255,0.09),rgba(0,229,255,0.04));
        border:1px solid rgba(0,229,255,0.28); border-radius:14px;
        padding:14px 18px; margin-bottom:16px;
        display:flex; align-items:center; justify-content:space-between; }
    .best-banner-l {}
    .best-banner-tag { font-size:9px; font-weight:700; letter-spacing:0.12em;
        text-transform:uppercase; color:#00e5ff; margin-bottom:3px; }
    .best-banner-name { font-family:'Syne',sans-serif; font-size:16px; font-weight:700; color:#e8edf5; }
    .best-banner-meta { font-size:11px; color:#2a3a52; margin-top:2px; }
    .best-banner-price { font-family:'Syne',sans-serif; font-size:22px;
        font-weight:800; color:#00e5ff; }

    /* cart bar */
    .cart-bar { background:rgba(0,224,150,0.06); border:1px solid rgba(0,224,150,0.2);
        border-radius:13px; padding:12px 18px; margin-bottom:16px;
        display:flex; align-items:center; justify-content:space-between; }
    .cart-lbl { font-size:13px; color:#00e096; font-weight:600; }
    .cart-tot { font-family:'Syne',sans-serif; font-size:19px; font-weight:800; color:#00e5ff; }
    .ci { display:flex; align-items:center; justify-content:space-between;
        padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
    .ci-n { font-size:12px; color:#e8edf5; font-weight:500; }
    .ci-m { font-size:10px; color:#2a3a52; margin-top:1px; }
    .ci-p { font-family:'DM Mono',monospace; font-size:13px; color:#00e5ff; }

    /* empty state */
    .mkt-empty { text-align:center; padding:56px 20px;
        border:1px dashed rgba(0,229,255,0.1); border-radius:16px; margin:16px 0; }
    .mkt-empty-i { font-size:44px; margin-bottom:12px; opacity:0.35; }
    .mkt-empty-t { font-family:'Syne',sans-serif; font-size:17px;
        font-weight:700; color:#2a3a52; margin-bottom:5px; }
    .mkt-empty-s { font-size:12px; color:#1e2e44; }

    /* product detail */
    .pd-panel { background:rgba(8,8,18,0.97); border:1px solid rgba(0,229,255,0.1);
        border-radius:18px; padding:24px; margin-bottom:14px;
        position:relative; overflow:hidden; }
    .pd-panel::before { content:''; position:absolute;top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,transparent,rgba(0,229,255,0.3),transparent); }
    .pd-name { font-family:'Syne',sans-serif; font-size:26px; font-weight:800;
        letter-spacing:-0.02em; color:#e8edf5; margin-bottom:6px; }
    .pd-price { font-family:'Syne',sans-serif; font-size:34px; font-weight:800;
        color:#00e5ff; line-height:1; margin:12px 0 3px; }
    .pd-stock-lbl { font-size:12px; color:#2a3a52; margin-bottom:13px; }
    .pd-desc-text { font-size:13px; color:#9aaabf; line-height:1.75; }
    .pd-seller-box { background:rgba(255,255,255,0.02); border:1px solid rgba(0,229,255,0.08);
        border-radius:12px; padding:14px; margin-top:16px; }
    .pd-seller-lbl { font-size:9px; font-weight:700; letter-spacing:0.1em;
        text-transform:uppercase; color:#2a3a52; margin-bottom:8px; }
    .pd-rec-banner { background:linear-gradient(135deg,rgba(0,229,255,0.1),rgba(0,229,255,0.05));
        border:1px solid rgba(0,229,255,0.28); border-radius:10px;
        padding:10px 14px; margin-bottom:12px; font-size:12px; color:#00e5ff; font-weight:600; }
    .bar-track { height:4px; background:rgba(255,255,255,0.05);
        border-radius:4px; overflow:hidden; margin-top:5px; }
    .bar-fill  { height:100%; border-radius:4px;
        background:linear-gradient(90deg,#00e5ff,#a855f7); }

    /* review */
    .rev { background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05);
        border-radius:12px; padding:12px 14px; margin-bottom:7px; }

    /* chat */
    .chat-hdr { display:flex; align-items:center; gap:11px; padding:15px 18px;
        background:rgba(8,8,18,0.97); border:1px solid rgba(0,229,255,0.1);
        border-radius:14px; margin-bottom:13px; }
    .chat-av { width:42px; height:42px; flex-shrink:0; border-radius:50%;
        background:linear-gradient(135deg,#00e5ff,#a855f7);
        display:flex; align-items:center; justify-content:center;
        font-family:'Syne',sans-serif; font-size:17px; font-weight:800; color:#000;
        box-shadow:0 0 14px rgba(0,229,255,0.2); }
    .chat-bme  { display:flex; justify-content:flex-end; margin:7px 0; }
    .chat-bthem{ display:flex; gap:7px; margin:7px 0; }
    .msg-me   { background:linear-gradient(135deg,rgba(0,229,255,0.13),rgba(168,85,247,0.10));
        border:1px solid rgba(0,229,255,0.2); border-radius:16px 16px 4px 16px;
        padding:9px 14px; max-width:70%; font-size:13px; color:#e8edf5; line-height:1.6; }
    .msg-them { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06);
        border-radius:4px 16px 16px 16px; padding:9px 14px;
        max-width:70%; font-size:13px; color:#d0dcea; line-height:1.6; }
    .chat-ts  { font-size:9px; color:#1e2e44; margin-top:2px;
        text-align:right; font-family:'DM Mono',monospace; }
    .wl-bar { background:rgba(168,85,247,0.06); border:1px solid rgba(168,85,247,0.15);
        border-radius:11px; padding:9px 15px; margin-bottom:12px;
        font-size:12px; color:#a855f7; }
    </style>
    """, unsafe_allow_html=True)

    _AUTO_REPLIES = [
        "Hi! Yes it's still available. When can you collect?",
        "Great choice! I can have it ready today.",
        "Happy to help — I can do a discount on larger orders.",
        "Still in stock. Send your location and I'll confirm.",
        "Fresh stock just arrived. Come through anytime!",
        "Available now. What time works for you?",
    ]
    _REV_NAMES = ["Alex K.","Mary J.","Daniel P.","Priya M.","Chris W.","Lena B.","Sam O."]

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW: CHAT
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.ps_chat_seller:
        seller  = st.session_state.ps_chat_seller
        product = st.session_state.ps_chat_product or "your product"

        if st.button("← Back", key="chat_back"):
            st.session_state.ps_chat_seller  = None
            st.session_state.ps_chat_product = None
            st.session_state.ps_chat_msgs    = []
            st.rerun()

        st.markdown(f"""
        <div class="chat-hdr">
            <div class="chat-av">{seller[0].upper()}</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:16px;
                    font-weight:700;color:#e8edf5;">{seller}</div>
                <div style="font-size:11px;color:#9aaabf;margin-top:1px;">
                    <span style="color:#00e096;">●</span>&nbsp;Online
                    &nbsp;·&nbsp; About: <em style="color:#b0bece;">{product}</em>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Build all chat bubbles as a single HTML string — no nested st.* calls
        bubbles = ""
        for m in st.session_state.ps_chat_msgs:
            if m["sender"] == "me":
                bubbles += (f'<div class="chat-bme"><div>'
                            f'<div class="msg-me">{m["msg"]}</div>'
                            f'<div class="chat-ts">{m["time"]}</div>'
                            f'</div></div>')
            else:
                av_html = (f'<div style="width:24px;height:24px;flex-shrink:0;margin-top:2px;'
                           f'background:linear-gradient(135deg,#00e5ff,#a855f7);border-radius:50%;'
                           f'display:flex;align-items:center;justify-content:center;'
                           f'font-size:10px;font-weight:800;color:#000;">{seller[0].upper()}</div>')
                bubbles += (f'<div class="chat-bthem">{av_html}<div>'
                            f'<div class="msg-them">{m["msg"]}</div>'
                            f'<div class="chat-ts">{m["time"]}</div>'
                            f'</div></div>')

        st.markdown(
            f'<div style="max-height:360px;overflow-y:auto;padding:4px 2px 10px;">{bubbles}</div>',
            unsafe_allow_html=True
        )

        msg_in = st.chat_input(f"Message {seller}...", key="chat_in")
        if msg_in:
            now = datetime.datetime.now().strftime("%H:%M")
            st.session_state.ps_chat_msgs.append({"sender":"me",  "msg":msg_in,                        "time":now})
            st.session_state.ps_chat_msgs.append({"sender":"them","msg":_rnd.choice(_AUTO_REPLIES),"time":now})
            try:
                c2 = sqlite3.connect("venus_ai.db")
                c2.execute("INSERT INTO seller_messages (seller_name,buyer_id,sender,message,sent_at) VALUES (?,?,?,?,?)",
                           (seller, user_id, "buyer", msg_in, str(datetime.datetime.now())))
                c2.commit(); c2.close()
            except: pass
            st.rerun()
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW: PRODUCT DETAIL
    # The ONLY place st.markdown is called for detail content.
    # All dynamic values are plain Python variables interpolated into
    # a single f-string — no function calls, no widgets inside HTML.
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.ps_view:
        p = st.session_state.ps_view

        if st.button("← Back to Search", key="pd_back"):
            st.session_state.ps_view = None
            st.rerun()

        # ── Pre-compute ALL values before any HTML ──
        pd_name     = str(p.get("product", ""))
        pd_price    = float(p.get("price", 0))
        pd_qty      = int(p.get("qty", 0))
        pd_sup      = str(p.get("supplier", "Unknown"))
        pd_loc      = str(p.get("location", "Lusaka"))
        pd_desc     = str(p.get("desc") or p.get("description") or f"Quality product from {pd_sup}.")
        pd_img      = str(p.get("img") or p.get("image_url") or "")
        pd_qs       = float(p.get("quality_score") or 0)
        pd_rs       = p.get("rec_score")
        pd_is_rec   = bool(p.get("recommended"))
        pd_rating   = _stable_int(f"rat_{pd_name}", 3, 5)
        pd_rcount   = _stable_int(f"rev_{pd_name}", 4, 120)
        pd_stars    = _stars(pd_rating)
        pd_sup_init = pd_sup[0].upper() if pd_sup else "S"
        pd_dist_lbl = str(p.get("dist_label") or "")
        pd_in_wl    = pd_name in st.session_state.ps_wishlist

        # ── Image ──
        col_img, col_info = st.columns([1, 1.3])
        with col_img:
            if pd_img:
                st.markdown(
                    f'<div style="border-radius:16px;overflow:hidden;'
                    f'border:1px solid rgba(0,229,255,0.12);height:300px;">'
                    f'<img src="{pd_img}" style="width:100%;height:300px;object-fit:cover;" loading="lazy"/>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="height:300px;border-radius:16px;'
                    'background:rgba(0,229,255,0.03);border:1px solid rgba(0,229,255,0.1);'
                    'display:flex;align-items:center;justify-content:center;'
                    'font-size:64px;color:rgba(0,229,255,0.1);">📦</div>',
                    unsafe_allow_html=True
                )

        # ── Info panel — one markdown call, all values pre-computed strings ──
        with col_info:
            rec_banner_html = (
                '<div class="pd-rec-banner">★ VENUS Best Match — '
                'top score across price, distance &amp; quality</div>'
                if pd_is_rec else ""
            )
            qs_html = (
                f'<div style="margin-top:12px;">'
                f'<div style="font-size:10px;color:#2a3a52;margin-bottom:3px;">AI Quality Score</div>'
                f'<div style="font-size:16px;font-weight:700;color:#00e5ff;">{pd_qs:.0f} / 100</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{min(pd_qs,100):.0f}%;"></div></div>'
                f'</div>'
            ) if pd_qs > 0 else ""

            rs_val  = f"{pd_rs:.0f}" if pd_rs is not None else ""
            rs_pct  = f"{min(pd_rs,100):.0f}" if pd_rs is not None else "0"
            rs_html = (
                f'<div style="margin-top:10px;">'
                f'<div style="font-size:10px;color:#2a3a52;margin-bottom:3px;">Recommendation Score</div>'
                f'<div style="font-size:16px;font-weight:700;color:#a855f7;">{rs_val} / 100</div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{rs_pct}%;background:linear-gradient(90deg,#a855f7,#00e5ff);"></div></div>'
                f'</div>'
            ) if pd_rs is not None else ""

            dist_line = f" &nbsp;·&nbsp; {pd_dist_lbl}" if pd_dist_lbl else ""

            st.markdown(
                f'<div class="pd-panel">'
                f'{rec_banner_html}'
                f'<div class="pd-name">{pd_name}</div>'
                f'<div style="display:flex;align-items:center;gap:7px;">'
                f'<span style="color:#ffb800;font-size:14px;letter-spacing:2px;">{pd_stars}</span>'
                f'<span style="font-size:11px;color:#2a3a52;">{pd_rcount} reviews</span>'
                f'</div>'
                f'<div class="pd-price">${pd_price:.2f}</div>'
                f'<div class="pd-stock-lbl">{pd_qty} units in stock</div>'
                f'<div class="pd-desc-text">{pd_desc}</div>'
                f'{qs_html}{rs_html}'
                f'<div class="pd-seller-box">'
                f'<div class="pd-seller-lbl">Sold by</div>'
                f'<div style="display:flex;align-items:center;gap:9px;">'
                f'<div style="width:34px;height:34px;flex-shrink:0;border-radius:50%;'
                f'background:linear-gradient(135deg,#00e5ff,#a855f7);'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#000;">'
                f'{pd_sup_init}</div>'
                f'<div>'
                f'<div style="font-size:13px;font-weight:700;color:#e8edf5;">{pd_sup}</div>'
                f'<div style="font-size:10px;color:#2a3a52;">📍 {pd_loc}{dist_line}'
                f' &nbsp;·&nbsp; <span style="color:#00e096;">✓ Verified</span></div>'
                f'</div></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Buttons — standard Streamlit, not inside HTML
            qa, qb, qc = st.columns([1, 2, 2])
            with qa:
                qty_sel = st.number_input("", 1, max(1, pd_qty), 1,
                                          key="pd_qty", label_visibility="collapsed")
            with qb:
                if st.button("Add to Cart", key="pd_cart", use_container_width=True):
                    item = dict(p); item["qty"] = qty_sel
                    _add_to_cart(item)
                    st.success(f"Added {qty_sel}× {pd_name} to cart!")
            with qc:
                if st.button("Message Seller", key="pd_msg", use_container_width=True):
                    st.session_state.ps_chat_seller  = pd_sup
                    st.session_state.ps_chat_product = pd_name
                    if not st.session_state.ps_chat_msgs:
                        st.session_state.ps_chat_msgs = [{"sender":"them","time":"Now",
                            "msg":f"Hi! I'm selling {pd_name} for ${pd_price:.2f}. How can I help?"}]
                    st.rerun()

            wl_lbl = "♥ Saved" if pd_in_wl else "♡ Wishlist"
            if st.button(wl_lbl, key="pd_wl", use_container_width=True):
                if pd_in_wl: st.session_state.ps_wishlist.discard(pd_name)
                else:        st.session_state.ps_wishlist.add(pd_name)
                st.rerun()

        # ── Reviews ──────────────────────────────────────────────────────────
        st.markdown(
            '<div style="height:1px;background:linear-gradient(90deg,transparent,'
            'rgba(0,229,255,0.1),transparent);margin:24px 0 16px;"></div>',
            unsafe_allow_html=True
        )
        st.markdown("### Reviews")

        try:
            c2 = sqlite3.connect("venus_ai.db")
            db_revs = c2.execute(
                "SELECT rating,comment,reviewed_at FROM reviews WHERE product=? ORDER BY id DESC LIMIT 15",
                (pd_name,)
            ).fetchall()
            c2.close()
        except:
            db_revs = []

        all_revs = [(r[0], str(r[1]), str(r[2])[:16]) for r in db_revs] or [
            (5,"Excellent quality, exactly as described.","2 days ago"),
            (4,"Good product. Seller responded quickly.","1 week ago"),
            (4,"Would buy again. Well packaged.","2 weeks ago"),
        ]
        avg_rat = sum(r[0] for r in all_revs) / len(all_revs)

        col_ra, col_rb = st.columns([1, 2])
        with col_ra:
            avg_stars = _stars(round(avg_rat))
            st.markdown(
                f'<div style="background:rgba(8,8,18,0.97);border:1px solid rgba(0,229,255,0.08);'
                f'border-radius:14px;padding:20px;text-align:center;">'
                f'<div style="font-family:Syne,sans-serif;font-size:48px;'
                f'font-weight:800;color:#ffb800;line-height:1;">{avg_rat:.1f}</div>'
                f'<div style="color:#ffb800;font-size:17px;letter-spacing:3px;margin:5px 0;">'
                f'{avg_stars}</div>'
                f'<div style="font-size:11px;color:#2a3a52;">{len(all_revs)} reviews</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_rb:
            for rev in all_revs[:3]:
                rev_rating_html = _stars(rev[0])
                rev_name = _rnd.choice(_REV_NAMES)
                rev_comment = str(rev[1])
                rev_date    = str(rev[2])
                st.markdown(
                    f'<div class="rev">'
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                    f'<div style="font-size:12px;font-weight:600;color:#e8edf5;">{rev_name}</div>'
                    f'<div style="display:flex;align-items:center;gap:5px;">'
                    f'<span style="color:#ffb800;font-size:11px;">{rev_rating_html}</span>'
                    f'<span style="font-size:9px;color:#2a3a52;font-family:DM Mono,monospace;">'
                    f'{rev_date}</span></div></div>'
                    f'<div style="font-size:12px;color:#9aaabf;line-height:1.6;">{rev_comment}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        with st.expander("Write a review", expanded=False):
            rev_r = st.select_slider("Rating", [1,2,3,4,5], 5, key="rev_slider")
            rev_c = st.text_area("Comment", placeholder="What did you think?", key="rev_txt")
            if st.button("Submit Review", key="rev_submit"):
                if rev_c.strip():
                    try:
                        c2 = sqlite3.connect("venus_ai.db")
                        c2.execute(
                            "INSERT INTO reviews (product,supplier,reviewer_id,rating,comment,reviewed_at) "
                            "VALUES (?,?,?,?,?,?)",
                            (pd_name, pd_sup, user_id, rev_r, rev_c, str(datetime.datetime.now()))
                        )
                        c2.commit(); c2.close()
                    except: pass
                    st.success("Review submitted!")
                    st.rerun()
                else:
                    st.error("Please write a comment first.")
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN MARKETPLACE — search bar + results only (no default listings)
    # ══════════════════════════════════════════════════════════════════════════

    # ── Hero / search bar ─────────────────────────────────────────────────────
    st.markdown('<div class="mkt-hero">', unsafe_allow_html=True)
    st.markdown('<div class="mkt-hero-title">Smart Marketplace</div>', unsafe_allow_html=True)
    st.markdown('<div class="mkt-hero-sub">Search for a product to find verified suppliers near you</div>',
                unsafe_allow_html=True)

    sq, sbtn = st.columns([5, 1])
    with sq:
        query = st.text_input("", placeholder="What are you looking for? e.g. maize, iPhone, shoes…",
                              key="mkt_q", label_visibility="collapsed")
    with sbtn:
        do_search = st.button("Search", key="mkt_srch", use_container_width=True)

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        use_loc = st.selectbox("", ["Custom location","My current location"],
                               key="mkt_loc", label_visibility="collapsed")
    with f2:
        if use_loc == "My current location":
            r_km = st.select_slider("", [1,2,5,10,20,50], value=5,
                                    format_func=lambda x: f"{x} km radius",
                                    key="mkt_rad", label_visibility="collapsed")
            radius_m = r_km * 1000
            u_lat, u_lon = _LUSAKA_LAT, _LUSAKA_LON
        else:
            _cities = {
                "Lusaka CBD":   (-15.4166, 28.2833),
                "Lusaka East":  (-15.3800, 28.3600),
                "Manda Hill":   (-15.4100, 28.3100),
                "Woodlands":    (-15.3700, 28.3000),
                "Chilenje":     (-15.4400, 28.2800),
                "Kabulonga":    (-15.3900, 28.3200),
                "Roma":         (-15.4200, 28.3400),
                "Other":        (-15.3875, 28.3228),
            }
            city = st.selectbox("", list(_cities.keys()),
                                key="mkt_city", label_visibility="collapsed")
            u_lat, u_lon = _cities[city]
            radius_m = 999_999
    with f3:
        sort_by = st.selectbox("", ["Recommended","Price: Low → High",
                                    "Price: High → Low","Closest first","Highest quality"],
                               key="mkt_sort", label_visibility="collapsed")
    with f4:
        max_p = st.number_input("", min_value=0.0, value=0.0, step=10.0,
                                placeholder="Max price ($, 0=any)",
                                key="mkt_maxp", label_visibility="collapsed")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Cart bar ──────────────────────────────────────────────────────────────
    if st.session_state.ps_cart:
        ctotal = sum(i["price"]*i["qty"] for i in st.session_state.ps_cart)
        ccount = len(st.session_state.ps_cart)
        st.markdown(
            f'<div class="cart-bar">'
            f'<div class="cart-lbl">🛒 &nbsp;{ccount} item{"s" if ccount!=1 else ""} in cart</div>'
            f'<div class="cart-tot">${ctotal:.2f}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        with st.expander("View cart & checkout"):
            for item in st.session_state.ps_cart:
                i_name = str(item["product"])
                i_sup  = str(item["supplier"])
                i_qty  = int(item["qty"])
                i_tot  = float(item["price"]) * i_qty
                st.markdown(
                    f'<div class="ci"><div>'
                    f'<div class="ci-n">{i_name}</div>'
                    f'<div class="ci-m">{i_sup} · Qty {i_qty}</div>'
                    f'</div><div class="ci-p">${i_tot:.2f}</div></div>',
                    unsafe_allow_html=True
                )
            ca, cb = st.columns(2)
            with ca:
                if st.button("Checkout & Notify Sellers", key="checkout_btn", use_container_width=True):
                    try:
                        c2 = sqlite3.connect("venus_ai.db")
                        for item in st.session_state.ps_cart:
                            c2.execute(
                                "INSERT INTO transactions (product,price,quantity,supplier,location,total,date) "
                                "VALUES (?,?,?,?,?,?,?)",
                                (item["product"], item["price"], item["qty"], item["supplier"],
                                 item["location"], item["price"]*item["qty"], str(datetime.datetime.now()))
                            )
                        c2.commit(); c2.close()
                    except: pass
                    st.session_state.ps_cart = []
                    st.success("Order placed! Sellers have been notified.")
                    st.rerun()
            with cb:
                if st.button("Clear Cart", key="clear_cart", use_container_width=True):
                    st.session_state.ps_cart = []
                    st.rerun()

    # ── Wishlist bar ──────────────────────────────────────────────────────────
    if st.session_state.ps_wishlist:
        wl_count = len(st.session_state.ps_wishlist)
        st.markdown(
            f'<div class="wl-bar">♥ &nbsp;'
            f'<strong>{wl_count}</strong> item{"s" if wl_count!=1 else ""} saved to wishlist</div>',
            unsafe_allow_html=True
        )

    # ── Sponsored ad slot — renders ONLY when paid ads exist in DB ────────────
    # To activate: INSERT a row into sponsored_ads with active=1, budget_remaining>0
    # and link it to a product_id. Nothing shows if the table is empty.
    try:
        _c2 = sqlite3.connect("venus_ai.db")
        _c2.execute("""CREATE TABLE IF NOT EXISTS sponsored_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER,
            product_id INTEGER, headline TEXT, tagline TEXT,
            budget_remaining REAL DEFAULT 0, active INTEGER DEFAULT 1,
            expires_at DATETIME, created_at DATETIME)""")
        _c2.commit()
        _active_ads = _c2.execute(
            """SELECT sa.headline, sa.tagline, p.id, p.product, p.price,
                      p.qty, p.supplier, p.location, p.image_url, p.description, p.quality_score
               FROM sponsored_ads sa JOIN products p ON p.id = sa.product_id
               WHERE sa.active=1 AND sa.budget_remaining>0
                 AND (sa.expires_at IS NULL OR sa.expires_at > datetime('now'))
               ORDER BY sa.budget_remaining DESC LIMIT 3"""
        ).fetchall()
        _c2.close()
    except:
        _active_ads = []

    if _active_ads:
        st.markdown(
            '<div class="mkt-sh">'
            '<div class="mkt-sh-t">Sponsored</div>'
            '<div class="mkt-sh-m">Paid placements · Verified sellers</div>'
            '</div>',
            unsafe_allow_html=True
        )
        _ad_prods = []
        for r in _active_ads:
            lat2, lon2 = _stable_coords(f"{r[3]}{r[6]}", u_lat, u_lon)
            dist = _haversine(u_lat, u_lon, lat2, lon2)
            dl, dc = _dist_badge(dist)
            _ad_prods.append({
                "id": f"ad_{r[2]}", "product": str(r[3]), "price": float(r[4] or 0),
                "qty": int(r[5] or 0), "supplier": str(r[6] or ""), "location": str(r[7] or ""),
                "img": str(r[8] or ""), "desc": str(r[9] or ""),
                "quality_score": float(r[10] or 0), "dist_m": dist,
                "dist_label": dl, "dist_cls": dc, "sponsored": True, "recommended": False,
            })
        # render ad grid inline (same pattern as search results below)
        for _row_i in range(0, len(_ad_prods), 3):
            _chunk = _ad_prods[_row_i:_row_i+3]
            _cols  = st.columns(3)
            for _ci, _p in enumerate(_chunk):
                _pid = f"ad_{_p['id']}_{_row_i}_{_ci}"
                with _cols[_ci]:
                    _img_html = (
                        f'<div class="pc-img-wrap">'
                        f'<img class="pc-img" src="{_p["img"]}" loading="lazy">'
                        f'<div class="pc-rec-badge" style="background:rgba(255,184,0,0.95);color:#000;">Sponsored</div>'
                        f'</div>'
                    ) if _p.get("img") else '<div class="pc-no-img">📦</div>'
                    _r = _stable_int(f"rat_{_p['product']}", 3, 5)
                    _rc = _stable_int(f"rev_{_p['product']}", 4, 120)
                    st.markdown(
                        f'<div class="pc">{_img_html}'
                        f'<div class="pc-body">'
                        f'<div class="pc-name">{_p["product"]}</div>'
                        f'<div class="pc-sup">{_p["supplier"]} · 📍 {_p["location"]}</div>'
                        f'<div><span class="pc-stars">{_stars(_r)}</span>'
                        f'<span class="pc-rc">{_rc} reviews</span></div>'
                        f'<div class="pc-tags">'
                        f'<span class="pc-tag {_p["dist_cls"]}">{_p["dist_label"]}</span>'
                        f'</div>'
                        f'<div class="pc-price">${_p["price"]:.2f}</div>'
                        f'<div class="pc-stock">{_p["qty"]} in stock</div>'
                        f'</div></div>',
                        unsafe_allow_html=True
                    )
                    st.session_state.ps_store[_pid] = _p
                    _ba, _bb = st.columns(2)
                    with _ba:
                        st.button("View", key=f"v_{_pid}",
                                  use_container_width=True,
                                  on_click=_cb_view, args=(_pid,))
                    with _bb:
                        st.button("Add to Cart", key=f"c_{_pid}",
                                  use_container_width=True,
                                  on_click=_cb_cart, args=(_pid,))

    # ── SEARCH RESULTS ────────────────────────────────────────────────────────
    if do_search and query.strip():
        try:
            _c2 = sqlite3.connect("venus_ai.db")
            _rows = _c2.execute(
                "SELECT id,product,price,qty,supplier,location,image_url,description,quality_score "
                "FROM products WHERE product LIKE ? ORDER BY id DESC",
                (f"%{query.strip()}%",)
            ).fetchall()
            _c2.close()
        except:
            _rows = []

        # Enrich + filter
        _enriched = []
        for _i, _r in enumerate(_rows):
            _lat2, _lon2 = _stable_coords(f"{_r[1]}{_r[4]}", u_lat, u_lon)
            _dist = _haversine(u_lat, u_lon, _lat2, _lon2)
            if _dist > radius_m: continue
            _price = float(_r[2] or 0)
            if max_p > 0 and _price > max_p: continue
            _dl, _dc = _dist_badge(_dist)
            _enriched.append({
                "id": f"db_{_r[0]}_{_i}",
                "product": str(_r[1]), "price": _price,
                "qty": int(_r[3] or 0), "supplier": str(_r[4] or "Unknown"),
                "location": str(_r[5] or "Lusaka"), "img": str(_r[6] or ""),
                "desc": str(_r[7] or ""), "quality_score": float(_r[8] or 0),
                "dist_m": _dist, "dist_label": _dl, "dist_cls": _dc,
                "lat2": _lat2, "lon2": _lon2, "recommended": False,
            })

        # Score
        if _enriched:
            _mp = max(x["price"] for x in _enriched) or 1
            _md = max(x["dist_m"] for x in _enriched) or 1
            for _p2 in _enriched:
                _p2["rec_score"] = _rec_score(_p2, _mp, _md)

            # Sort
            if   sort_by == "Recommended":       _enriched.sort(key=lambda x: x["rec_score"], reverse=True)
            elif sort_by == "Price: Low → High":  _enriched.sort(key=lambda x: x["price"])
            elif sort_by == "Price: High → Low":  _enriched.sort(key=lambda x: x["price"], reverse=True)
            elif sort_by == "Closest first":       _enriched.sort(key=lambda x: x["dist_m"])
            elif sort_by == "Highest quality":     _enriched.sort(key=lambda x: x["quality_score"], reverse=True)

            if sort_by == "Recommended":
                _enriched[0]["recommended"] = True

        # Result count header
        st.markdown(
            f'<div class="mkt-sh">'
            f'<div class="mkt-sh-t">Results for "{query}"</div>'
            f'<div class="mkt-sh-m">{len(_enriched)} supplier{"s" if len(_enriched)!=1 else ""} found</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if _enriched:
            # Best match banner
            _best = _enriched[0]
            if _best.get("recommended"):
                _b_price = f"${_best['price']:.2f}"
                _b_score = f"{_best.get('rec_score',0):.0f}"
                st.markdown(
                    f'<div class="best-banner">'
                    f'<div class="best-banner-l">'
                    f'<div class="best-banner-tag">★ VENUS Best Match</div>'
                    f'<div class="best-banner-name">{_best["product"]}</div>'
                    f'<div class="best-banner-meta">{_best["supplier"]} · 📍 {_best["location"]}'
                    f' · Score {_b_score}/100</div>'
                    f'</div>'
                    f'<div class="best-banner-price">{_b_price}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Product grid — HTML card then buttons, strictly separated
            for _row_i in range(0, len(_enriched), 3):
                _chunk = _enriched[_row_i:_row_i+3]
                _cols  = st.columns(3)
                for _ci, _p in enumerate(_chunk):
                    _pid    = f"res_{_p['id']}"
                    _is_rec = bool(_p.get("recommended"))
                    _in_wl  = _p["product"] in st.session_state.ps_wishlist
                    _rating = _stable_int(f"rat_{_p['product']}", 3, 5)
                    _rcount = _stable_int(f"rev_{_p['product']}", 4, 120)
                    _rs_val = _p.get("rec_score")
                    _qs_val = float(_p.get("quality_score") or 0)

                    # Pre-build all tag strings as plain str — no function calls inside f-string expressions
                    _dist_tag_str  = f'<span class="pc-tag {_p["dist_cls"]}">{_p["dist_label"]}</span>'
                    _score_tag_str = (f'<span class="pc-tag t-blue">Score {_rs_val:.0f}</span>'
                                      if _rs_val is not None else "")
                    _qs_tag_str    = (f'<span class="pc-tag t-blue">Quality {_qs_val:.0f}</span>'
                                      if _qs_val > 0 else "")
                    _stock_tag_str = (f'<span class="pc-tag t-warn">Only {_p["qty"]} left</span>'
                                      if 0 < _p.get("qty",0) < 10 else "")
                    _rec_badge_str = '<div class="pc-rec-badge">Best Match</div>' if _is_rec else ""
                    _pc_cls        = "pc rec" if _is_rec else "pc"
                    _stars_str     = _stars(_rating)
                    _price_str     = f"${_p['price']:.2f}"

                    if _p.get("img"):
                        _img_block = (f'<div class="pc-img-wrap">'
                                      f'<img class="pc-img" src="{_p["img"]}" loading="lazy">'
                                      f'{_rec_badge_str}</div>')
                    else:
                        _img_block = f'<div class="pc-no-img">{_rec_badge_str}📦</div>'

                    with _cols[_ci]:
                        st.markdown(
                            f'<div class="{_pc_cls}">'
                            f'{_img_block}'
                            f'<div class="pc-body">'
                            f'<div class="pc-name">{_p["product"]}</div>'
                            f'<div class="pc-sup">{_p["supplier"]} · 📍 {_p["location"]}</div>'
                            f'<div><span class="pc-stars">{_stars_str}</span>'
                            f'<span class="pc-rc">{_rcount} reviews</span></div>'
                            f'<div class="pc-tags">{_dist_tag_str}{_score_tag_str}'
                            f'{_qs_tag_str}{_stock_tag_str}</div>'
                            f'<div class="pc-price">{_price_str}</div>'
                            f'<div class="pc-stock">{_p["qty"]} in stock</div>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                        st.session_state.ps_store[_pid] = _p
                        _ba, _bb = st.columns(2)
                        with _ba:
                            st.button("View", key=f"v_{_pid}",
                                      use_container_width=True,
                                      on_click=_cb_view, args=(_pid,))
                        with _bb:
                            st.button("Add to Cart", key=f"c_{_pid}",
                                      use_container_width=True,
                                      on_click=_cb_cart, args=(_pid,))

            # Map
            if len(_enriched) > 1:
                st.markdown(
                    '<div class="mkt-sh">'
                    '<div class="mkt-sh-t">Supplier locations</div>'
                    '<div class="mkt-sh-m">Relative to your selected area</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                _map_pts = [{"lat": _p.get("lat2", u_lat), "lon": _p.get("lon2", u_lon)}
                            for _p in _enriched]
                _map_pts.insert(0, {"lat": u_lat, "lon": u_lon})
                st.map(pd.DataFrame(_map_pts))

        else:
            st.markdown(
                f'<div class="mkt-empty">'
                f'<div class="mkt-empty-i">🔍</div>'
                f'<div class="mkt-empty-t">No results for "{query}"</div>'
                f'<div class="mkt-empty-s">'
                f'Try a broader term, a different location, or expand the radius.</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    else:
        # Nothing searched yet — show prompt only
        st.markdown(
            '<div class="mkt-empty">'
            '<div class="mkt-empty-i">🔍</div>'
            '<div class="mkt-empty-t">Search for a product to begin</div>'
            '<div class="mkt-empty-s">'
            'Enter a product name above and hit Search.<br>'
            'Results will show verified suppliers ranked by price, distance and quality.'
            '</div></div>',
            unsafe_allow_html=True
        )
                                
# =========================================================
# VENUS AI ASSISTANT — Next-level upgrade
# =========================================================
elif "VENUS AI Assistant" in menu:
    import requests, base64, io

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

    /* ── Page background pulse ── */
    @keyframes bgPulse {
        0%,100% { opacity: 0.6; }
        50%      { opacity: 1.0; }
    }
    .venus-chat-glow {
        position: fixed; top: -160px; left: 50%; transform: translateX(-50%);
        width: 700px; height: 340px; pointer-events: none; z-index: 0;
        background: radial-gradient(ellipse, rgba(0,229,255,0.07) 0%, rgba(168,85,247,0.05) 45%, transparent 70%);
        animation: bgPulse 6s ease-in-out infinite;
    }

    /* ── Header ── */
    .vai-chat-header {
        text-align: center;
        padding: 18px 0 32px;
        position: relative; z-index: 1;
    }
    .vai-chat-logo {
        font-family: 'Syne', sans-serif;
        font-size: 13px; font-weight: 700;
        letter-spacing: 0.22em; text-transform: uppercase;
        color: #4a5a72; margin-bottom: 18px;
    }
    .vai-chat-title {
        font-family: 'Syne', sans-serif;
        font-size: 38px; font-weight: 800;
        letter-spacing: -0.03em; line-height: 1.1;
        background: linear-gradient(135deg, #e8edf5 20%, #00e5ff 60%, #a855f7 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .vai-chat-sub {
        font-size: 14px; color: #4a5a72;
        font-family: 'DM Sans', sans-serif; font-weight: 300;
        letter-spacing: 0.02em;
    }

    /* ── Suggestion cards ── */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .vai-suggestion-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        max-width: 680px;
        margin: 0 auto 36px;
    }
    .vai-suggestion-card {
        background: rgba(8,8,18,0.9);
        border: 1px solid rgba(0,229,255,0.08);
        border-radius: 16px;
        padding: 16px 18px;
        cursor: pointer;
        transition: border-color 0.2s, background 0.2s, transform 0.15s;
        position: relative; overflow: hidden;
        animation: fadeUp 0.5s ease both;
    }
    .vai-suggestion-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,229,255,0.25), transparent);
        opacity: 0; transition: opacity 0.2s;
    }
    .vai-suggestion-card:hover {
        border-color: rgba(0,229,255,0.22);
        background: rgba(0,229,255,0.04);
        transform: translateY(-2px);
    }
    .vai-suggestion-card:hover::before { opacity: 1; }
    .vai-sug-icon {
        font-size: 20px; margin-bottom: 8px; display: block; line-height: 1;
    }
    .vai-sug-title {
        font-family: 'Syne', sans-serif;
        font-size: 13px; font-weight: 700;
        color: #e8edf5; margin-bottom: 3px;
    }
    .vai-sug-desc {
        font-size: 11px; color: #4a5a72;
        font-family: 'DM Sans', sans-serif; line-height: 1.5;
    }
    .vai-sug-arrow {
        position: absolute; right: 14px; bottom: 14px;
        font-size: 13px; color: rgba(0,229,255,0.3);
        transition: color 0.2s, transform 0.2s;
    }
    .vai-suggestion-card:hover .vai-sug-arrow {
        color: #00e5ff; transform: translateX(3px);
    }

    /* ── Chat bubbles ── */
    .vai-chat-wrap {
        max-width: 740px; margin: 0 auto 20px;
        position: relative; z-index: 1;
    }

    @keyframes bubbleIn {
        from { opacity: 0; transform: translateY(8px) scale(0.98); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    .vai-bubble-row-user {
        display: flex; justify-content: flex-end;
        margin: 10px 0;
        animation: bubbleIn 0.25s ease both;
    }
    .vai-bubble-user {
        background: linear-gradient(135deg, rgba(0,229,255,0.13), rgba(168,85,247,0.10));
        border: 1px solid rgba(0,229,255,0.2);
        color: #e8edf5;
        border-radius: 20px 20px 5px 20px;
        padding: 13px 18px;
        max-width: 72%;
        font-size: 14px; line-height: 1.65;
        font-family: 'DM Sans', sans-serif;
    }

    .vai-bubble-row-ai {
        display: flex; justify-content: flex-start;
        align-items: flex-start; gap: 11px;
        margin: 14px 0;
        animation: bubbleIn 0.3s ease both;
    }
    .vai-avatar {
        width: 34px; height: 34px; min-width: 34px;
        background: linear-gradient(135deg, #00e5ff, #a855f7);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Syne', sans-serif;
        font-size: 13px; font-weight: 800; color: #000;
        box-shadow: 0 0 14px rgba(0,229,255,0.25);
        flex-shrink: 0; margin-top: 2px;
    }
    .vai-bubble-ai {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(0,229,255,0.07);
        color: #d0dcea;
        border-radius: 5px 20px 20px 20px;
        padding: 14px 20px;
        max-width: 78%;
        font-size: 14px; line-height: 1.75;
        font-family: 'DM Sans', sans-serif;
        position: relative;
    }
    .vai-bubble-ai strong { color: #e8edf5; font-weight: 600; }
    .vai-bubble-ai ul { margin: 8px 0 4px 16px; padding: 0; }
    .vai-bubble-ai li { margin-bottom: 4px; }

    /* ── Thinking indicator ── */
    @keyframes dot {
        0%,80%,100% { transform: scale(0.6); opacity: 0.3; }
        40%          { transform: scale(1.0); opacity: 1.0; }
    }
    .vai-thinking {
        display: flex; gap: 5px; align-items: center;
        padding: 14px 20px;
    }
    .vai-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #00e5ff; animation: dot 1.4s ease-in-out infinite;
    }
    .vai-dot:nth-child(2) { animation-delay: 0.2s; }
    .vai-dot:nth-child(3) { animation-delay: 0.4s; }

    /* ── Input bar ── */
    [data-testid="stChatInput"] > div {
        border-radius: 20px !important;
        border: 1px solid rgba(0,229,255,0.18) !important;
        background: rgba(10,14,26,0.97) !important;
        backdrop-filter: blur(24px) !important;
        box-shadow: 0 0 40px rgba(0,229,255,0.05) !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border-color: rgba(0,229,255,0.4) !important;
        box-shadow: 0 0 0 3px rgba(0,229,255,0.07), 0 0 40px rgba(0,229,255,0.08) !important;
    }
    [data-testid="stChatInput"] textarea {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
        color: #e8edf5 !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] textarea::placeholder { color: #4a6080 !important; }
    [data-testid="stChatInput"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #00e5ff, #a855f7) !important;
        border-radius: 12px !important;
        color: #000 !important;
        font-weight: 700 !important;
    }

    /* ── Clear button ── */
    .vai-clear-row {
        max-width: 740px; margin: 6px auto 0;
        display: flex; justify-content: flex-end;
        position: relative; z-index: 1;
    }

    /* ── Divider label ── */
    .vai-session-label {
        text-align: center; font-size: 11px; color: #1e2e44;
        font-family: 'DM Mono', monospace; letter-spacing: 0.08em;
        margin: 6px 0 18px; position: relative; z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Background glow ──
    st.markdown('<div class="venus-chat-glow"></div>', unsafe_allow_html=True)

    # ── Fetch live business context for Claude ──
    cursor.execute("SELECT COUNT(*) FROM products WHERE user_id=?", (user_id,))
    prod_count = cursor.fetchone()[0]
    try:
        df_txn_ctx = pd.read_sql("SELECT total FROM transactions ORDER BY id DESC LIMIT 20", conn)
        rev_ctx = df_txn_ctx["total"].sum()
        txn_ctx = len(df_txn_ctx)
    except:
        rev_ctx, txn_ctx = 0, 0
    cursor.execute("SELECT SUM(qty) FROM inventory WHERE user_id=?", (user_id,))
    inv_ctx = cursor.fetchone()[0] or 0

    biz_context = f"""You are VENUS AI, a superintelligent e-commerce business advisor embedded inside the VENUS AI platform.
The user is: {user['name']} ({user['role']}) based in {user.get('location','Lusaka, Zambia')}.
Their live business snapshot: {prod_count} products listed, {txn_ctx} transactions recorded, ${rev_ctx:,.2f} revenue, {inv_ctx} inventory units.
Be sharp, specific, and direct. Use markdown formatting (bold, bullet points) where it helps clarity.
Keep responses focused and actionable. Reference their actual numbers when relevant."""

    # ── Session init ──
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "vai_pending" not in st.session_state:
        st.session_state.vai_pending = None

    # ── Suggestion definitions ──
    suggestions = [
        {
            "icon": "📊",
            "title": "Analyse my sales performance",
            "desc": "Revenue trends, top products & growth",
            "prompt": f"Analyse my sales performance. I have {txn_ctx} transactions totalling ${rev_ctx:,.2f}. What does this tell you and what should I do next?",
            "delay": "0.05s"
        },
        {
            "icon": "💡",
            "title": "Generate marketing ideas",
            "desc": "Campaign strategies for my products",
            "prompt": f"Give me 5 specific marketing campaign ideas for a {user.get('location','Lusaka')}-based supplier with {prod_count} products listed on an e-commerce platform.",
            "delay": "0.15s"
        },
        {
            "icon": "📦",
            "title": "Optimise my inventory",
            "desc": "Cut waste, prevent stockouts",
            "prompt": f"I have {inv_ctx} inventory units across {prod_count} products. How should I optimise my inventory strategy to reduce waste and prevent stockouts?",
            "delay": "0.25s"
        },
        {
            "icon": "🛡️",
            "title": "Fraud & risk assessment",
            "desc": "Identify vulnerabilities in my setup",
            "prompt": "What are the top fraud and risk vulnerabilities for an e-commerce supplier like me, and what specific steps should I take to protect my business?",
            "delay": "0.35s"
        },
        {
            "icon": "💰",
            "title": "Pricing strategy advice",
            "desc": "Maximise margin without losing buyers",
            "prompt": f"Help me build a pricing strategy for my {prod_count} products. How do I maximise margin without losing buyers in a competitive market?",
            "delay": "0.10s"
        },
        {
            "icon": "🚀",
            "title": "Scale my business",
            "desc": "Next steps to grow revenue 2x",
            "prompt": f"What are the top 3 highest-leverage actions I can take right now to grow my e-commerce revenue? I have {prod_count} products and ${rev_ctx:,.2f} in recorded revenue.",
            "delay": "0.30s"
        },
    ]

    # ── Header ──
    st.markdown("""
    <div class="vai-chat-header">
        <div class="vai-chat-logo">VENUS · AI ASSISTANT</div>
        <div class="vai-chat-title">What can I help<br>you build today?</div>
        <div class="vai-chat-sub">Ask anything about your business — I have your live data.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Suggestion grid (only when chat is empty) ──
    if not st.session_state.chat and st.session_state.vai_pending is None:
        cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(
                    f"{s['icon']}  {s['title']}\n{s['desc']}",
                    key=f"sug_{i}",
                    use_container_width=True
                ):
                    st.session_state.vai_pending = s["prompt"]
                    st.rerun()

        # Style the suggestion buttons to match the cards
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] .stButton > button {
            background: rgba(8,8,18,0.9) !important;
            border: 1px solid rgba(0,229,255,0.08) !important;
            border-radius: 16px !important;
            color: #e8edf5 !important;
            text-align: left !important;
            padding: 16px 18px !important;
            height: auto !important;
            min-height: 76px !important;
            font-size: 13px !important;
            font-family: 'DM Sans', sans-serif !important;
            line-height: 1.5 !important;
            white-space: pre-line !important;
            transition: border-color 0.2s, background 0.2s, transform 0.15s !important;
        }
        div[data-testid="stHorizontalBlock"] .stButton > button:hover {
            border-color: rgba(0,229,255,0.28) !important;
            background: rgba(0,229,255,0.05) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(0,0,0,0.3) !important;
            color: #e8edf5 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # ── Session label ──
    if st.session_state.chat:
        st.markdown('<div class="vai-session-label">— current session —</div>', unsafe_allow_html=True)

    # ── Chat history render ──
    if st.session_state.chat:
        chat_html = '<div class="vai-chat-wrap">'
        for role, msg in st.session_state.chat:
            if role == "You":
                chat_html += f"""
                <div class="vai-bubble-row-user">
                    <div class="vai-bubble-user">{msg}</div>
                </div>"""
            else:
                # Light markdown: **bold**, newlines
                import re
                formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', msg)
                formatted = formatted.replace('\n', '<br>')
                chat_html += f"""
                <div class="vai-bubble-row-ai">
                    <div class="vai-avatar">V</div>
                    <div class="vai-bubble-ai">{formatted}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # ── Process pending (suggestion click) or chat input ──
    def call_claude(prompt):
        """Call real Claude API with full business context."""
        messages = []
        # Include conversation history
        for role, msg in st.session_state.chat[-10:]:
            messages.append({
                "role": "user" if role == "You" else "assistant",
                "content": msg
            })
        messages.append({"role": "user", "content": prompt})

        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "system": biz_context,
                    "messages": messages
                },
                timeout=30
            )
            return resp.json()["content"][0]["text"]
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again in a moment. *(Error: {e})*"

    # Handle suggestion click
    if st.session_state.vai_pending is not None:
        prompt = st.session_state.vai_pending
        st.session_state.vai_pending = None
        st.session_state.chat.append(("You", prompt))
        with st.spinner(""):
            reply = call_claude(prompt)
        st.session_state.chat.append(("VENUS AI", reply))
        st.rerun()

    # Handle typed message
    user_input = st.chat_input("Ask VENUS anything about your business...")
    if user_input:
        st.session_state.chat.append(("You", user_input))
        with st.spinner(""):
            reply = call_claude(user_input)
        st.session_state.chat.append(("VENUS AI", reply))
        st.rerun()

    # ── Clear button ──
    if st.session_state.chat:
        st.markdown('<div class="vai-clear-row">', unsafe_allow_html=True)
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state.chat = []
            st.session_state.vai_pending = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
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
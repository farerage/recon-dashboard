import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import plotly.express as px
import config

# ======================
# DATABASE CONNECTION
# ======================
engine = create_engine(
    f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASS}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

SCHEMA = getattr(config, "DB_SCHEMA", "public").strip() or "public"

def tbl(name: str) -> str:
    """Qualified table name with schema."""
    return f'{SCHEMA}.{name}'

def ensure_schema(engine, schema: str):
    """Create schema if not exists (safe to run repeatedly)."""
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}";'))

# Pastikan schema tersedia kalau bukan 'public'
if SCHEMA != "public":
    try:
        ensure_schema(engine, SCHEMA)
    except Exception as e:
        st.info(f"Note: gagal membuat schema {SCHEMA}: {e}. Pastikan role DB-mu punya izin.")

# ======================
# CUSTOM CSS - Paper.id Style
# ======================
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* Modern dark theme with vibrant accents */
    .stApp {
        background: #0a0e27;
        background-image: 
            radial-gradient(circle at 25% 25%, #1e3a8a 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, #7c3aed 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, #059669 0%, transparent 50%);
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
        min-height: 100vh;
    }
    
    /* Main content area */
    .main {
        background: transparent;
        padding: 2rem;
    }
    
    /* Sidebar with frosted glass effect */
    .css-1d391kg {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(25px);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    
    /* Hide default radio buttons */
    .stRadio > div {
        display: none;
    }
    
    /* Navigation styling */
    .nav-title {
        color: #f1f5f9;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 1.5rem;
        padding: 0 1rem;
        text-align: center;
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Navigation buttons */
    .stButton > button {
        width: 100% !important;
        background: rgba(30, 41, 59, 0.6) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 16px !important;
        padding: 1rem 1.5rem !important;
        margin: 0.5rem 0 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(10px) !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.2), transparent);
        transition: left 0.6s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2)) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: #f1f5f9 !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Active navigation button */
    .stButton > button:focus {
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Glass card containers */
    .card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(25px);
        border-radius: 24px;
        padding: 2.5rem;
        margin: 2rem 0;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
    }
    
    /* Stunning title */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6, #ec4899) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-shadow: 0 0 50px rgba(59, 130, 246, 0.3) !important;
        animation: glow 3s ease-in-out infinite alternate !important;
    }
    
    @keyframes glow {
        from {
            filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.3));
        }
        to {
            filter: drop-shadow(0 0 40px rgba(139, 92, 246, 0.5));
        }
    }
    
    /* Subtitle with animation */
    .subtitle {
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 1.25rem !important;
        margin-bottom: 3rem !important;
        font-weight: 400 !important;
        animation: fadeInUp 1s ease-out !important;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Section headers with gradient */
    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin-bottom: 2rem !important;
        padding-bottom: 1rem !important;
        position: relative !important;
    }
    
    h3::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6);
        border-radius: 2px;
    }
    
    /* Stunning metric cards */
    .metric-container {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 1rem !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .metric-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #06b6d4, #3b82f6, #8b5cf6, #ec4899);
    }
    
    .metric-container:hover {
        transform: translateY(-8px) scale(1.02) !important;
        box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.3) !important;
        background: rgba(30, 41, 59, 0.8) !important;
    }
    
    /* Premium buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem 2.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button[kind="primary"]::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
        transition: all 0.6s;
        transform: translate(-50%, -50%);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 30px 60px -12px rgba(59, 130, 246, 0.5) !important;
    }
    
    .stButton > button[kind="primary"]:hover::before {
        width: 300px;
        height: 300px;
    }
    
    /* Enhanced inputs */
    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        color: #f1f5f9 !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
        background: rgba(30, 41, 59, 0.8) !important;
        outline: none !important;
    }
    
    /* Premium file uploader */
    .stFileUploader > div {
        border: 2px dashed rgba(59, 130, 246, 0.3) !important;
        border-radius: 20px !important;
        padding: 4rem !important;
        text-align: center !important;
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stFileUploader > div::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
        transition: left 1s;
    }
    
    .stFileUploader > div:hover {
        border-color: #3b82f6 !important;
        background: rgba(30, 41, 59, 0.6) !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stFileUploader > div:hover::before {
        left: 100%;
    }
    
    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 16px !important;
        padding: 0.5rem !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 1rem 2rem !important;
        transition: all 0.3s ease !important;
        color: #94a3b8 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #06b6d4, #3b82f6) !important;
        color: white !important;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Enhanced dataframe */
    .stDataFrame {
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        backdrop-filter: blur(10px) !important;
        background: rgba(30, 41, 59, 0.4) !important;
    }
    
    /* Beautiful alerts */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
        color: #34d399 !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
        color: #f87171 !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #60a5fa !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Custom metrics styling */
    [data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(20px) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.2) !important;
        background: rgba(30, 41, 59, 0.8) !important;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6);
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #0891b2, #2563eb, #7c3aed);
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    
    /* Card containers with glassmorphism */
    .card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Title styling */
    h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.75rem;
        margin-bottom: 0.5rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Subtitle */
    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }
    
    /* Section headers */
    h3 {
        color: #1e293b;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid transparent;
        background: linear-gradient(90deg, #667eea, #764ba2) bottom / 100% 2px no-repeat;
    }
    
    /* Metrics styling with glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
        background: rgba(255, 255, 255, 0.98);
    }
    
    /* Button styling - Paper.id gradient style */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Input styling with glassmorphism */
    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stSelectbox > div > div > select {
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 8px;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        color: #374151;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stDateInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border: 2px solid #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* File uploader with Paper.id style */
    .stFileUploader > div {
        border: 2px dashed rgba(102, 126, 234, 0.3);
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #667eea;
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    /* Success/Error messages with glassmorphism */
    .stSuccess {
        background: rgba(240, 253, 244, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(187, 247, 208, 0.5);
        border-radius: 10px;
        color: #166534;
    }
    
    .stError {
        background: rgba(254, 242, 242, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(254, 202, 202, 0.5);
        border-radius: 10px;
        color: #dc2626;
    }
    
    .stInfo {
        background: rgba(239, 246, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(147, 197, 253, 0.5);
        border-radius: 10px;
        color: #1e40af;
    }
    
    /* Metrics styling */
    .metric-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8, #6b46c1);
    }
</style>
""", unsafe_allow_html=True)

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Reconciliation Dashboard", layout="wide", initial_sidebar_state="expanded")

# ======================
# SIDEBAR NAVIGATION
# ======================
with st.sidebar:
    st.markdown('<div class="nav-title">🎯 Navigation</div>', unsafe_allow_html=True)
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'

    st.markdown('<div class="nav-menu">', unsafe_allow_html=True)
    if st.button("📊 Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.current_page = 'Dashboard'
    if st.button("📤 Upload Data", key="nav_upload", use_container_width=True):
        st.session_state.current_page = 'Upload Data'
    if st.button("📈 Analytics", key="nav_visualization", use_container_width=True):
        st.session_state.current_page = 'Visualization'
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📈 Quick Stats")
    try:
        with engine.connect() as conn:
            quick_stats = pd.read_sql(text(f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN recon_status = 'Reconciled' THEN 1 END) as reconciled,
                    COUNT(CASE WHEN recon_status = 'Unreconciled' THEN 1 END) as unreconciled
                FROM {tbl('reconciliation')}
                WHERE transaction_date_dash >= CURRENT_DATE - INTERVAL '7 days'
            """), conn)
            if not quick_stats.empty:
                st.metric("Records (7d)", f"{quick_stats.iloc[0]['total_records']:,}")
                st.metric("Reconciled", f"{quick_stats.iloc[0]['reconciled']:,}")
                st.metric("Unreconciled", f"{quick_stats.iloc[0]['unreconciled']:,}")
    except Exception as e:
        st.info(f"Connect to view stats (schema={SCHEMA}). Detail: {e}")

# Label menu (opsional dipakai)
selected_menu = (
    f"📊 {st.session_state.current_page}" if st.session_state.current_page == 'Dashboard'
    else f"📤 {st.session_state.current_page}" if st.session_state.current_page == 'Upload Data'
    else f"📈 {st.session_state.current_page}"
)

# ======================
# MAIN CONTENT
# ======================
if st.session_state.current_page == 'Upload Data':
    st.title("📤 Upload Reconciliation Data")
    st.markdown('<p class="subtitle">Upload your CSV or Excel files to the database</p>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📁 File Upload")

        uploaded_file = st.file_uploader(
            "Choose your reconciliation data file",
            type=["csv", "xlsx"],
            help="Supported formats: CSV, Excel (.xlsx)"
        )

        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)

                # File info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Name", uploaded_file.name)
                with col2:
                    st.metric("Total Rows", f"{len(df_upload):,}")
                with col3:
                    st.metric("Total Columns", len(df_upload.columns))

                # Preview
                st.markdown("### 👀 Data Preview")
                st.dataframe(df_upload.head(10), use_container_width=True)

                # Options
                st.markdown("### ⚙️ Upload Options")
                col1, col2 = st.columns(2)
                with col1:
                    duplicate_action = st.selectbox(
                        "Handle Duplicates:",
                        ["Skip Duplicates", "Update Existing", "Add All (Allow Duplicates)"],
                        help="Choose how to handle records that already exist in database"
                    )
                with col2:
                    unique_column = st.selectbox(
                        "Unique Identifier:",
                        ["tx_id_gds", "ref_number_gds", "unique_id_gds", "invoice_number_dash"],
                        help="Column used to identify duplicate records"
                    )

                # Upload button
                if st.button("💾 Save to Database", type="primary", use_container_width=True):
                    with st.spinner("Processing and saving data to database..."):
                        # Normalize columns
                        df_upload.columns = [c.lower() for c in df_upload.columns]

                        valid_columns = [
                            'no_dash','payment_method_dash','acquirer_dash','transaction_date_dash',
                            'recon_code_dash','invoice_number_dash','type_dash','credit_type_dash','currency_dash',
                            'total_amount_dash','total_discount_dash','aggregator_invoicing_dash','total_fee_dash',
                            'net_amount_dash','settlement_schedule_dash','status_dash','remarks_dash',
                            'settlement_batch_number_dash','settlement_amount_dash','destination_bank_dash',
                            'destination_account_name_dash','destination_account_number_dash','created_datetime_gds',
                            'last_updated_datetime_gds','transaction_datetime_gds','settlement_time_gds',
                            'settlement_amount_gds','amount_gds','service_gds','sender_bank_gds','vendor_gds',
                            'transaction_status_gds','username_gds','tx_id_gds','ref_number_gds','unique_id_gds',
                            'va_number_gds','admin_fee_gds','admin_fee_invoice_gds','deduction_cost_gds',
                            'mam_child_username_gds','mam_parent_username_gds','charge_transaction_id_gds',
                            '_merge','recon_status'
                        ]
                        df_upload = df_upload[[c for c in df_upload.columns if c in valid_columns]]

                        # Date parsing
                        date_columns = [
                            'transaction_date_dash', 'created_datetime_gds', 'last_updated_datetime_gds',
                            'transaction_datetime_gds', 'settlement_time_gds'
                        ]
                        for col in date_columns:
                            if col in df_upload.columns:
                                df_upload[col] = pd.to_datetime(df_upload[col], errors="coerce", dayfirst=True)

                        # Numeric columns
                        numeric_columns = [
                            'total_amount_dash','total_discount_dash','total_fee_dash','net_amount_dash',
                            'settlement_amount_dash','settlement_amount_gds','amount_gds','admin_fee_gds',
                            'admin_fee_invoice_gds','deduction_cost_gds'
                        ]
                        for col in numeric_columns:
                            if col in df_upload.columns:
                                df_upload[col] = (
                                    df_upload[col].astype(str)
                                        .str.replace(",", "", regex=False)
                                        .str.replace(" ", "", regex=False)
                                )
                                df_upload[col] = pd.to_numeric(df_upload[col], errors="coerce")

                        # Dedupe flow
                        unique_col = unique_column.lower()

                        if duplicate_action == "Add All (Allow Duplicates)":
                            with engine.begin() as conn:
                                df_upload.to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                            uploaded_count = len(df_upload)
                            duplicate_count = 0

                        else:
                            if unique_col in df_upload.columns:
                                unique_values = df_upload[unique_col].dropna().astype(str).unique()

                                with engine.connect() as conn:
                                    if len(unique_values) == 0:
                                        existing_ids = set()
                                    else:
                                        # escape single quotes
                                        vals = "', '".join(v.replace("'", "''") for v in unique_values)
                                        existing_query = f"""
                                            SELECT DISTINCT {unique_col}
                                            FROM {tbl('reconciliation')}
                                            WHERE {unique_col} IN ('{vals}')
                                        """
                                        try:
                                            existing_df = pd.read_sql(text(existing_query), conn)
                                            existing_ids = set(existing_df[unique_col].astype(str).values)
                                        except Exception:
                                            existing_ids = set()

                                df_upload['__is_dup'] = df_upload[unique_col].astype(str).isin(existing_ids)
                                duplicates = df_upload[df_upload['__is_dup']]
                                new_records = df_upload[~df_upload['__is_dup']]
                                duplicate_count = len(duplicates)

                                if duplicate_action == "Skip Duplicates":
                                    if len(new_records) > 0:
                                        with engine.begin() as conn:
                                            new_records.drop(columns='__is_dup').to_sql(
                                                "reconciliation", conn, if_exists="append", index=False, schema=SCHEMA
                                            )
                                    uploaded_count = len(new_records)

                                elif duplicate_action == "Update Existing":
                                    # Insert new
                                    if len(new_records) > 0:
                                        with engine.begin() as conn:
                                            new_records.drop(columns='__is_dup').to_sql(
                                                "reconciliation", conn, if_exists="append", index=False, schema=SCHEMA
                                            )

                                    # Upsert duplicates
                                    if len(duplicates) > 0:
                                        duplicates_clean = duplicates.drop(columns='__is_dup')
                                        with engine.begin() as conn:
                                            # Temp table (schema default)
                                            duplicates_clean.to_sql("temp_reconciliation", conn, if_exists="replace", index=False)

                                            columns = list(duplicates_clean.columns)
                                            columns_str = ', '.join(columns)
                                            update_str = ', '.join(
                                                [f"{col} = EXCLUDED.{col}" for col in columns if col != unique_col]
                                            )
                                            upsert_query = f"""
                                                INSERT INTO {tbl('reconciliation')} ({columns_str})
                                                SELECT {columns_str} FROM temp_reconciliation
                                                ON CONFLICT ({unique_col}) DO UPDATE SET {update_str}
                                            """
                                            conn.execute(text(upsert_query))
                                            conn.execute(text("DROP TABLE temp_reconciliation"))

                                    uploaded_count = len(df_upload)

                                df_upload.drop(columns='__is_dup', inplace=True)
                            else:
                                with engine.begin() as conn:
                                    df_upload.to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                                uploaded_count = len(df_upload)
                                duplicate_count = 0

                        # Messages
                        if duplicate_count > 0:
                            if duplicate_action == "Skip Duplicates":
                                st.success(f"✅ Successfully uploaded {uploaded_count:,} new records! Skipped {duplicate_count:,} duplicates.")
                            elif duplicate_action == "Update Existing":
                                st.success(f"✅ Successfully processed {uploaded_count:,} records! Updated {duplicate_count:,} existing records.")
                            else:
                                st.success(f"✅ Successfully uploaded {uploaded_count:,} records!")
                        else:
                            st.success(f"✅ Successfully uploaded {uploaded_count:,} new records to the database!")

                        if duplicate_count > 0:
                            c1, c2, c3 = st.columns(3)
                            with c1: st.metric("Total Records", f"{len(df_upload):,}")
                            with c2: st.metric("New Records", f"{uploaded_count:,}")
                            with c3: st.metric("Duplicates Found", f"{duplicate_count:,}")

            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'Visualization':
    st.title("📊 Data Visualization")
    st.markdown('<p class="subtitle">Visual analytics of reconciliation data</p>', unsafe_allow_html=True)

    try:
        with engine.connect() as conn:
            df_viz = pd.read_sql(text(f"""
                SELECT transaction_date_dash, username_gds, tx_id_gds, 
                       total_amount_dash, recon_status, payment_method_dash
                FROM {tbl('reconciliation')}
                WHERE transaction_date_dash >= CURRENT_DATE - INTERVAL '30 days'
            """), conn)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df_viz = pd.DataFrame()

    if not df_viz.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🥧 Status Distribution")
            fig_pie = px.pie(
                df_viz.groupby('recon_status').size().reset_index(name='count'),
                values='count', names='recon_status',
                color_discrete_map={'Reconciled': '#10b981', 'Unreconciled': '#ef4444'}
            )
            fig_pie.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📈 Daily Trend (Last 30 Days)")
            if not pd.api.types.is_datetime64_any_dtype(df_viz['transaction_date_dash']):
                df_viz['transaction_date_dash'] = pd.to_datetime(df_viz['transaction_date_dash'], errors='coerce')
            daily_data = (
                df_viz.groupby([df_viz['transaction_date_dash'].dt.date, 'recon_status'])
                .size().reset_index(name='count')
            ).rename(columns={'transaction_date_dash': 'tx_date'})
            fig_line = px.line(
                daily_data, x='tx_date', y='count', color='recon_status',
                color_discrete_map={'Reconciled': '#10b981', 'Unreconciled': '#ef4444'}
            )
            fig_line.update_layout(height=400)
            st.plotly_chart(fig_line, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if 'payment_method_dash' in df_viz.columns:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 💳 Payment Method Analysis")
            payment_data = df_viz.groupby(['payment_method_dash', 'recon_status']).size().reset_index(name='count')
            fig_bar = px.bar(
                payment_data, x='payment_method_dash', y='count', color='recon_status',
                color_discrete_map={'Reconciled': '#10b981', 'Unreconciled': '#ef4444'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📊 No data available for visualization. Please upload data first.")

else:
    # DASHBOARD
    st.title("📊 Reconciliation Dashboard")
    st.markdown('<p class="subtitle">Monitor and analyze your reconciliation data</p>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Filters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_date = st.date_input("Start Date", value=datetime(2025,1,1))
        with col2:
            end_date = st.date_input("End Date", value=datetime.today())
        with col3:
            username = st.text_input("Username")
        with col4:
            identifier = st.text_input("Transaction ID")
        st.markdown('</div>', unsafe_allow_html=True)

    query = f"""
        SELECT transaction_date_dash, username_gds, tx_id_gds, total_amount_dash, recon_status,
               payment_method_dash, acquirer_dash
        FROM {tbl('reconciliation')}
        WHERE transaction_date_dash BETWEEN :start_date AND :end_date
    """
    params = {"start_date": start_date, "end_date": end_date}
    if username:
        query += " AND username_gds ILIKE :username"
        params["username"] = f"%{username}%"
    if identifier:
        query += " AND tx_id_gds ILIKE :identifier"
        params["identifier"] = f"%{identifier}%"

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df = pd.DataFrame()

    if not df.empty:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📈 Summary Metrics")

            col1, col2, col3, col4 = st.columns(4)
            total_records = len(df)

            # >>> Seragamkan status: gunakan 'Reconciled'/'Unreconciled'
            reconciled_count = len(df[df['recon_status'] == 'Reconciled'])
            unreconciled_count = len(df[df['recon_status'] == 'Unreconciled'])
            total_amount = df['total_amount_dash'].sum() if 'total_amount_dash' in df.columns else 0

            with col1:
                st.metric("Total Records", f"{total_records:,}")
            with col2:
                st.metric("Reconciled", f"{reconciled_count:,}", f"{(reconciled_count/total_records*100 if total_records else 0):.1f}%")
            with col3:
                st.metric("Unreconciled", f"{unreconciled_count:,}", f"{(unreconciled_count/total_records*100 if total_records else 0):.1f}%")
            with col4:
                st.metric("Total Amount", f"Rp {total_amount:,.0f}")

            st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📋 Reconciliation Data")
            tab1, tab2, tab3 = st.tabs(["📊 All Data", "✅ Reconciled", "❌ Unreconciled"])

            with tab1:
                st.dataframe(df, use_container_width=True, height=400)
                st.download_button(
                    "📥 Download All Data", df.to_csv(index=False),
                    f"reconciliation_all_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv"
                )

            with tab2:
                df_reconciled = df[df['recon_status'] == 'Reconciled']
                if not df_reconciled.empty:
                    st.dataframe(df_reconciled, use_container_width=True, height=400)
                    st.download_button(
                        "📥 Download Reconciled", df_reconciled.to_csv(index=False),
                        f"reconciliation_reconciled_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv"
                    )
                else:
                    st.info("No reconciled data found.")

            with tab3:
                df_unreconciled = df[df['recon_status'] == 'Unreconciled']
                if not df_unreconciled.empty:
                    st.dataframe(df_unreconciled, use_container_width=True, height=400)
                    st.download_button(
                        "📥 Download Unreconciled", df_unreconciled.to_csv(index=False),
                        f"reconciliation_unreconciled_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv"
                    )
                else:
                    st.info("No unreconciled data found.")

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("🔍 No data found. Please check your filters or upload data first.")
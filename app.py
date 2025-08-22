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
/* =========================================================
   Modern Pro Dashboard Theme (Dark-first, Accessible)
   - Uses CSS variables for easy theming
   - Toned glassmorphism, high contrast text
   - Streamlit component polish
   ========================================================= */

/* ---------- Theme Tokens ---------- */
:root {
  /* Brand */
  --brand-1: #06b6d4;  /* cyan */
  --brand-2: #3b82f6;  /* blue */
  --brand-3: #8b5cf6;  /* violet */
  --brand-4: #ec4899;  /* pink */

  /* Base (Dark) */
  --bg: #0a0e27;                /* page background */
  --bg-elev-1: rgba(18, 26, 58, 0.85);
  --bg-elev-2: rgba(22, 32, 72, 0.6);
  --glass: rgba(30, 41, 59, 0.55);
  --glass-strong: rgba(30, 41, 59, 0.75);
  --card-border: rgba(148, 163, 184, 0.18);

  /* Text */
  --text-1: #e5ecf5;            /* primary text */
  --text-2: #b6c2d1;            /* secondary */
  --text-3: #8fa0b6;            /* muted */

  /* Lines / Effects */
  --line-1: rgba(148, 163, 184, 0.25);
  --line-2: rgba(99, 102, 241, 0.35);

  /* States */
  --success: #10b981;
  --danger: #ef4444;
  --info: #60a5fa;
  --warning: #f59e0b;

  /* Radii, shadows */
  --radius-lg: 20px;
  --radius-md: 14px;
  --radius-sm: 10px;
  --shadow-1: 0 12px 30px -12px rgba(0,0,0,0.35);
  --shadow-2: 0 24px 48px -18px rgba(0,0,0,0.45);
}

/* ---------- App Background ---------- */
.stApp {
  background: var(--bg);
  background-image:
    radial-gradient(60rem 60rem at 20% 20%, rgba(59, 130, 246, 0.18), transparent 60%),
    radial-gradient(50rem 50rem at 80% 80%, rgba(139, 92, 246, 0.18), transparent 60%),
    radial-gradient(45rem 45rem at 50% 50%, rgba(6, 182, 212, 0.15), transparent 60%);
  color: var(--text-1);
  font-family: 'Outfit', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
  min-height: 100vh;
}

/* ---------- Page Containers ---------- */
.block-container {
  padding-top: 1.75rem;
  padding-bottom: 2rem;
}

/* ---------- Sidebar (use data-testid to avoid brittle classnames) ---------- */
section[data-testid="stSidebar"] {
  background: var(--bg-elev-1) !important;
  backdrop-filter: blur(18px);
  border-right: 1px solid var(--card-border);
  box-shadow: var(--shadow-1);
}

section[data-testid="stSidebar"] .sidebar-content {
  padding-top: 1rem;
}

.nav-title {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 800;
  letter-spacing: .3px;
  text-align: center;
  margin: .25rem 0 1rem;
  font-size: 1.05rem;
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2), var(--brand-3));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ---------- Buttons ---------- */
.stButton > button {
  width: 100% !important;
  border-radius: var(--radius-md) !important;
  padding: .9rem 1.2rem !important;
  font-weight: 700 !important;
  letter-spacing: .2px;
  background: linear-gradient(135deg, rgba(30, 41, 59, .7), rgba(30, 41, 59, .55)) !important;
  color: var(--text-1) !important;
  border: 1px solid var(--card-border) !important;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease, background .3s ease !important;
  backdrop-filter: blur(8px) !important;
}
.stButton > button:hover {
  transform: translateY(-1px);
  border-color: var(--line-2) !important;
  box-shadow: 0 10px 24px -10px rgba(59, 130, 246, .35) !important;
  background: linear-gradient(135deg, rgba(59,130,246,.18), rgba(139,92,246,.18)) !important;
}
.stButton > button:active {
  transform: translateY(0);
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2), var(--brand-3)) !important;
  color: white !important;
  border: none !important;
  box-shadow: 0 16px 36px -14px rgba(59, 130, 246, .55) !important;
}
.stButton > button[kind="primary"]:hover {
  filter: brightness(1.06);
}

/* ---------- Cards / Surfaces ---------- */
.card {
  background: var(--glass);
  border: 1px solid var(--card-border);
  backdrop-filter: blur(18px);
  border-radius: var(--radius-lg);
  padding: 1.75rem;
  margin: 1.25rem 0;
  box-shadow: var(--shadow-1);
  position: relative;
  overflow: clip;
}
.card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,.55), transparent);
  opacity: .6;
}

/* ---------- Typography ---------- */
h1, h2, h3 {
  color: var(--text-1) !important;
}
h1 {
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 900 !important;
  font-size: clamp(2rem, 3.2vw, 3.2rem) !important;
  text-align: center !important;
  margin: .25rem 0 1rem !important;
  letter-spacing: .2px;
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2), var(--brand-3), var(--brand-4));
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  text-shadow: 0 0 24px rgba(59,130,246,.22);
}
.subtitle {
  color: var(--text-2) !important;
  text-align: center !important;
  font-size: 1.05rem !important;
  margin-bottom: 1.6rem !important;
}

/* Section headers */
.card h3 {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.15rem !important;
  font-weight: 800 !important;
  color: var(--text-1) !important;
  margin: 0 0 1.2rem !important;
  padding-bottom: .6rem !important;
  position: relative !important;
}
.card h3::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 72px; height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--brand-1), var(--brand-2), var(--brand-3));
}

/* ---------- Inputs ---------- */
.stTextInput input, .stDateInput input, .stSelectbox select {
  background: var(--bg-elev-2) !important;
  border: 1px solid var(--card-border) !important;
  color: var(--text-1) !important;
  border-radius: var(--radius-sm) !important;
  padding: .7rem .9rem !important;
  backdrop-filter: blur(10px) !important;
}
.stTextInput input:focus, .stDateInput input:focus, .stSelectbox select:focus {
  outline: none !important;
  border-color: var(--line-2) !important;
  box-shadow: 0 0 0 4px rgba(59,130,246,.12) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-elev-2) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: var(--radius-md) !important;
  padding: .35rem !important;
  backdrop-filter: blur(12px) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-3) !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  padding: .6rem 1rem !important;
}
.stTabs [aria-selected="true"] {
  color: white !important;
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2)) !important;
  box-shadow: 0 10px 22px -12px rgba(59,130,246,.45) !important;
}

/* ---------- Dataframe/Table ---------- */
.stDataFrame, .stTable {
  border: 1px solid var(--card-border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden !important;
  background: var(--glass-strong) !important;
}
[data-testid="stStyledTable"] table {
  color: var(--text-1) !important;
}
[data-testid="stStyledTable"] thead tr th {
  background: rgba(59,130,246,.12) !important;
  color: var(--text-1) !important;
  font-weight: 800 !important;
}
[data-testid="stStyledTable"] tbody tr:hover td {
  background: rgba(148, 163, 184, 0.08) !important;
}

/* ---------- Metrics ---------- */
[data-testid="metric-container"] {
  background: var(--bg-elev-2) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.2rem !important;
  transition: transform .2s ease;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-1);
}

/* ---------- Alerts ---------- */
.stAlert {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--card-border) !important;
  backdrop-filter: blur(10px) !important;
}
.stAlert [data-testid="stMarkdownContainer"] {
  color: var(--text-1) !important;
}
.stAlert[data-baseweb="alert"] {
  background: rgba(59,130,246,.10) !important;
}

/* Variant helpers for specific messages (if you use st.success/info/error) */
.stSuccess { background: rgba(16,185,129,.12) !important; color: var(--text-1) !important; }
.stInfo    { background: rgba(59,130,246,.12) !important; color: var(--text-1) !important; }
.stError   { background: rgba(239,68,68,.12) !important;  color: var(--text-1) !important; }

/* ---------- File Uploader ---------- */
.stFileUploader > div {
  border: 2px dashed rgba(59,130,246,.35) !important;
  border-radius: var(--radius-lg) !important;
  padding: 2.2rem !important;
  text-align: center !important;
  background: var(--bg-elev-2) !important;
  backdrop-filter: blur(12px) !important;
  transition: transform .2s ease, box-shadow .2s ease;
}
.stFileUploader > div:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-1);
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.04);
  border-radius: 6px;
}
::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--brand-1), var(--brand-2));
  border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
  filter: brightness(1.05);
}

/* ---------- Hide Streamlit Brand Bits ---------- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ---------- Utility Animations ---------- */
@keyframes floaty {
  from { transform: translateY(0px); }
  to   { transform: translateY(-3px); }
}

/* ---------- Optional Light Theme (swap by adding .theme-light to body) ---------- */
body.theme-light {
  --bg: #f6f7fb;
  --bg-elev-1: rgba(255, 255, 255, .9);
  --bg-elev-2: rgba(255, 255, 255, .78);
  --glass: rgba(255, 255, 255, .72);
  --glass-strong: rgba(255, 255, 255, .88);
  --text-1: #0f172a;
  --text-2: #334155;
  --text-3: #475569;
  --card-border: rgba(15, 23, 42, 0.08);
  --line-2: rgba(59, 130, 246, 0.45);
}
</style>

<!-- Load fonts after styles to avoid FOIT -->
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Space+Grotesk:wght@600;700;800&display=swap" rel="stylesheet">
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
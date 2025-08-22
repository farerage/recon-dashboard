# app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, date
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
TABLE = "reconciliation"

def tbl(name: str) -> str:
    """Qualified table name with schema."""
    return f'{SCHEMA}.{name}'

def ensure_schema(engine, schema: str):
    """Create schema if not exists (safe)."""
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}";'))

if SCHEMA != "public":
    try:
        ensure_schema(engine, SCHEMA)
    except Exception as e:
        st.info(f"Note: gagal membuat schema {SCHEMA}: {e}. Pastikan role DB-mu punya izin.")

# ======================
# THEME / CSS
# ======================
st.set_page_config(page_title="Reconciliation Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root{
  --brand-1:#2563eb; --brand-2:#22c55e; --brand-3:#7c3aed;
  --bg:#f7f9fc; --bg2:#eef3ff; --surface:#ffffff; --surface2:#f5f7fb;
  --text-1:#0f172a; --text-2:#334155; --text-3:#64748b;
  --line:#e5e7eb; --radius:14px; --shadow:0 10px 30px rgba(2,6,23,.06);
}
.stApp{background: linear-gradient(180deg,#fff,var(--bg2) 60%,var(--bg)) fixed; color:var(--text-1);
font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial;}
.block-container{padding-top:1rem; padding-bottom:1rem;}
section[data-testid="stSidebar"]{background:var(--surface) !important; border-right:1px solid var(--line); box-shadow:var(--shadow);}
.nav-title{font-family:'Space Grotesk',sans-serif; font-weight:800; text-align:center; margin:.25rem 0 1rem;
background:linear-gradient(90deg,var(--brand-1),var(--brand-3)); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
h1{font-family:'Space Grotesk',sans-serif !important; font-weight:900 !important; text-align:center !important;
font-size:clamp(2rem,3vw,3rem) !important; margin:.25rem 0 .75rem !important;}
.subtitle{color:var(--text-2); text-align:center; margin-bottom:1rem;}
.stButton > button{width:100%; border-radius:12px !important; padding:.7rem 1rem !important; font-weight:700 !important;
border:1px solid var(--line) !important; background:linear-gradient(180deg,#fff,var(--surface2)) !important; box-shadow:var(--shadow) !important;}
.stButton > button[kind="primary"]{background:linear-gradient(135deg,var(--brand-1),var(--brand-3)) !important; color:#fff !important; border:none !important;}
.card{background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:1.2rem; margin:1rem 0; box-shadow:var(--shadow); position:relative;}
.card::before{content:""; position:absolute; inset:0 0 auto 0; height:3px; background:linear-gradient(90deg,var(--brand-1),var(--brand-3)); border-top-left-radius:18px; border-top-right-radius:18px; opacity:.9;}
.stTextInput input, .stDateInput input, .stSelectbox select{background:#fff !important; border:1px solid var(--line) !important;
border-radius:10px !important; padding:.6rem .8rem !important;}
.stTabs [data-baseweb="tab-list"]{background:var(--surface2) !important; border:1px solid var(--line) !important; border-radius:12px !important; padding:.3rem !important;}
.stTabs [data-baseweb="tab"]{color:var(--text-3) !important; font-weight:700 !important; border-radius:10px !important; padding:.5rem .8rem !important;}
.stTabs [aria-selected="true"]{color:#fff !important; background:linear-gradient(135deg,var(--brand-1),var(--brand-2)) !important;}
.stDataFrame, .stTable{border:1px solid var(--line) !important; border-radius:12px !important; overflow:hidden !important; background:var(--surface) !important;}
/* Metric smaller font */
[data-testid="metric-container"]{background:linear-gradient(180deg,#fff,var(--surface2)) !important; border:1px solid var(--line) !important;
border-radius:12px !important; padding:.7rem .9rem !important;}
div[data-testid="stMetricValue"]{font-size:1.1rem !important; line-height:1.15 !important;}
div[data-testid="stMetricLabel"]{font-size:.78rem !important; color:var(--text-3) !important;}
#MainMenu, footer, header{visibility:hidden;}
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800;900&family=Space+Grotesk:wght@700;800;900&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# ======================
# HELPERS
# ======================
DATE_COLS = [
    'std_transaction_date', 'std_vendor_settled_date', 'last_updated', 'created'
]
NUM_COLS = [
    'std_admin_fee','std_admin_fee_invoice','std_amount','std_vendor_cost',
    'amount','balance_before','balance_after',
    'used_overdraft_before','used_overdraft_after','service_fee_paid',
    'transaction_fee_paid','service_fee_before','service_fee_after',
    'pending_balance_after','pending_balance_before','admin_fee','transfer_amount',
    'freeze_balance_before','freeze_balance_after'
]

FRONTEND_COLS = [
    'std_transaction_date', 'std_vendor', 'std_identifier', 'std_username',
    'std_admin_fee', 'std_admin_fee_invoice', 'std_amount',
    'std_vendor_cost', 'std_balance_joiner', 'std_vendor_settled_date'
]

FILTER_COLS = ['std_transaction_date', 'std_vendor', 'std_identifier', 'std_balance_joiner']

def parse_dates(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)
    return df

def normalize_numeric(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = (
                df[c].astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace(" ", "", regex=False)
            )
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def sum_by_std_transaction_date(df: pd.DataFrame) -> pd.DataFrame:
    """SUM(std_amount) grouped by date(std_transaction_date)."""
    need = {'std_transaction_date','std_amount'}
    if not need.issubset(df.columns):
        return pd.DataFrame(columns=['date','sum_std_amount'])
    d = df.copy()
    d = parse_dates(d, ['std_transaction_date'])
    d['date'] = d['std_transaction_date'].dt.date
    out = d.groupby('date', dropna=True)['std_amount'].sum(min_count=1).reset_index()
    out = out.rename(columns={'std_amount':'sum_std_amount'})
    return out.sort_values('date')

def sum_by_std_vendor_settled_date(df: pd.DataFrame) -> pd.DataFrame:
    """SUM(std_amount - std_vendor_cost) grouped by date(std_vendor_settled_date)."""
    need = {'std_vendor_settled_date','std_amount','std_vendor_cost'}
    if not need.issubset(df.columns):
        return pd.DataFrame(columns=['date','sum_net_vendor'])
    d = df.copy()
    d = parse_dates(d, ['std_vendor_settled_date'])
    d = normalize_numeric(d, ['std_amount','std_vendor_cost'])
    d['date'] = d['std_vendor_settled_date'].dt.date
    d['net_vendor'] = d['std_amount'].fillna(0) - d['std_vendor_cost'].fillna(0)
    out = d.groupby('date', dropna=True)['net_vendor'].sum(min_count=1).reset_index()
    out = out.rename(columns={'net_vendor':'sum_net_vendor'})
    return out.sort_values('date')

def sum_by_last_updated_date(df: pd.DataFrame) -> pd.DataFrame:
    """SUM(amount) grouped by date(last_updated)."""
    need = {'last_updated','amount'}
    if not need.issubset(df.columns):
        return pd.DataFrame(columns=['date','sum_amount'])
    d = df.copy()
    d = parse_dates(d, ['last_updated'])
    d = normalize_numeric(d, ['amount'])
    d['date'] = d['last_updated'].dt.date
    out = d.groupby('date', dropna=True)['amount'].sum(min_count=1).reset_index()
    out = out.rename(columns={'amount':'sum_amount'})
    return out.sort_values('date')

def compute_start_end_balances(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung starting/ending balance per hari (tanggal = date(last_updated)):
    - Starting D = Ending D-1 jika ada; kalau tidak ada, earliest balance_before di hari D (kalau ada).
    - Ending D   = latest balance_after di hari D; jika tidak ada, fallback starting + SUM(amount di hari D).
    """
    if 'last_updated' not in df.columns:
        return pd.DataFrame(columns=['date','starting_balance','ending_balance','rows'])

    d = df.copy()
    d = parse_dates(d, ['last_updated'])
    d = normalize_numeric(d, ['balance_before','balance_after','amount'])
    d['date'] = d['last_updated'].dt.date

    results = []
    prev_end = None

    for day, g in sorted(d.groupby('date'), key=lambda kv: kv[0]):
        g_sorted = g.sort_values('last_updated')

        # starting prefer previous day ending
        starting = prev_end
        if pd.isna(starting) or starting is None:
            if 'balance_before' in g_sorted.columns and g_sorted['balance_before'].notna().any():
                starting = g_sorted.loc[g_sorted['balance_before'].first_valid_index(), 'balance_before']

        # ending prefer last balance_after
        ending = None
        if 'balance_after' in g_sorted.columns and g_sorted['balance_after'].notna().any():
            ending = g_sorted.loc[g_sorted['balance_after'].last_valid_index(), 'balance_after']

        # fallback ending
        if (ending is None or pd.isna(ending)) and starting is not None:
            total_amt = g_sorted['amount'].fillna(0).sum() if 'amount' in g_sorted.columns else 0
            ending = starting + total_amt

        results.append({
            'date': day,
            'starting_balance': starting,
            'ending_balance': ending,
            'rows': int(len(g_sorted))
        })
        prev_end = ending

    return pd.DataFrame(results)

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Reconciliation Dashboard", layout="wide", initial_sidebar_state="expanded")

# ======================
# SIDEBAR NAVIGATION
# ======================
with st.sidebar:
    st.markdown('### 🎯 Navigation')
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
            # Quick stats 7 hari terakhir berbasis std_transaction_date
            qs = pd.read_sql(text(f"""
                SELECT
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT std_vendor) AS unique_vendors,
                    COUNT(DISTINCT std_identifier) AS unique_identifiers
                FROM {tbl(TABLE)}
                WHERE std_transaction_date >= CURRENT_DATE - INTERVAL '7 days'
            """), conn)
            if not qs.empty:
                st.metric("Records (7d)", f"{qs.iloc[0]['total_records']:,}")
                st.metric("Vendors (7d)", f"{qs.iloc[0]['unique_vendors']:,}")
                st.metric("Identifiers (7d)", f"{qs.iloc[0]['unique_identifiers']:,}")
    except Exception as e:
        st.info(f"Connect to view stats (schema={SCHEMA}). Detail: {e}")

# ======================
# MAIN CONTENT
# ======================
if st.session_state.current_page == 'Upload Data':
    # ======================
    # UPLOAD PAGE
    # ======================
    st.title("📤 Upload Reconciliation Data")
    st.caption("Upload CSV/Excel dengan kolom standar `std_*` + kolom operasional.")

    with st.container():
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

                # Normalize headers
                df_upload.columns = [c.strip().lower() for c in df_upload.columns]

                # Hanya ambil kolom yang dikenal
                valid_columns = [
                    # std*
                    'std_transaction_date','std_vendor','std_identifier','std_username',
                    'std_admin_fee','std_admin_fee_invoice','std_amount','std_vendor_cost',
                    'std_balance_joiner','std_vendor_settled_date',
                    # kunci & meta
                    'id','created','create_by','last_updated','last_update_by','tx_id',
                    'tx_type','username','amount','balance_flow','balance_before','balance_after',
                    'description','used_overdraft_before','used_overdraft_after','service_fee_paid',
                    'transaction_fee_paid','service_fee_before','service_fee_after',
                    'pending_balance_after','pending_balance_before','admin_fee','transfer_amount',
                    'freeze_balance_before','freeze_balance_after','recon_balance_status'
                ]
                df_upload = df_upload[[c for c in df_upload.columns if c in valid_columns]]

                # Info file
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("File Name", uploaded_file.name)
                with c2: st.metric("Total Rows", f"{len(df_upload):,}")
                with c3: st.metric("Total Columns", len(df_upload.columns))

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
                        help="Bagaimana menangani baris yang id-nya sudah ada di DB"
                    )
                with col2:
                    unique_col = "id"
                    st.text_input("Unique Identifier (fixed)", value=unique_col, disabled=True)

                # Parse dates & numeric
                df_upload = parse_dates(df_upload, DATE_COLS)
                df_upload = normalize_numeric(df_upload, NUM_COLS)

                # Upload button
                if st.button("💾 Save to Database", type="primary", use_container_width=True):
                    with st.spinner("Processing and saving data to database..."):
                        if duplicate_action == "Add All (Allow Duplicates)":
                            with engine.begin() as conn:
                                df_upload.to_sql(TABLE, conn, if_exists="append", index=False, schema=SCHEMA)
                            uploaded_count = len(df_upload)
                            duplicate_count = 0
                        else:
                            # ambil id existing
                            if 'id' not in df_upload.columns:
                                raise ValueError("Kolom 'id' wajib ada di file untuk UPSERT.")

                            unique_values = df_upload['id'].dropna().astype(str).unique()
                            with engine.connect() as conn:
                                if len(unique_values) == 0:
                                    existing_ids = set()
                                else:
                                    vals = "', '".join(v.replace("'", "''") for v in unique_values)
                                    existing_query = f"""
                                        SELECT id FROM {tbl(TABLE)}
                                        WHERE id IN ('{vals}')
                                    """
                                    try:
                                        existing_df = pd.read_sql(text(existing_query), conn)
                                        existing_ids = set(existing_df['id'].astype(str).values)
                                    except Exception:
                                        existing_ids = set()

                            df_upload['__is_dup'] = df_upload['id'].astype(str).isin(existing_ids)
                            duplicates = df_upload[df_upload['__is_dup']]
                            new_records = df_upload[~df_upload['__is_dup']]
                            duplicate_count = len(duplicates)

                            if duplicate_action == "Skip Duplicates":
                                if len(new_records) > 0:
                                    with engine.begin() as conn:
                                        new_records.drop(columns='__is_dup').to_sql(
                                            TABLE, conn, if_exists="append", index=False, schema=SCHEMA
                                        )
                                uploaded_count = len(new_records)

                            elif duplicate_action == "Update Existing":
                                # insert baru
                                if len(new_records) > 0:
                                    with engine.begin() as conn:
                                        new_records.drop(columns='__is_dup').to_sql(
                                            TABLE, conn, if_exists="append", index=False, schema=SCHEMA
                                        )
                                # upsert baris duplikat
                                if len(duplicates) > 0:
                                    duplicates_clean = duplicates.drop(columns='__is_dup')
                                    with engine.begin() as conn:
                                        # tmp table di default schema (tanpa schema=SCHEMA agar gampang drop)
                                        duplicates_clean.to_sql("temp_reconciliation", conn, if_exists="replace", index=False)
                                        columns = list(duplicates_clean.columns)
                                        columns_str = ', '.join(columns)
                                        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])
                                        upsert_query = f"""
                                            INSERT INTO {tbl(TABLE)} ({columns_str})
                                            SELECT {columns_str} FROM temp_reconciliation
                                            ON CONFLICT (id) DO UPDATE SET {update_str}
                                        """
                                        conn.execute(text(upsert_query))
                                        conn.execute(text("DROP TABLE IF EXISTS temp_reconciliation"))
                                uploaded_count = len(df_upload)

                            df_upload.drop(columns='__is_dup', inplace=True, errors='ignore')

                        # Messages
                        if duplicate_count > 0:
                            if duplicate_action == "Skip Duplicates":
                                st.success(f"✅ Uploaded {uploaded_count:,} new records. Skipped {duplicate_count:,} duplicates.")
                            elif duplicate_action == "Update Existing":
                                st.success(f"✅ Processed {uploaded_count:,} rows. Updated {duplicate_count:,} existing rows.")
                            else:
                                st.success(f"✅ Uploaded {uploaded_count:,} records!")
                        else:
                            st.success(f"✅ Uploaded {uploaded_count:,} new records.")

            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

elif st.session_state.current_page == 'Visualization':
    # ======================
    # VISUALIZATION PAGE
    # ======================
    st.title("📊 Data Visualization")
    st.caption("Visual analytics of reconciliation data")

    # Pull last 60 days by std_transaction_date
    try:
        with engine.connect() as conn:
            df_viz = pd.read_sql(text(f"""
                SELECT {", ".join(set(FRONTEND_COLS + ["last_updated","amount"]))}
                FROM {tbl(TABLE)}
                WHERE std_transaction_date >= CURRENT_DATE - INTERVAL '60 days'
            """), conn)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df_viz = pd.DataFrame()

    if not df_viz.empty:
        df_viz = parse_dates(df_viz, DATE_COLS)
        df_viz = normalize_numeric(df_viz, NUM_COLS)

        # A. Sum by std_transaction_date (std_amount)
        a = sum_by_std_transaction_date(df_viz)
        fig_a = px.bar(a, x='date', y='sum_std_amount', title="SUM(std_amount) by std_transaction_date")
        st.plotly_chart(fig_a, use_container_width=True)

        # B. Sum by std_vendor_settled_date (std_amount - std_vendor_cost)
        b = sum_by_std_vendor_settled_date(df_viz)
        fig_b = px.bar(b, x='date', y='sum_net_vendor', title="SUM(std_amount - std_vendor_cost) by std_vendor_settled_date")
        st.plotly_chart(fig_b, use_container_width=True)

        # C. Sum by last_updated date (amount)
        c = sum_by_last_updated_date(df_viz)
        fig_c = px.line(c, x='date', y='sum_amount', title="SUM(amount) by last_updated (date)")
        st.plotly_chart(fig_c, use_container_width=True)

        # D. Starting/Ending balances by last_updated
        se = compute_start_end_balances(df_viz)
        st.markdown("### 🧮 Daily Starting / Ending Balance (by last_updated)")
        if not se.empty:
            st.dataframe(se, use_container_width=True, height=300)
        else:
            st.info("No enough data to compute start/end balance.")
    else:
        st.info("📊 No data available for visualization. Please upload data first.")

else:
    # ======================
    # DASHBOARD PAGE (DEFAULT)
    # ======================
    st.title("📊 Reconciliation Dashboard")
    st.caption("Monitor and analyze your reconciliation data")

    # ---------- Filters ----------
    with st.container():
        st.markdown("### 🔍 Filters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_date = st.date_input("Start Date (std_transaction_date)", value=date(date.today().year, 1, 1))
        with col2:
            end_date = st.date_input("End Date (std_transaction_date)", value=date.today())
        with col3:
            f_vendor = st.text_input("std_vendor (contains)")
        with col4:
            f_identifier = st.text_input("std_identifier (contains)")

        col5, _c6, _c7, _c8 = st.columns(4)
        with col5:
            f_balance_joiner = st.text_input("std_balance_joiner (contains)")

    # ---------- Query data ----------
    query = f"""
        SELECT {", ".join(set(FRONTEND_COLS + ["last_updated","amount","balance_before","balance_after"]))}
        FROM {tbl(TABLE)}
        WHERE std_transaction_date BETWEEN :start_date AND :end_date
    """
    params = {"start_date": start_date, "end_date": end_date}
    if f_vendor:
        query += " AND std_vendor ILIKE :vendor"
        params["vendor"] = f"%{f_vendor}%"
    if f_identifier:
        query += " AND std_identifier ILIKE :identifier"
        params["identifier"] = f"%{f_identifier}%"
    if f_balance_joiner:
        query += " AND std_balance_joiner ILIKE :bj"
        params["bj"] = f"%{f_balance_joiner}%"

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df = pd.DataFrame()

    if not df.empty:
        df = parse_dates(df, DATE_COLS)
        df = normalize_numeric(df, NUM_COLS)

        # ---------- Summary Metrics ----------
        with st.container():
            st.markdown("### 📈 Summary Metrics")
            colm = st.columns(4)
            total_records = len(df)
            total_std_amount = df['std_amount'].sum() if 'std_amount' in df.columns else 0
            net_vendor = (df['std_amount'].fillna(0) - df['std_vendor_cost'].fillna(0)).sum() if {'std_amount','std_vendor_cost'}.issubset(df.columns) else 0
            sum_amount_by_last = df['amount'].sum() if 'amount' in df.columns else 0

            with colm[0]: st.metric("Total Records", f"{total_records:,}")
            with colm[1]: st.metric("Σ std_amount", f"{total_std_amount:,.0f}")
            with colm[2]: st.metric("Σ (std_amount - std_vendor_cost)", f"{net_vendor:,.0f}")
            with colm[3]: st.metric("Σ amount (by last_updated)", f"{sum_amount_by_last:,.0f}")

        # ---------- Aggregation Cards ----------
        with st.container():
            st.markdown("### 📆 Sum by Key Dates")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**By `std_transaction_date`**")
                a = sum_by_std_transaction_date(df)
                if not a.empty:
                    st.dataframe(a, use_container_width=True, height=220)
                else:
                    st.info("No data")

            with c2:
                st.markdown("**By `std_vendor_settled_date`** *(std_amount − std_vendor_cost)*")
                b = sum_by_std_vendor_settled_date(df)
                if not b.empty:
                    st.dataframe(b, use_container_width=True, height=220)
                else:
                    st.info("No data")

            with c3:
                st.markdown("**By `last_updated` (date)** *(sum of `amount`)*")
                c = sum_by_last_updated_date(df)
                if not c.empty:
                    st.dataframe(c, use_container_width=True, height=220)
                else:
                    st.info("No data")

        # ---------- Starting / Ending Balance ----------
        with st.container():
            st.markdown("### 🧮 Daily Starting / Ending Balance (by `last_updated`)")
            se = compute_start_end_balances(df)
            if not se.empty:
                # highlight latest day
                latest = se.dropna(subset=['ending_balance']).tail(1)
                if not latest.empty:
                    ld = latest.iloc[0]
                    cols = st.columns(3)
                    with cols[0]: st.metric("Latest Day", f"{ld['date']}")
                    with cols[1]: st.metric("Starting", f"{(ld['starting_balance'] if pd.notna(ld['starting_balance']) else 0):,.0f}")
                    with cols[2]: st.metric("Ending", f"{(ld['ending_balance'] if pd.notna(ld['ending_balance']) else 0):,.0f}")
                st.dataframe(se, use_container_width=True, height=300)
            else:
                st.info("No enough data to compute start/end balance.")

        # ---------- Data Table (columns requested) ----------
        with st.container():
            st.markdown("### 📋 Reconciliation Data (Selected Columns)")
            show_cols = [c for c in FRONTEND_COLS if c in df.columns]
            if show_cols:
                st.dataframe(df[show_cols], use_container_width=True, height=420)
                st.download_button(
                    "📥 Download Selected Columns",
                    df[show_cols].to_csv(index=False),
                    f"reconciliation_selected_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.info("Selected columns not found in dataset.")
    else:
        st.info("🔍 No data found. Please check your filters or upload data first.")

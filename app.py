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

def tbl(name: str) -> str:
    """Qualified table name with schema."""
    return f'{SCHEMA}.{name}'

def ensure_schema(engine, schema: str):
    """Create schema if not exists (safe)."""
    from sqlalchemy import text as _text
    with engine.begin() as conn:
        conn.execute(_text(f'CREATE SCHEMA IF NOT EXISTS "{schema}";'))

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
    if st.button("📈 Analytics", key="nav_analytics", use_container_width=True):
        st.session_state.current_page = 'Analytics'
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📈 Quick Stats")
    try:
        with engine.connect() as conn:
            qs = pd.read_sql(text(f"""
                SELECT 
                  COUNT(*) AS total_records,
                  COALESCE(SUM(std_amount),0) AS total_amount
                FROM {tbl('reconciliation')}
                WHERE std_transaction_date >= CURRENT_DATE - INTERVAL '7 days'
            """), conn)
            if not qs.empty:
                st.metric("Records (7d)", f"{qs.iloc[0]['total_records']:,}")
                st.metric("Sum Amount (7d)", f"{float(qs.iloc[0]['total_amount']):,.2f}")
    except Exception as e:
        st.info(f"Connect to view stats (schema={SCHEMA}). Detail: {e}")

# ======================
# HELPERS
# ======================
def parse_dates(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def coalesce(a, b):
    return a if pd.notna(a) else b

def compute_start_end_balance(df: pd.DataFrame):
    if df.empty or "last_updated" not in df.columns:
        return None, None
    tmp = df.copy()
    tmp = parse_dates(tmp, ["last_updated"])
    tmp = tmp.sort_values("last_updated")
    first = tmp.loc[tmp[["balance_after","balance_before"]].notna().any(axis=1)].head(1)
    last  = tmp.loc[tmp[["balance_after","balance_before"]].notna().any(axis=1)].tail(1)
    if first.empty or last.empty:
        return None, None
    start_val = coalesce(first.iloc[0].get("balance_after"), first.iloc[0].get("balance_before"))
    end_val   = coalesce(last.iloc[0].get("balance_after"),  last.iloc[0].get("balance_before"))
    try:
        start_val = float(start_val) if start_val is not None else None
        end_val   = float(end_val) if end_val is not None else None
    except Exception:
        pass
    return start_val, end_val

def daily_start_end_table_chained(df: pd.DataFrame):
    if df.empty or "last_updated" not in df.columns:
        return pd.DataFrame()
    d = df.copy()
    d = parse_dates(d, ["last_updated"])
    d["lu_date"] = d["last_updated"].dt.date
    rows = []
    for dte, group in d.groupby("lu_date", dropna=True):
        s, e = compute_start_end_balance(group)
        rows.append({"date": dte, "starting_balance": s, "ending_balance": e})
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    prev_end = None
    for i in range(len(out)):
        if i == 0:
            if pd.isna(out.loc[i, "starting_balance"]) and prev_end is not None:
                out.loc[i, "starting_balance"] = prev_end
        else:
            if pd.notna(prev_end):
                out.loc[i, "starting_balance"] = prev_end
        prev_end = out.loc[i, "ending_balance"] if pd.notna(out.loc[i, "ending_balance"]) else prev_end
    return out

def safe_sum_by_date(df: pd.DataFrame, col_date: str, value_col: str):
    if df.empty or col_date not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    temp = df.copy()
    temp = parse_dates(temp, [col_date])
    temp["__d"] = temp[col_date].dt.date
    g = temp.groupby("__d", dropna=True)[value_col].sum().reset_index()
    g.columns = ["date", f"sum_{value_col}"]
    return g.sort_values("date")

# ======================
# PAGES
# ======================
if st.session_state.current_page == 'Upload Data':
    st.title("📤 Upload Reconciliation Data")
    st.markdown('<p class="subtitle">Upload CSV/XLSX dengan kolom std_* dan related fields</p>', unsafe_allow_html=True)

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
                df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

                c1, c2, c3 = st.columns(3)
                with c1: st.metric("File Name", uploaded_file.name)
                with c2: st.metric("Total Rows", f"{len(df_upload):,}")
                with c3: st.metric("Total Columns", len(df_upload.columns))

                st.markdown("### 👀 Data Preview")
                st.dataframe(df_upload.head(10), use_container_width=True)

                st.markdown("### ⚙️ Upload Options")
                col1, col2 = st.columns(2)
                with col1:
                    duplicate_action = st.selectbox(
                        "Handle Duplicates:",
                        ["Skip Duplicates", "Update Existing", "Add All (Allow Duplicates)"],
                        help="ON CONFLICT pakai std_identifier (disarankan unique)"
                    )
                with col2:
                    unique_column = st.selectbox(
                        "Unique Identifier:",
                        ["std_identifier", "tx_id"],
                        help="Kolom unik untuk dedupe/UPSERT"
                    )

                if st.button("💾 Save to Database", type="primary", use_container_width=True):
                    with st.spinner("Processing and saving data to database..."):
                        # Normalisasi
                        df_upload.columns = [c.strip().lower() for c in df_upload.columns]

                        valid_columns = [
                            'std_transaction_date','std_vendor','std_identifier','std_username',
                            'std_admin_fee','std_admin_fee_invoice','std_amount','std_vendor_cost',
                            'std_balance_joiner','std_vendor_settled_date',
                            'id','created','create_by','last_updated','last_update_by','tx_id',
                            'tx_type','username','amount','balance_flow','balance_before','balance_after',
                            'description','used_overdraft_before','used_overdraft_after','service_fee_paid',
                            'transaction_fee_paid','service_fee_before','service_fee_after',
                            'pending_balance_after','pending_balance_before','admin_fee','transfer_amount',
                            'freeze_balance_before','freeze_balance_after','recon_balance_status'
                        ]
                        df_upload = df_upload[[c for c in df_upload.columns if c in valid_columns]]

                        # parse tanggal
                        df_upload = parse_dates(df_upload, ["std_transaction_date", "std_vendor_settled_date", "created", "last_updated"])

                        # numeric sanitize
                        for nc in [
                            'std_admin_fee','std_admin_fee_invoice','std_amount','std_vendor_cost',
                            'amount','balance_before','balance_after','used_overdraft_before','used_overdraft_after',
                            'service_fee_paid','transaction_fee_paid','service_fee_before','service_fee_after',
                            'pending_balance_after','pending_balance_before','admin_fee','transfer_amount',
                            'freeze_balance_before','freeze_balance_after'
                        ]:
                            if nc in df_upload.columns:
                                df_upload[nc] = pd.to_numeric(
                                    pd.Series(df_upload[nc]).astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
                                    errors="coerce"
                                )

                        unique_col = unique_column.lower()

                        if duplicate_action == "Add All (Allow Duplicates)":
                            with engine.begin() as conn:
                                df_upload.to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                            uploaded_count = len(df_upload); duplicate_count = 0
                        else:
                            if unique_col in df_upload.columns:
                                keys = df_upload[unique_col].dropna().astype(str).unique().tolist()
                                with engine.connect() as conn:
                                    if not keys:
                                        existing_ids = set()
                                    else:
                                        vals = "', '".join(k.replace("'", "''") for k in keys)
                                        q = f"SELECT DISTINCT {unique_col} FROM {tbl('reconciliation')} WHERE {unique_col} IN ('{vals}')"
                                        try:
                                            ex = pd.read_sql(text(q), conn)
                                            existing_ids = set(ex[unique_col].astype(str).tolist())
                                        except Exception:
                                            existing_ids = set()

                                df_upload["__dup"] = df_upload[unique_col].astype(str).isin(existing_ids)
                                duplicates = df_upload[df_upload["__dup"]]
                                new_records = df_upload[~df_upload["__dup"]]
                                duplicate_count = len(duplicates)

                                if duplicate_action == "Skip Duplicates":
                                    if not new_records.empty:
                                        with engine.begin() as conn:
                                            new_records.drop(columns="__dup").to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                                    uploaded_count = len(new_records)

                                else:  # Update Existing
                                    if not new_records.empty:
                                        with engine.begin() as conn:
                                            new_records.drop(columns="__dup").to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                                    if not duplicates.empty:
                                        dup_clean = duplicates.drop(columns="__dup")
                                        with engine.begin() as conn:
                                            dup_clean.to_sql("temp_reconciliation", conn, if_exists="replace", index=False)
                                            cols = list(dup_clean.columns)
                                            columns_str = ", ".join(cols)
                                            update_str = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c != unique_col])
                                            upsert = f"""
                                                INSERT INTO {tbl('reconciliation')} ({columns_str})
                                                SELECT {columns_str} FROM temp_reconciliation
                                                ON CONFLICT ({unique_col}) DO UPDATE SET {update_str}
                                            """
                                            conn.execute(text(upsert))
                                            conn.execute(text("DROP TABLE temp_reconciliation"))
                                    uploaded_count = len(df_upload)
                                df_upload.drop(columns="__dup", inplace=True)
                            else:
                                with engine.begin() as conn:
                                    df_upload.to_sql("reconciliation", conn, if_exists="append", index=False, schema=SCHEMA)
                                uploaded_count = len(df_upload); duplicate_count = 0

                        if duplicate_count > 0:
                            if duplicate_action == "Skip Duplicates":
                                st.success(f"✅ Uploaded {uploaded_count:,} new | Skipped {duplicate_count:,} dup.")
                            elif duplicate_action == "Update Existing":
                                st.success(f"✅ Processed {uploaded_count:,} | Updated {duplicate_count:,} existing.")
                            else:
                                st.success(f"✅ Uploaded {uploaded_count:,}.")
                        else:
                            st.success(f"✅ Uploaded {uploaded_count:,} rows.")

                        if duplicate_count > 0:
                            c1, c2, c3 = st.columns(3)
                            with c1: st.metric("Total Rows", f"{len(df_upload):,}")
                            with c2: st.metric("New Rows", f"{uploaded_count:,}")
                            with c3: st.metric("Duplicates", f"{duplicate_count:,}")

            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'Analytics':
    st.title("📈 Analytics")
    st.markdown('<p class="subtitle">Tabular analytics for quick comparison</p>', unsafe_allow_html=True)

    # ---------- Filters ----------
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Filters")
        c1, c2, c3 = st.columns(3)
        with c1:
            a_start = st.date_input("Start Date", value=date(2025,1,1), key="a_start")
        with c2:
            a_end = st.date_input("End Date", value=date.today(), key="a_end")
        with c3:
            a_username = st.text_input("Filter std_username (contains)", key="a_user")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Query Data ----------
    try:
        with engine.connect() as conn:
            query = f"""
                SELECT 
                    std_transaction_date,
                    std_vendor,
                    std_identifier,
                    std_username,
                    std_amount,
                    std_vendor_cost,
                    std_vendor_settled_date,
                    last_updated,
                    amount,
                    balance_before,
                    balance_after
                FROM {tbl('reconciliation')}
                WHERE std_transaction_date BETWEEN :s AND :e
            """
            params = {"s": a_start, "e": a_end}
            if a_username:
                query += " AND std_username ILIKE :u"
                params["u"] = f"%{a_username}%"

            df_viz = pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df_viz = pd.DataFrame()

    if not df_viz.empty:
        df_viz = parse_dates(df_viz, ["std_transaction_date","std_vendor_settled_date","last_updated"])

        # ==== 3 SUM TABLES (no charts), sejajar & kolom kecil ====
        cA, cB, cC = st.columns(3)

        # 1) Sum std_amount by std_transaction_date
        with cA:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("Sum Transaction Amount")
            g1 = safe_sum_by_date(df_viz, "std_transaction_date", "std_amount")
            if not g1.empty:
                st.dataframe(
                    g1.style.format({"sum_std_amount": "{:,.2f}"}),
                    use_container_width=True, height=300
                )
            else:
                st.caption("No data")
            st.markdown('</div>', unsafe_allow_html=True)

        # 2) Sum (std_amount - std_vendor_cost) by std_vendor_settled_date
        with cB:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("Sum Vendor Settlement Amount")
            tmp = df_viz.copy()
            tmp["_net_value"] = tmp["std_amount"].fillna(0) - tmp["std_vendor_cost"].fillna(0)
            g2 = safe_sum_by_date(tmp.rename(columns={"_net_value":"net_value"}),
                                  "std_vendor_settled_date", "net_value")
            if not g2.empty:
                st.dataframe(
                    g2.style.format({"sum_net_value": "{:,.2f}"}),
                    use_container_width=True, height=300
                )
            else:
                st.caption("No data")
            st.markdown('</div>', unsafe_allow_html=True)

        # 3) Sum amount by last_updated (date)
        with cC:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("Sum Settled Client Amount")
            g3 = safe_sum_by_date(df_viz, "last_updated", "amount")
            if not g3.empty:
                st.dataframe(
                    g3.style.format({"sum_amount": "{:,.2f}"}),
                    use_container_width=True, height=300
                )
            else:
                st.caption("No data")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Daily Starting/Ending Balance (chained) ---
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🧮 Daily Starting/Ending Balance (by `last_updated`, chained)")

        try:
            with engine.connect() as conn:
                df_bal = pd.read_sql(text(f"""
                    SELECT last_updated, balance_before, balance_after
                    FROM {tbl('reconciliation')}
                """), conn)   # <-- tanpa filter sama sekali
            df_bal = parse_dates(df_bal, ["last_updated"])
            dtable = daily_start_end_table_chained(df_bal)
        except Exception as e:
            st.error(f"❌ Database error (balance): {e}")
            dtable = pd.DataFrame()

        if not dtable.empty:
            st.dataframe(
                dtable.style.format({"starting_balance":"{:,.2f}", "ending_balance":"{:,.2f}"}),
                use_container_width=True, height=320
            )
        else:
            st.info("Data tidak cukup untuk menghitung starting/ending balance harian.")

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("📊 No data available. Cek filter atau rentang tanggal.")

else:
    # ============= DASHBOARD =============
    st.title("📊 Reconciliation Dashboard")
    st.markdown('<p class="subtitle">Monitor and analyze your reconciliation data</p>', unsafe_allow_html=True)

    # -------- (A) SUMMARY METRICS — ditempatkan DI ATAS filter --------
    # Ambil ringkas data untuk periode default (bisa kamu ubah bila perlu)
    default_start = date(2025, 1, 1)
    default_end = date.today()
    try:
        with engine.connect() as conn:
            summary_df = pd.read_sql(
                text(f"""
                    SELECT 
                        COALESCE(SUM(std_amount),0) AS sum_std_amount,
                        COALESCE(SUM(std_vendor_cost),0) AS sum_std_vendor_cost,
                        COALESCE(SUM(std_admin_fee),0) AS sum_std_admin_fee,
                        COALESCE(SUM(std_admin_fee_invoice),0) AS sum_std_admin_fee_invoice
                    FROM {tbl('reconciliation')}
                    WHERE std_transaction_date BETWEEN :s AND :e
                """),
                conn, params={"s": default_start, "e": default_end}
            )
            s = summary_df.iloc[0]
    except Exception as e:
        st.error(f"❌ Database connection error (summary): {e}")
        s = pd.Series({"sum_std_amount":0,"sum_std_vendor_cost":0,"sum_std_admin_fee":0,"sum_std_admin_fee_invoice":0})

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📈 Summary Metrics")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Sum std_amount", f"{float(s['sum_std_amount']):,.2f}")
        with c2: st.metric("Sum std_vendor_cost", f"{float(s['sum_std_vendor_cost']):,.2f}")
        with c3: st.metric("Sum std_admin_fee", f"{float(s['sum_std_admin_fee']):,.2f}")
        with c4: st.metric("Sum std_admin_fee_invoice", f"{float(s['sum_std_admin_fee_invoice']):,.2f}")
        st.caption("Periode default: 2025-01-01 s.d. hari ini")
        st.markdown('</div>', unsafe_allow_html=True)

    # -------- (B) FILTERS --------
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Filters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            start_date = st.date_input("Start Date", value=default_start)
        with col2:
            end_date = st.date_input("End Date", value=default_end)
        with col3:
            f_vendor = st.text_input("std_vendor")
        with col4:
            f_identifier = st.text_input("std_identifier")
        col5, _ = st.columns([1,3])
        with col5:
            f_balance_joiner = st.text_input("std_balance_joiner")
        st.markdown('</div>', unsafe_allow_html=True)

    # -------- (C) DATA --------
    base_query = f"""
        SELECT 
          std_transaction_date, std_vendor, std_identifier, std_username,
          std_admin_fee, std_admin_fee_invoice, std_amount, std_vendor_cost,
          std_balance_joiner, std_vendor_settled_date,
          last_updated, balance_before, balance_after
        FROM {tbl('reconciliation')}
        WHERE std_transaction_date BETWEEN :start_date AND :end_date
    """
    params = {"start_date": start_date, "end_date": end_date}
    if f_vendor:
        base_query += " AND std_vendor ILIKE :vendor"
        params["vendor"] = f"%{f_vendor}%"
    if f_identifier:
        base_query += " AND std_identifier ILIKE :ident"
        params["ident"] = f"%{f_identifier}%"
    if f_balance_joiner:
        base_query += " AND std_balance_joiner ILIKE :bj"
        params["bj"] = f"%{f_balance_joiner}%"

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(base_query), conn, params=params)
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        df = pd.DataFrame()

    show_cols = [
        'std_transaction_date','std_vendor','std_identifier','std_username',
        'std_admin_fee','std_admin_fee_invoice','std_amount',
        'std_vendor_cost','std_balance_joiner','std_vendor_settled_date'
    ]

    if not df.empty:
        df = parse_dates(df, ["std_transaction_date","std_vendor_settled_date","last_updated"])

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📋 Reconciliation Data (Selected Fields)")
            present_cols = [c for c in show_cols if c in df.columns]
            st.dataframe(df[present_cols].sort_values("std_transaction_date", na_position="last"),
                         use_container_width=True, height=420)
            st.download_button(
                "📥 Download Visible Fields",
                df[present_cols].to_csv(index=False),
                f"reconciliation_selected_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("🔍 No data found. Please check your filters or upload data first.")
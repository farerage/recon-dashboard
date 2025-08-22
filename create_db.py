# create_db.py
import psycopg2
import config

SCHEMA = getattr(config, "DB_SCHEMA", "public").strip() or "public"
TABLE = "reconciliation"

DDL = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
    -- id diambil dari file upload (string/uuid)
    id TEXT PRIMARY KEY,

    -- kolom std_* utama untuk frontend & filter
    std_transaction_date TIMESTAMPTZ,
    std_vendor TEXT,
    std_identifier TEXT,
    std_username TEXT,
    std_admin_fee NUMERIC(18,2),
    std_admin_fee_invoice NUMERIC(18,2),
    std_amount NUMERIC(18,2),
    std_vendor_cost NUMERIC(18,2),
    std_balance_joiner TEXT,
    std_vendor_settled_date TIMESTAMPTZ,

    -- kolom operasional
    created TIMESTAMPTZ,
    create_by TEXT,
    last_updated TIMESTAMPTZ,
    last_update_by TEXT,

    -- kolom tambahan sesuai daftar kamu
    tx_id TEXT,
    tx_type TEXT,
    username TEXT,
    amount NUMERIC(18,2),
    balance_flow TEXT,
    balance_before NUMERIC(18,2),
    balance_after NUMERIC(18,2),
    description TEXT,
    used_overdraft_before NUMERIC(18,2),
    used_overdraft_after NUMERIC(18,2),
    service_fee_paid NUMERIC(18,2),
    transaction_fee_paid NUMERIC(18,2),
    service_fee_before NUMERIC(18,2),
    service_fee_after NUMERIC(18,2),
    pending_balance_after NUMERIC(18,2),
    pending_balance_before NUMERIC(18,2),
    admin_fee NUMERIC(18,2),
    transfer_amount NUMERIC(18,2),
    freeze_balance_before NUMERIC(18,2),
    freeze_balance_after NUMERIC(18,2),
    recon_balance_status TEXT
);

-- unik opsional untuk upsert kedua pakai std_identifier
CREATE UNIQUE INDEX IF NOT EXISTS ux_{TABLE}_std_identifier
    ON {SCHEMA}.{TABLE} (std_identifier);
"""

def create_tables():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # pastikan schema
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";')

    # kalau mau benar-benar bersih, uncomment baris di bawah:
    cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{TABLE};")

    # create tabel
    cur.execute(DDL)

    cur.close()
    conn.close()
    print(f"✅ Table {SCHEMA}.{TABLE} is ready (id TEXT).")

if __name__ == "__main__":
    create_tables()

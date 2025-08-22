import psycopg2
import config

SCHEMA = getattr(config, "DB_SCHEMA", "public").strip() or "public"
TABLE = "reconciliation"

DDL = f"""
CREATE TABLE {SCHEMA}.{TABLE} (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Standardized columns (std_*)
    std_transaction_date       TIMESTAMP,
    std_vendor                 VARCHAR(120),
    std_identifier             VARCHAR(150),
    std_username               VARCHAR(120),
    std_admin_fee              NUMERIC(18,2),
    std_admin_fee_invoice      NUMERIC(18,2),
    std_amount                 NUMERIC(18,2),
    std_vendor_cost            NUMERIC(18,2),
    std_balance_joiner         VARCHAR(200),
    std_vendor_settled_date    TIMESTAMP,

    -- Audit columns
    created                    TIMESTAMP,
    create_by                  VARCHAR(120),
    last_updated               TIMESTAMP,
    last_update_by             VARCHAR(120),

    -- Transaction / balance details
    tx_id                      VARCHAR(150),
    tx_type                    VARCHAR(60),
    username                   VARCHAR(120),
    amount                     NUMERIC(18,2),
    balance_flow               VARCHAR(24),     -- e.g., IN/OUT
    balance_before             NUMERIC(18,2),
    balance_after              NUMERIC(18,2),
    description                TEXT,
    used_overdraft_before      NUMERIC(18,2),
    used_overdraft_after       NUMERIC(18,2),
    service_fee_paid           NUMERIC(18,2),
    transaction_fee_paid       NUMERIC(18,2),
    service_fee_before         NUMERIC(18,2),
    service_fee_after          NUMERIC(18,2),
    pending_balance_after      NUMERIC(18,2),
    pending_balance_before     NUMERIC(18,2),
    admin_fee                  NUMERIC(18,2),
    transfer_amount            NUMERIC(18,2),
    freeze_balance_before      NUMERIC(18,2),
    freeze_balance_after       NUMERIC(18,2),

    -- Reconciliation flag/status
    recon_balance_status       VARCHAR(60)
);
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

    # 1) Pastikan schema ada
    cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";')

    # 2) Drop tabel lama di schema yang benar (opsional; aman karena IF EXISTS)
    cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{TABLE};")

    # 3) Buat tabel baru
    cur.execute(DDL)

    # 4) Index yang direkomendasikan
    #    Jika yang unik di datamu adalah std_identifier → biarkan baris ini.
    #    Jika yang unik adalah tx_id, ganti ke (tx_id) saja.
    cur.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_{TABLE}_std_identifier
        ON {SCHEMA}.{TABLE} (std_identifier);
    """)

    # Contoh index tambahan yang sering berguna untuk query
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_std_transaction_date ON {SCHEMA}.{TABLE} (std_transaction_date);")
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_tx_id ON {SCHEMA}.{TABLE} (tx_id);")
    cur.execute(f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_username ON {SCHEMA}.{TABLE} (username);")

    cur.close()
    conn.close()
    print(f"✅ Table {SCHEMA}.{TABLE} created successfully with new columns.")

if __name__ == "__main__":
    create_tables()

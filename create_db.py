import psycopg2
import psycopg2.extras
import config

SCHEMA = getattr(config, "DB_SCHEMA", "public").strip() or "public"
TABLE = "reconciliation"

DDL = f"""
CREATE TABLE {SCHEMA}.{TABLE} (
    id SERIAL PRIMARY KEY,
    no_dash VARCHAR(50),
    payment_method_dash VARCHAR(100),
    acquirer_dash VARCHAR(100),
    transaction_date_dash TIMESTAMP,
    recon_code_dash VARCHAR(100),
    invoice_number_dash VARCHAR(100),
    type_dash VARCHAR(50),
    credit_type_dash VARCHAR(50),
    currency_dash VARCHAR(10),
    total_amount_dash NUMERIC(18,2),
    total_discount_dash NUMERIC(18,2),
    aggregator_invoicing_dash VARCHAR(100),
    total_fee_dash NUMERIC(18,2),
    net_amount_dash NUMERIC(18,2),
    settlement_schedule_dash VARCHAR(100),
    status_dash VARCHAR(50),
    remarks_dash TEXT,
    settlement_batch_number_dash VARCHAR(100),
    settlement_amount_dash NUMERIC(18,2),
    destination_bank_dash VARCHAR(100),
    destination_account_name_dash VARCHAR(200),
    destination_account_number_dash VARCHAR(100),
    created_datetime_gds TIMESTAMP,
    last_updated_datetime_gds TIMESTAMP,
    transaction_datetime_gds TIMESTAMP,
    settlement_time_gds TIMESTAMP,
    settlement_amount_gds NUMERIC(18,2),
    amount_gds NUMERIC(18,2),
    service_gds VARCHAR(100),
    sender_bank_gds VARCHAR(100),
    vendor_gds VARCHAR(100),
    transaction_status_gds VARCHAR(50),
    username_gds VARCHAR(100),
    tx_id_gds VARCHAR(100),
    ref_number_gds VARCHAR(100),
    unique_id_gds VARCHAR(100),
    va_number_gds VARCHAR(100),
    admin_fee_gds NUMERIC(18,2),
    admin_fee_invoice_gds NUMERIC(18,2),
    deduction_cost_gds NUMERIC(18,2),
    mam_child_username_gds VARCHAR(100),
    mam_parent_username_gds VARCHAR(100),
    charge_transaction_id_gds VARCHAR(100),
    _merge VARCHAR(50),
    recon_status VARCHAR(50)
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

    # 2) Drop tabel lama di schema yang benar
    cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{TABLE};")

    # 3) Buat tabel baru di schema tsb
    cur.execute(DDL)

    # 4) (Opsional tapi disarankan) Unique index untuk UPSERT di app (tx_id_gds)
    cur.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_{TABLE}_txid
        ON {SCHEMA}.{TABLE} (tx_id_gds);
    """)

    cur.close()
    conn.close()
    print(f"✅ Table {SCHEMA}.{TABLE} created successfully.")

if __name__ == "__main__":
    create_tables()

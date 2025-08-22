import psycopg2
import config

def create_tables():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS
    )
    cur = conn.cursor()

    # Drop tabel lama biar aman (opsional, bisa di-comment kalau tidak mau overwrite)
    cur.execute("DROP TABLE IF EXISTS reconciliation;")

    # Buat tabel reconciliation sesuai list kolom
    cur.execute("""
    CREATE TABLE reconciliation (
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
        created_datetime_GDS TIMESTAMP,
        last_updated_datetime_GDS TIMESTAMP,
        transaction_datetime_GDS TIMESTAMP,
        settlement_time_GDS TIMESTAMP,
        settlement_amount_GDS NUMERIC(18,2),
        amount_GDS NUMERIC(18,2),
        service_GDS VARCHAR(100),
        sender_bank_GDS VARCHAR(100),
        vendor_GDS VARCHAR(100),
        transaction_status_GDS VARCHAR(50),
        username_GDS VARCHAR(100),
        tx_id_GDS VARCHAR(100),
        ref_number_GDS VARCHAR(100),
        unique_id_GDS VARCHAR(100),
        va_number_GDS VARCHAR(100),
        admin_fee_GDS NUMERIC(18,2),
        admin_fee_invoice_GDS NUMERIC(18,2),
        deduction_cost_GDS NUMERIC(18,2),
        mam_child_username_GDS VARCHAR(100),
        mam_parent_username_GDS VARCHAR(100),
        charge_transaction_id_GDS VARCHAR(100),
        _merge VARCHAR(50),
        recon_status VARCHAR(50)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database & table created successfully.")

if __name__ == "__main__":
    create_tables()

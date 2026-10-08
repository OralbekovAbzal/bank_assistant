from app.db import conn

def get_transactions_by_account(account_id: int) -> list:
    with conn.cursor() as cur:
        cur.execute("select * from transactions where orig_id = %s or dest_id = %s",(account_id,account_id,))
        rows = cur.fetchall()
        return rows
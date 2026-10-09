from app.db import conn

def get_transactions(user_id: int, limit: int = 10) -> list:
    limit = max(1, min(limit, 50))
    with conn.cursor() as cur:
        data = []
        cur.execute(
            "select t.id, a.id, t.orig_id, t.dest_id, t.type, t.amount, t.description, t.created_at from transactions t " \
            "inner join accounts a on t.orig_id = a.id or t.dest_id = a.id " \
            "where a.user_id = %s " \
            "order by t.created_at desc " \
            "limit %s",
            (user_id, limit)
        )
        rows = cur.fetchall()
        
        for transaction_id, account_id, orig_id, dest_id, type, amount, description, created_at in rows:
            direction = "gone" if orig_id == account_id else "came"
            data.append({
                "transaction_id": transaction_id,
                "account_id": account_id,
                "direction": direction,
                "type": type,
                "amount": amount,
                "description": description,
                "created_at": created_at.isoformat()
            })
        return data
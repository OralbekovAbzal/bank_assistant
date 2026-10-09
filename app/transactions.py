from app.db import conn
from datetime import date, timedelta

def get_transactions(user_id: int, limit: int = 10, date_from: str = None, date_to: str = None) -> list:
    limit = max(1, min(limit, 50))
    with conn.cursor() as cur:
        data = []
        query_start = "select t.id, a.id, t.orig_id, t.type, t.amount, t.description, t.created_at from transactions t " \
            "inner join accounts a on t.orig_id = a.id or t.dest_id = a.id " \
            "where a.user_id = %s "
        query_end = "order by t.created_at desc " \
            "limit %s"
        params = [user_id]

        query_add = ""
        if date_from is not None:
            try:
                start = date.fromisoformat(date_from) + timedelta()
                query_add += "and t.created_at >= %s "
                params.append(start)
            except ValueError:
                return {"error": "date_from must be YYYY-MM-DD"}
            
        if date_to is not None:
            try:
                end = date.fromisoformat(date_to) + timedelta()
                query_add += "and t.created_at <= %s "
                params.append(end)
            except ValueError:
                return {"error": "date_to must be YYYY-MM-DD"}

        if date_from and date_to and start > end:
            return {"error": "date_from must be before date_to"}
        
        params.append(limit)
        cur.execute(query_start + query_add + query_end,params)
        rows = cur.fetchall()
        
        for transaction_id, account_id, orig_id, type, amount, description, created_at in rows:
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
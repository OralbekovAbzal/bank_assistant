from app.db import conn
from app.auth import get_current_user
from fastapi import Depends

def create_account(user_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("insert into accounts (user_id,balance,status) values (%s,0,'active')",(user_id,))
        conn.commit()

def get_accounts(user_id: int) -> list:
    with conn.cursor() as cur:
        cur.execute("select id, balance, status, created_at from accounts where user_id = %s", (user_id,))
        rows = cur.fetchall()
        data = []
        for account_id, balance, status, created_at in rows:
            data.append({
                "account_id": account_id,
                "balance": balance,
                "status": status,
                "created_at": created_at.isoformat()
            })
        return data
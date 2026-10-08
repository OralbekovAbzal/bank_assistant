from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from app.db import conn
import jwt
import os

bearer = HTTPBearer()
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    token = creds.credentials
    try:
        payload = jwt.decode(token,os.getenv("JWT_SECRET"),algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload["sub"])

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    encoded_jwt = jwt.encode(payload,os.getenv("JWT_SECRET"),algorithm="HS256")
    return encoded_jwt

def check_login(user_data: dict) -> int:
    with conn.cursor() as cur:
        cur.execute("select password_hash from users where phone = %s",(user_data["phone"],))
        row = cur.fetchone()
        if row is None:
            return 0
        hashed_pass = row[0]
        password_hash = PasswordHash.recommended()
        if password_hash.verify(user_data["password"],hashed_pass):
            cur.execute("select id from users where phone = %s",(user_data["phone"],))
            return cur.fetchone()[0]
        return 0
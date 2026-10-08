import psycopg
from pwdlib import PasswordHash
from google import genai
from google.genai import types
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(dbname = "bank_assistant", host = "localhost", user = "admin", password = os.getenv("DB_PASSWORD"), port = "5433", autocommit=True)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000)
)

def create_user(user_data: dict):
    with conn.cursor() as cur:
        cur.execute("select phone from users where phone = %s",(user_data["phone"],))
        rows = cur.fetchall()

        if (rows != []):
            return "User already exists!"

        password_hash = PasswordHash.recommended()
        hashed_pass = password_hash.hash(user_data["password"])
        cur.execute("insert into users (phone,name,password_hash) values (%s,%s,%s)",(user_data["phone"],user_data["name"],hashed_pass,))
        conn.commit()
        return "success"

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

def create_account(user_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("insert into accounts (user_id,balance,status) values (%s,0,'active')",(user_id,))
        conn.commit()

def get_transactions_by_account(account_id: int) -> list:
    with conn.cursor() as cur:
        cur.execute("select * from transactions where orig_id = %s or dist_id = %s",(account_id,account_id,))
        rows = cur.fetchall()
        return rows

def get_accounts(user_id: int) -> list:
    with conn.cursor() as cur:
        cur.execute("select * from accounts where user_id = %s",(user_id,))
        rows = cur.fetchall()
        return rows

def new_conversation(user_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("insert into conversations (user_id) values (%s) returning id", (user_id,))
        conversation_id = cur.fetchone()[0]
        conn.commit()
    return conversation_id

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    encoded_jwt = jwt.encode(payload,os.getenv("JWT_SECRET"),algorithm="HS256")
    return encoded_jwt

bearer = HTTPBearer()
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    token = creds.credentials
    try:
        payload = jwt.decode(token,os.getenv("JWT_SECRET"),algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload["sub"])

def get_conversation(conv_id: int, user_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("select last_interaction_id from conversations where id = %s and user_id = %s",(conv_id,user_id,))
        last_itr_id = cur.fetchone()
    if last_itr_id is None:
        raise HTTPException(status_code=404, detail="Invalid data")
    return last_itr_id[0]

def ask_gemini(message: str, prev_id: str) -> tuple:
    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=message,
        previous_interaction_id=prev_id,
    )
    return (interaction.id, interaction.output_text)

def save_turn(last_itr_id: str, message: str, conv_id: int, user_id: int, output_text: str) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("insert into messages (conversation_id,role,content) values (%s,%s,%s)", (conv_id, "user", message))
            cur.execute("insert into messages (conversation_id,role,content) values (%s,%s,%s)", (conv_id, "model", output_text))
            cur.execute("update conversations set last_interaction_id = %s where id = %s and user_id = %s", (last_itr_id, conv_id, user_id))
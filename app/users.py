from pwdlib import PasswordHash
from app.db import conn

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
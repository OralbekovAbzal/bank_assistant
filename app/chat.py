from app.db import conn
from fastapi import HTTPException

def new_conversation(user_id: int) -> int:
    with conn.cursor() as cur:
        cur.execute("insert into conversations (user_id) values (%s) returning id", (user_id,))
        conversation_id = cur.fetchone()[0]
        conn.commit()
    return conversation_id

def get_conversation(conv_id: int, user_id: int) -> str:
    with conn.cursor() as cur:
        cur.execute("select last_interaction_id from conversations where id = %s and user_id = %s",(conv_id,user_id,))
        last_itr_id = cur.fetchone()
    if last_itr_id is None:
        raise HTTPException(status_code=404, detail="Invalid data")
    return last_itr_id[0]

def save_turn(last_itr_id: str, message: str, conv_id: int, user_id: int, output_text: str) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("insert into messages (conversation_id,role,content) values (%s,%s,%s)", (conv_id, "user", message))
            cur.execute("insert into messages (conversation_id,role,content) values (%s,%s,%s)", (conv_id, "model", output_text))
            cur.execute("update conversations set last_interaction_id = %s where id = %s and user_id = %s", (last_itr_id, conv_id, user_id))

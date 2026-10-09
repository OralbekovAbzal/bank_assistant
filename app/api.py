from fastapi import FastAPI,HTTPException, Depends
from pydantic import BaseModel
from app.users import create_user
from app.chat import get_conversation, new_conversation, save_turn
from app.gemini import ask_gemini
from app.auth import check_login, create_access_token, get_current_user

class New_user(BaseModel):
    phone: str
    name: str
    password: str

class Login_user(BaseModel):
    phone: str
    password: str

class Chat_data(BaseModel):
    conv_id: int | None = None
    message: str

app = FastAPI()

@app.post("/registration")
def registration(user: New_user):
    data = user.model_dump()
    return create_user(data)

@app.post("/chat")
def chat(body: Chat_data, user_id: int = Depends(get_current_user)):
    data = body.model_dump()
    conv_id = data["conv_id"]
    message = data["message"]
    if conv_id == None:
        conv_id = new_conversation(user_id)
    prev_id = get_conversation(conv_id,user_id)
    try:
        new_id, answer = ask_gemini(message, prev_id, user_id)
    except Exception as e:
        print("Gemini error:", e)
        raise HTTPException(status_code=504,detail="Ассистент не ответил, попробуйте ещё раз")
    save_turn(new_id, message, conv_id, user_id, answer)
    return {"conv_id": conv_id ,"answer": answer}

@app.post("/login")
def login(user: Login_user):
    data = user.model_dump()
    res = check_login(data)
    if res == 0:
        raise HTTPException(401,"Login or password is invalid!")
    json = {
        "access_token": create_access_token(res),
        "token_type": "bearer"
    }
    return json
from fastapi import FastAPI,HTTPException, Depends
from pydantic import BaseModel,Field
from main import create_user,new_conversation, check_login, create_access_token, get_current_user

class New_user(BaseModel):
    phone: str
    name: str
    password: str

class Login_user(BaseModel):
    phone: str
    password: str

class Chat_data(BaseModel):
    conv_id: int = Field(ge=0)
    message: str

app = FastAPI()

@app.post("/registration")
def registration(user: New_user):
    data = user.model_dump()
    return create_user(data)

@app.get("/chat")
def chat(body: Chat_data, user_id: int = Depends(get_current_user)):
    return user_id
    

@app.post("/login")
def login(user: Login_user):
    data = user.model_dump()
    res = check_login(data)
    if res == 0:
        return "login or password is invalid"
    return create_access_token(res)
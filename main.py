from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from threading import Thread
from fastapi import Depends, FastAPI, HTTPException
from typing import List
from auth.routes import auth_router
from qna.routes import qna_router
from docqna.routes import docqna_router
from webqna.routes import webqna_router
from auth.auth import get_current_user
from db import get_db
from models import crud
from models.models import *
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(qna_router)
app.include_router(docqna_router)
app.include_router(webqna_router)

choices_mapping = {
    1: (GeneralQnAConversation, GeneralQnAChatMessage),
    2: (DocumentQnAConversation, DocumentQnAChatMessage),
    3: (WebQnAConversation, WebQnAChatMessage),
}

conversation_choices_mapping = {
    1: GeneralQnAConversation,
    2: DocumentQnAConversation,
    3: WebQnAConversation,
}


@app.get('/')
async def home():
    return {"response":"This is home route"}


@app.get("/get_titles/{choice}")
async def read_titles(choice: int, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if choice not in conversation_choices_mapping:
        raise HTTPException(status_code=400, detail="Correct the choice code")

    Conversation = conversation_choices_mapping.get(choice)
    titles = crud.get_titles(db, user=user,conversation_class=Conversation)
    return titles


@app.post("/delete_conversation/{choice}/")
async def delete_conversation_endpoint(choice: int, request_data: dict, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if choice not in conversation_choices_mapping:
        raise HTTPException(status_code=400, detail="Correct the choice code")

    Conversation = conversation_choices_mapping.get(choice)
    title = request_data.get('title')
    crud.delete_conversation(db, user=user, title=title, conversation_class=Conversation)
    return {"message": "Conversation deleted successfully"}

@app.post("/get_data/{choice}/")
async def get_data_endpoint(choice: int, request_data: dict, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    provided_title = request_data.get('title')
    if choice not in choices_mapping:
        raise HTTPException(status_code=400, detail="Correct the choice code")

    Conversation, ChatMessage = choices_mapping[choice]

    if provided_title:
        conversation_title = db.query(Conversation).filter_by(title=provided_title, user=user).first()
        
        if not conversation_title:
            raise HTTPException(status_code=400, detail="Conversation not found")
        
        conversation_id = conversation_title.id
        chat_messages = db.query(ChatMessage).filter_by(conversation_id=conversation_id).order_by(ChatMessage.timestamp).all()
        return chat_messages
    else:
        raise HTTPException(status_code=400, detail="Title not provided")

    
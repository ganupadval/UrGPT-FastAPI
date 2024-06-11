from utils.utils import retrieve_conversation, generator
from fastapi.responses import StreamingResponse
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from auth.auth import get_current_user 
from db import get_db
from models.models import GeneralQnAChatMessage, GeneralQnAConversation
qna_router= APIRouter()

@qna_router.post("/chat/")
async def streaming(request_data: dict, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt = request_data.get('prompt')
    provided_title = request_data.get('title')
    if provided_title:
        retrieved_chat_history = retrieve_conversation(
            db=db,title=provided_title, user=user, conversation_class=GeneralQnAConversation, chatmsg_class=GeneralQnAChatMessage
            )
        return StreamingResponse(generator(db=db, query=prompt, title= provided_title, chat_history=retrieved_chat_history,user=user), media_type="text/event-stream")
    else:
        return StreamingResponse(generator(db=db,query=prompt, title= None, chat_history=None,user=user), media_type="text/event-stream")
from pydantic import BaseModel
from typing import List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    hashed_password: str

class User(UserBase):
    id: int
    general_qna_conversations: List["GeneralQnAConversation"] = []
    document_qna_conversations: List["DocumentQnAConversation"] = []
    web_qna_conversations: List["WebQnAConversation"] = []

    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    user_id: int
    chat_messages: List["ChatMessage"] = []

    class Config:
        orm_mode = True

class ChatMessageBase(BaseModel):
    user_response: str
    ai_response: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class GeneralQnAConversation(Conversation):
    pass

class DocumentQnAConversation(Conversation):
    pass

class WebQnAConversation(Conversation):
    pass

class GeneralQnAChatMessage(ChatMessage):
    pass

class DocumentQnAChatMessage(ChatMessage):
    pass

class WebQnAChatMessage(ChatMessage):
    pass

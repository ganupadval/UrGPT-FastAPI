from sqlalchemy.orm import Session
from .schemas import *
from sqlalchemy.orm import Session
from .models import *

def create_user(db: Session, user: UserCreate):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_conversation(db: Session, user: str, title: str, conversation_class) -> None:
    conversation = db.query(conversation_class).filter_by(user=user, title=title).first()
    if conversation:
        db.delete(conversation)
        db.commit()


def get_titles(db: Session, user: str, conversation_class) -> List[str]:
    titles = db.query(conversation_class).filter(conversation_class.user == user).all()
    return [titles]

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_conversation(db: Session, conversation: ConversationCreate, user_id: int,conversation_class):
    db_conversation = conversation_class(**conversation.dict(), user_id=user_id)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def create_chat_message(db: Session, chat_message: ChatMessageCreate, conversation_id: int, chatmsg_class):
    db_chat_message = chatmsg_class(**chat_message.dict(), conversation_id=conversation_id)
    db.add(db_chat_message)
    db.commit()
    db.refresh(db_chat_message)
    return db_chat_message

def get_conversation(db: Session, conversation_id: int, conversation_class):
    return db.query(conversation_class).filter(conversation_class.id == conversation_id).first()

def get_chat_messages(db: Session, conversation_id: int, chatmsg_class):
    return db.query(chatmsg_class).filter(chatmsg_class.conversation_id == conversation_id).all()

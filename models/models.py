# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, index=True)
    hashed_password = Column(String)
    general_qna_conversations = relationship('GeneralQnAConversation', back_populates='user')
    document_qna_conversations = relationship('DocumentQnAConversation', back_populates='user')
    web_qna_conversations = relationship('WebQnAConversation', back_populates='user')


    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"

class GeneralQnAConversation(Base):
    __tablename__ = 'general_qna_conversations'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='general_qna_conversations')
    chat_messages = relationship('GeneralQnAChatMessage', back_populates='conversation')

    def __repr__(self):
        return f"GeneralQnAConversation - {self.user}:{self.title}"

class DocumentQnAConversation(Base):
    __tablename__ = 'document_qna_conversations'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='document_qna_conversations')
    chat_messages = relationship('DocumentQnAChatMessage', back_populates='conversation')

    def __repr__(self):
        return f"DocumentQnAConversation - {self.user}:{self.title}"
    
class WebQnAConversation(Base):
    __tablename__ = 'web_qna_conversations'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='web_qna_conversations')
    chat_messages = relationship('WebQnAChatMessage', back_populates='conversation')

    def __repr__(self):
        return f"WebQnAConversation - {self.user}:{self.title}"
    
class GeneralQnAChatMessage(Base):
    __tablename__ = 'general_qna_chat_messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('general_qna_conversations.id'))
    conversation = relationship('GeneralQnAConversation', back_populates='chat_messages')
    user_response = Column(Text, nullable=True, default='')
    ai_response = Column(Text, nullable=True, default='')
    timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"{self.conversation}: {self.id}"


class DocumentQnAChatMessage(Base):
    __tablename__ = 'document_qna_chat_messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('document_qna_conversations.id'))
    conversation = relationship('DocumentQnAConversation', back_populates='chat_messages')
    user_response = Column(Text, nullable=True, default='')
    ai_response = Column(Text, nullable=True, default='')
    timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"{self.conversation}: {self.id}"


class WebQnAChatMessage(Base):
    __tablename__ = 'web_qna_chat_messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('web_qna_conversations.id'))
    conversation = relationship('WebQnAConversation', back_populates='chat_messages')
    user_response = Column(Text, nullable=True, default='')
    ai_response = Column(Text, nullable=True, default='')
    timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"{self.conversation}: {self.id}"

# Create the tables in the database
# Base.metadata.create_all(bind=engine, checkfirst=True)


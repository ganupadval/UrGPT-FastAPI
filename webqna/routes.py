import tempfile, torch
from typing import List, Annotated
from fastapi import FastAPI, Depends, HTTPException, APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from auth.auth import get_current_user 
from db import get_db
from utils.utils import retrieve_conversation, retrival_from_vector, retrival_from_qa
from models.models import WebQnAChatMessage, WebQnAConversation
from chromadb.config import Settings
from llm import llm
import chromadb
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import  ConversationBufferWindowMemory

embeddings= HuggingFaceEmbeddings()

qa_chain=None

langchain_chroma_web = Chroma(
    collection_name="web_collection"
)


text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


webqna_router= APIRouter()

@webqna_router.post('/set_link/')
async def set_link(urls: list[str]):
    global qa_chain
    langchain_chroma_web.delete_collection()
    url=[x for x in urls]
    # url=["https://www.pinecone.io/learn/series/langchain/langchain-conversational-memory/"]
    loader = WebBaseLoader(url)
    loader.requests_per_second = 1
    docs = loader.aload()
    all_splits = text_splitter.split_documents(docs)
    langchain_chroma_web.from_documents(documents=all_splits, embedding=embeddings)
    retriever=langchain_chroma_web.as_retriver()
    qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever, 
                memory=ConversationBufferWindowMemory(
                    memory_key="chat_history",
                ),
                return_source_documents=False
            )
    return {"res": "website loaded"}

@webqna_router.post("/chat/webqna/")
async def webqna_chat(request_data: dict, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if qa_chain!=None:
            prompt = request_data.get('prompt')
            provided_title = request_data.get('title')
            if provided_title:
                retrieved_chat_history = retrieve_conversation(
                    db=db,
                    title=provided_title,
                    user=user,
                    conversation_class=WebQnAConversation,
                    chatmsg_class=WebQnAChatMessage
                    )
                return StreamingResponse(retrival_from_qa(db=db,qa_chain=qa_chain, query=prompt, title= provided_title, chat_history=retrieved_chat_history, user=user, conversation_class=WebQnAConversation,), media_type="text/event-stream")
            else:
                return StreamingResponse(retrival_from_qa(db=db,qa_chain=qa_chain, query=prompt, title= None, chat_history=None, user=user, conversation_class=WebQnAConversation,), media_type="text/event-stream")
        else:
            raise HTTPException(status_code=500, detail="provide the url first")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
    
@webqna_router.post("/chat/webqna/sim/")
async def simmilarity(request_data: dict):
    prompt = request_data.get('prompt')
    res= langchain_chroma_web.similarity_search(query=prompt)
    return res
import tempfile, torch
from typing import List
from fastapi import FastAPI, Depends, HTTPException, APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from auth.auth import get_current_user 
from db import get_db
from utils.utils import retrieve_conversation, retrival_from_vector
from models.models import DocumentQnAConversation, DocumentQnAChatMessage
from chromadb.config import Settings
from llm import llm
import chromadb

embeddings= HuggingFaceEmbeddings()

persistent_client = chromadb.Client()
#Define the chroma settings
CHROMA_SETTINGS = Settings(
    chroma_db_impl = 'duckdb+parquet',
    persist_directory = "db",
    anonymized_telemetry = False
)

langchain_chroma = Chroma(
    client=persistent_client,
    # collection_name="doc_collection",
    embedding_function=embeddings,
    client_settings=CHROMA_SETTINGS,
)


text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


docqna_router= APIRouter()

@docqna_router.post('/upload_pdf/')
async def create_upload_files(files: list[UploadFile] = File(...)):
    chunks=[]
    global langchain_chroma
    langchain_chroma.delete_collection()
    for file in files:
        #read pdf bytes 
        pdf_bytes = await file.read()
    
        # Create a temporary file and write the PDF bytes into it
        with tempfile.NamedTemporaryFile(prefix=file.filename, delete=False) as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        #load pdf into document
        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        chunk = text_splitter.split_documents(documents)
        chunks.append(chunk)
        # print(f"This is chunk {chunk}")  # Assuming text_splitter is defined elsewhere

        temp_file.close()
    document = [num for sublist in chunks for num in sublist]
    langchain_chroma.from_documents(documents=document, embedding=embeddings, collection_name="doc_collection")

    return {"res": "documents loaded"}

@docqna_router.post("/chat/docqna/")
async def docqna_chat(request_data: dict, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        prompt = request_data.get('prompt')
        provided_title = request_data.get('title')
        if provided_title:
            retrieved_chat_history = retrieve_conversation(
                db=db,
                title=provided_title,
                user=user,
                conversation_class=DocumentQnAConversation,
                chatmsg_class=DocumentQnAChatMessage
                )
            return StreamingResponse(retrival_from_vector(db=db, retriever= langchain_chroma.as_retriever(), query=prompt, title= provided_title, chat_history=retrieved_chat_history, user=user, conversation_class=DocumentQnAConversation,), media_type="text/event-stream")
        else:
            return StreamingResponse(retrival_from_vector(db=db, retriever= langchain_chroma.as_retriever(), query=prompt, title= None, chat_history=None, user=user, conversation_class=DocumentQnAConversation,), media_type="text/event-stream")
    except:
        raise HTTPException(status_code=500, detail="load document first")

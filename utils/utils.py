from llm import generate_title, memory, llm, streamer
from models.models import *
import torch, re
from threading import Thread
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.chains import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import  ConversationBufferWindowMemory
from sqlalchemy.orm import Session

choices_mapping = {
    GeneralQnAConversation: GeneralQnAChatMessage,
    DocumentQnAConversation: DocumentQnAChatMessage,
    WebQnAConversation: WebQnAChatMessage,
}

def store_message(db: Session, user_response: str, ai_response: str, conversation_id: int, chatmsg_class) -> None:
    db_message = chatmsg_class(user_response=user_response, ai_response=ai_response, conversation_id=conversation_id)
    db.add(db_message)
    db.commit()

def store_title(db: Session, title: str, user, conversation_class) -> None:
    db_conversation = conversation_class(title=title, user=user)
    db.add(db_conversation)
    db.commit()
    
def store_response( generated_text, title, prompt, user, db: Session, conversation_class):
    response = generated_text.replace('</s>', '')
    if title is None:
        title =  generate_title(response)
        store_title(db=db, title=title, user=user,conversation_class=conversation_class)
    
    conversation_obj = db.query(conversation_class).filter_by(title=title, user=user).first()
    conversation_id = conversation_obj.id
    chatmsg_class=choices_mapping.get(conversation_class)
    store_message(db=db, user_response=prompt, ai_response=response, conversation_id=conversation_id, chatmsg_class=chatmsg_class)
    return None

def retrieve_conversation(db: Session, title: str, user, conversation_class, chatmsg_class) -> ChatMessageHistory:
    # number of conversations
    num_recent_conversations = 3

    # Retrieve the most recent conversation history from the database
    conversation_obj = db.query(conversation_class).filter_by(title=title, user=user).first()
    
    if not conversation_obj:
        # Handle case where conversation is not found
        return ChatMessageHistory(messages=[])

    conversation_id = conversation_obj.id
    
    # Retrieve recent conversation messages
    conversation_context = db.query(chatmsg_class).filter(
        chatmsg_class.conversation_id == conversation_id
    ).order_by(chatmsg_class.timestamp.desc())[:num_recent_conversations]

    # Storing the retrieved data from db to model memory 
    lst = []
    for msg in conversation_context:
        input_msg = msg.user_response
        output_msg = msg.ai_response
        lst.append({"input": input_msg, "output": output_msg})
    
    for x in lst:
        inputs = {"input": x["input"]}
        outputs = {"output": x["output"]}
        memory.save_context(inputs, outputs)
    # Simulate memory.save_context(inputs, outputs) based on the example
    # (You may need to adapt this part based on your actual memory implementation)

    retrieved_chat_history = ChatMessageHistory(messages=memory.chat_memory.messages)

    return retrieved_chat_history


async def generator(db, query, title, chat_history, user):
    if chat_history is None:
        retrieved_chat_history = ChatMessageHistory(messages=[])
        torch.cuda.empty_cache()
    else:
        retrieved_chat_history = chat_history

    chain = ConversationChain(
        llm=llm,
        memory=ConversationBufferWindowMemory(
            chat_memory=retrieved_chat_history
            ),
        verbose=True
    )

    generation_kwargs = {
        "input": query,
    }
    thread = Thread(target=chain.predict, kwargs=generation_kwargs)
    thread.start()
    # print('request started')
    generated_text = ""
    for new_text in streamer:
        generated_text += new_text
        yield new_text
    # print('request finished')
    store_response(db=db,generated_text=generated_text, title=title, prompt=query, user=user, conversation_class=GeneralQnAConversation)
    torch.cuda.empty_cache()
    yield ''



async def retrival_from_vector(db, query, retriever, title, chat_history, user, conversation_class):
    if chat_history is None:
        retrieved_chat_history = ChatMessageHistory(messages=[])
        torch.cuda.empty_cache()
    else:
        retrieved_chat_history = chat_history

    qa_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=retriever, 
                    memory=ConversationBufferWindowMemory(
                        memory_key="chat_history",
                    ),
                    return_source_documents=False
                )

    def chat_thread(query): 
        qa_chain({"question": query, "chat_history":retrieved_chat_history})

    args_dict= {
        "query":query
    }
    # Create a thread with the defined function as the target
    thread = Thread(target=chat_thread, args=args_dict)
    thread.start()
    print('request started')
    generated_text = ""
    for new_text in streamer:
        generated_text += new_text
        yield new_text
    print('request finished')
    store_response(db=db,generated_text=generated_text, title=title, prompt=query, user=user, conversation_class=conversation_class)
    torch.cuda.empty_cache()
    yield ''

async def retrival_from_qa(db,qa_chain,chat_history, query, title, user, conversation_class):
    if chat_history is None:
        retrieved_chat_history = ChatMessageHistory(messages=[])
        torch.cuda.empty_cache()
    else:
        retrieved_chat_history = chat_history

    
    def chat_thread(query): 
        qa_chain({"question": query, "chat_history":retrieved_chat_history})

    args_dict= {
        "query":query
    }
    # Create a thread with the defined function as the target
    thread = Thread(target=chat_thread, args=args_dict)
    thread.start()
    print('request started')
    generated_text = ""
    for new_text in streamer:
        generated_text += new_text
        yield new_text
    print('request finished')
    store_response(db=db,generated_text=generated_text, title=title, prompt=query, user=user, conversation_class=conversation_class)
    torch.cuda.empty_cache()
    yield ''
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, APIRouter
ACCESS_TOKEN_EXPIRE_MINUTES = 30
from .passwords import *
from .auth import *
from db import get_db
from models import crud
from datetime import datetime, timedelta
from models.schemas import UserCreate

auth_router= APIRouter()
# Token endpoint
@auth_router.post("/token/")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post('/register/')
async def create_user(request: UserCreate, db: Session = Depends(get_db)):
    # Check if the username is already taken
    db_user_by_username = crud.get_user_by_username(db, username=request.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if the email is already taken
    db_user_by_email = crud.get_user_by_email(db, email=request.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password before storing it in the database
    hashed_password = get_password_hash(request.hashed_password)
    
    # Create the user in the database
    return crud.create_user(db, UserCreate(username=request.username, email=request.email, hashed_password=hashed_password))

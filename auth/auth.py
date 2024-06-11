
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
from db import get_db
from models.models import User

ALGORITHM = "HS256"
SECRET_KEY = "def123d8a4f56b20f155c71e15cdcad6"


# Dependency to get the current user based on the provided token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise credentials_exception

    return db_user

# Dependency to create JWT token
def create_jwt_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
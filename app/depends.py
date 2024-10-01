import os
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.connection import Session
from app.auth_user import UserUseCases
from database.models import UserModel
from fastapi.exceptions import HTTPException
from jose import JWTError, jwt


oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth/detail')


def get_db_session():
    try:
        session = Session()
        yield session
    finally:
        session.close()


def token_verifier(
    db_session: Session = Depends(get_db_session),
    token = Depends(oauth_scheme)
):  
    uc = UserUseCases(db_session=db_session)
    uc.verify_token(access_token=token)

    return uc


def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if user is None:
        raise credentials_exception
    return user

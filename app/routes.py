import os
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from app.schemas import User
from app.depends import get_db_session
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.depends import oauth_scheme
from jose import jwt

from database.models import UserModel


user_router = APIRouter(prefix='/auth')

class LoginRequest(BaseModel):
    username: str
    password: str


@user_router.post('/register')
def user_register(
    user: User,
    db_session: Session = Depends(get_db_session),
):
    uc = UserUseCases(db_session=db_session)
    uc.user_register(user=user)
    return JSONResponse(
        content={'msg': 'success'},
        status_code=status.HTTP_201_CREATED
    )



@user_router.post('/login')
def user_login(
    login_request: LoginRequest,
    db_session: Session = Depends(get_db_session),
):
    uc = UserUseCases(db_session=db_session)
    user = User(
        username=login_request.username,
        password=login_request.password
    )

    auth_data = uc.user_login(user=user)

    return JSONResponse(
        content=auth_data,
        status_code=status.HTTP_200_OK
    )


@user_router.get('/detail')
def get_current_user(
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):
    # Exceção padrão para erros de autenticação
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica o token JWT usando a chave secreta e algoritmo
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Verifica se o usuário existe no banco de dados
    user = db_session.query(UserModel).filter(UserModel.username == username).first()
    if user is None:
        raise credentials_exception

    # Retorna o nome do usuário logado
    return JSONResponse(content={"username": user.username}, status_code=status.HTTP_200_OK)

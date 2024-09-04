from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas import User
from app.depends import get_db_session, token_verifier
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel


user_router = APIRouter(prefix='/auth')
test_router = APIRouter(prefix='/test', dependencies=[Depends(token_verifier)])

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


@test_router.get('/test')
def test_user_verify():
    return 'It works'
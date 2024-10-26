import os
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from jose import JWTError
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, PlanilhaCreate, User
from app.depends import get_current_user, get_db_session
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from app.depends import oauth_scheme
from jose import jwt

from database.models import PanilhaModel, UserModel


user_router = APIRouter(prefix='/auth')
planilha_router = APIRouter(prefix='/planilha')


@user_router.post('/register')
def user_register(
    user: User,
    db_session: Session = Depends(get_db_session),
):
    uc = UserUseCases(db_session=db_session)
    uc.user_register(user=user)
    return JSONResponse(
        content={"message": "User created"},
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
def get_current_user_details(
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


@planilha_router.post('/register')
def create_planilha(
    planilha: PlanilhaCreate,
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):
    
    user = get_current_user(token=token, db=db_session)
    
    nova_planilha = PanilhaModel(
        nome_produto=planilha.nome_produto,
        data_venda=planilha.data_venda,
        data_pagamento=planilha.data_pagamento,
        valor_bruto=planilha.valor_bruto,
        valor_liquido=planilha.valor_liquido,
        taxa=planilha.taxa,
        forma_pagamento=planilha.forma_pagamento,
        user_id=user.id,
        categoria_produto=planilha.categoria
    )

    db_session.add(nova_planilha)
    db_session.commit()

    return JSONResponse(
        content={"message": "Dados inseridos com sucesso!"},
        status_code=status.HTTP_200_OK
    )


@planilha_router.put('/upload')
def create_planilha(
    selected_file: UploadFile = File(...),
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):
    
    user = get_current_user(token=token, db=db_session)
    
    try:
        df = pd.read_excel(selected_file.file, skiprows=range(1, 10))
        for index, row in df.iterrows():
            nova_planilha = PanilhaModel(
                nome_produto=row['NOME DO PRODUTO'],
                data_venda=row['DATA DE VENDA (DIA-MÊS-ANO)'],
                data_pagamento=row['DATA DO PAGAMENTO (DIA-MÊS-ANO)'],
                valor_bruto=row['VALOR BRUTO (R$)'],
                valor_liquido=row['VALOR LIQUIDO (R$)'],
                taxa=row['TAXA (R$)'],
                forma_pagamento=row['FORMA DE PAGAMENTO'],
                user_id=user.id,
                categoria_produto=row['CATEGORIA']
            )

            db_session.add(nova_planilha)
            db_session.commit()
    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(
        content={"message": "Dados inseridos com sucesso!"},
        status_code=status.HTTP_200_OK
    )

import os
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from jose import JWTError
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, PlanilhaCreate, User
from app.depends import get_current_user, get_data_dashboard, get_db_session
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from app.depends import oauth_scheme
from jose import jwt
from sqlalchemy import and_, func
from typing import Annotated, List

from database.models import HistoricDashboard, PlanilhaModel, UserModel


user_router = APIRouter(prefix='/auth')
planilha_router = APIRouter(prefix='/planilha')
dashboard_router = APIRouter(prefix='/dashboard')


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
    
    nova_planilha = PlanilhaModel(
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

    historic = HistoricDashboard(
        user_id=user.id,
        data_upload_planilha=datetime.now()
    )

    db_session.add(historic)
    db_session.commit()
    
    try:
        # Exel -> DataFrame
        df = pd.read_excel(selected_file.file, skiprows=range(1, 10))

        # Coverter datas para o formato correto
        df['DATA DE VENDA (DIA-MÊS-ANO)'] = pd.to_datetime(df['DATA DE VENDA (DIA-MÊS-ANO)'], format='%d-%m-%Y')
        df['DATA DO PAGAMENTO (DIA-MÊS-ANO)'] = pd.to_datetime(df['DATA DO PAGAMENTO (DIA-MÊS-ANO)'], format='%d-%m-%Y')

        # Renomear colunas para facilitar
        df.rename(columns={
            'NOME DO PRODUTO': 'nome_produto',
            'DATA DE VENDA (DIA-MÊS-ANO)': 'data_venda',
            'DATA DO PAGAMENTO (DIA-MÊS-ANO)': 'data_pagamento',
            'VALOR BRUTO (R$)': 'valor_bruto',
            'VALOR LIQUIDO (R$)': 'valor_liquido',
            'TAXA (R$)': 'taxa',
            'FORMA DE PAGAMENTO': 'forma_pagamento',
            'CATEGORIA': 'categoria_produto'
        }, inplace=True)

        df['user_id'] = user.id
        df['historic_dashboard_id'] = historic.id

        # Converter o DataFrame em uma lista de dicionários
        data_to_insert = df.to_dict(orient='records')

        # Criar um objeto para cada linha
        novas_planilhas = [PlanilhaModel(**row) for row in data_to_insert]

        # Inserção em lote (maior performance)
        db_session.bulk_save_objects(novas_planilhas)
        db_session.commit()
    except Exception as e:
        return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    return JSONResponse(
        content={"message": "Dados inseridos com sucesso!"},
        status_code=status.HTTP_200_OK
    )


@dashboard_router.get('/detail')
def get_dashboard_detail(
    date_selected: List[str] = Query(None, alias="date_selected[]"),
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):  

    user = get_current_user(token=token, db=db_session)

    filters = [PlanilhaModel.user_id==user.id]
    if date_selected:
        filter_date = [datetime.strptime(date_selected, "%m/%Y") for date_selected in date_selected]
        filter_date.sort()
        filters.append(
            func.extract('year', PlanilhaModel.data_venda).in_([date.year for date in filter_date]) &
            func.extract('month', PlanilhaModel.data_venda).in_([date.month for date in filter_date])
        )
    
    planilhas = db_session.query(PlanilhaModel).filter(and_(*filters)).order_by(PlanilhaModel.data_venda).all()

    data = get_data_dashboard(planilhas, user, db_session, filters)

    if date_selected:
        date_selected.sort()
        data['date_selected'] = date_selected
    else:
        data['date_selected'] = data['dates']

    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK
    )

    


    
        
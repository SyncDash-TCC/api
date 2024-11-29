import os
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from jose import JWTError
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, PlanilhaCreate, User, UpdateVendaRequest
from app.depends import format_currency, get_current_user, get_data_dashboard, get_db_session
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from app.depends import oauth_scheme
from jose import jwt
from sqlalchemy import and_, func
from typing import List

from database.models import HistoricDashboard, PlanilhaModel, UserModel


user_router = APIRouter(prefix='/auth')
planilha_router = APIRouter(prefix='/planilha')
dashboard_router = APIRouter(prefix='/dashboard')
historico_router = APIRouter(prefix='/historico')


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
        df = pd.read_excel(selected_file.file, skiprows=range(0, 11))

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
    id_historico: int = Query(None, alias="id_historico"),
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):  

    user = get_current_user(token=token, db=db_session)

    filters = [PlanilhaModel.user_id==user.id]
    if date_selected:
        filter_date = [datetime.strptime(date, "%m/%Y") for date in date_selected]
        filter_date.sort()
        filters.append(
            func.extract('year', PlanilhaModel.data_venda).in_([date.year for date in filter_date]) &
            func.extract('month', PlanilhaModel.data_venda).in_([date.month for date in filter_date])
        )

    if id_historico:
        filters.append(PlanilhaModel.historic_dashboard_id == id_historico)
    
    planilhas = db_session.query(PlanilhaModel).filter(and_(*filters)).order_by(PlanilhaModel.data_venda).all()

    data = get_data_dashboard(planilhas, user, db_session, filters)

    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK
    )


@planilha_router.get('/detail')
def get_planilha_detail(
    date_selected: List[str] = Query(None, alias="date_selected[]"),
    id_historico: int = Query(None, alias="id_historico"),
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):

    user = get_current_user(token=token, db=db_session)

    filters = [PlanilhaModel.user_id==user.id]
    if date_selected:
        filter_date = [datetime.strptime(date, "%m/%Y") for date in date_selected]
        filter_date.sort()
        filters.append(
            func.extract('year', PlanilhaModel.data_venda).in_([date.year for date in filter_date]) &
            func.extract('month', PlanilhaModel.data_venda).in_([date.month for date in filter_date])
        )

    if id_historico:
        filters.append(PlanilhaModel.historic_dashboard_id == id_historico)

    planilhas = (
        db_session.query(
            PlanilhaModel.id,
            func.to_char(PlanilhaModel.data_venda, 'DD/MM/YYYY').label('data_venda'),
            func.to_char(PlanilhaModel.data_pagamento, 'DD/MM/YYYY').label('data_pagamento'),
            PlanilhaModel.valor_bruto,
            PlanilhaModel.valor_liquido,
            PlanilhaModel.taxa,
            PlanilhaModel.forma_pagamento,
            PlanilhaModel.nome_produto,
            PlanilhaModel.categoria_produto,
            PlanilhaModel.historic_dashboard_id
        )
        .filter(and_(*filters))
        .order_by(PlanilhaModel.data_venda).all()
    )

    dates = db_session.query(func.date_trunc('month', PlanilhaModel.data_venda).label('month_year'))\
        .filter(PlanilhaModel.user_id == user.id)\
        .distinct()\
        .order_by(func.date_trunc('month', PlanilhaModel.data_venda))\
        .all()
    dates_formatted = [
        date[0].strftime("%m/%Y")
        for date in dates
    ]

    formatted_rows = [
        {
            "id": row.id,
            "data_venda": row.data_venda,
            "data_pagamento": row.data_pagamento,
            "valor_bruto": format_currency(row.valor_bruto),
            "valor_liquido": format_currency(row.valor_liquido),
            "taxa": format_currency(row.taxa),
            "forma_pagamento": row.forma_pagamento,
            "nome_produto": row.nome_produto,
            "categoria_produto": row.categoria_produto,
        }
        for row in planilhas
    ]

    data = {
        "planilhas": formatted_rows,
        "dates": dates_formatted
    }

    if date_selected:
        data['date_selected'] = list(dict.fromkeys(date.strftime("%m/%Y") for date in filter_date))
    else:
        data['date_selected'] = dates_formatted

    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK
    )


@historico_router.get('/detail')
def get_historico_detail(
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):

    user = get_current_user(token=token, db=db_session)

    historico = db_session.query(HistoricDashboard).filter(HistoricDashboard.user_id == user.id).all()

    data = [
        {
            "id": row.id,
            "data": row.data_upload_planilha.strftime('%d/%m/%Y'),
            "hora": row.data_upload_planilha.strftime('%H:%M:%S')
        }
        for row in historico
    ]

    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK
    )


@planilha_router.put('/update')
def update_vendas(
    data_request: UpdateVendaRequest,
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):

    user = get_current_user(token=token, db=db_session)
    
    planilha = db_session.query(PlanilhaModel).filter(
        PlanilhaModel.id == data_request.id,
        PlanilhaModel.user_id == user.id
    ).first()

    for field, value in data_request.dict(exclude_unset=True).items():
        if field == "taxa":
            planilha.taxa = value if value is not None else planilha.valor_bruto - planilha.valor_liquido
        else:
            setattr(planilha, field, value)

    db_session.commit()

    return JSONResponse(
        content={"message": "Dados atualizados com sucesso!"},
        status_code=status.HTTP_200_OK
    )



    


    
        
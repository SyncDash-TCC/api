import os
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from jose import JWTError
from sqlalchemy.orm import Session
from app.schemas import LoginRequest, PlanilhaCreate, User
from app.depends import get_current_user, get_db_session
from app.auth_user import UserUseCases
from fastapi.responses import JSONResponse
from app.depends import oauth_scheme
from jose import jwt
from sqlalchemy import func

from database.models import PanilhaModel, UserModel


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

            data_venda = datetime.strptime(row['DATA DE VENDA (DIA-MÊS-ANO)'], '%d-%m-%Y').strftime('%Y-%m-%d')
            data_pagamento = datetime.strptime(row['DATA DO PAGAMENTO (DIA-MÊS-ANO)'], '%d-%m-%Y').strftime('%Y-%m-%d')

            nova_planilha = PanilhaModel(
                nome_produto=row['NOME DO PRODUTO'],
                data_venda=data_venda,
                data_pagamento=data_pagamento,
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


@dashboard_router.get('/detail')
def get_dashboard_detail(
    token: str = Depends(oauth_scheme),
    db_session: Session = Depends(get_db_session)
):
        
    user = get_current_user(token=token, db=db_session)
    planilhas = db_session.query(PanilhaModel).filter(PanilhaModel.user_id == user.id).order_by(PanilhaModel.data_venda).all()

    unique_dates = set()
    
    for planilha in planilhas:
        year_month = planilha.data_venda.strftime("%Y-%m")
        unique_dates.add(year_month)

    year_months = list(sorted(unique_dates))

    faturamento_results = (
        db_session.query(
            func.to_char(PanilhaModel.data_venda, 'YYYY-MM').label('year_month'),
            func.sum(PanilhaModel.valor_bruto).label('total_valor_bruto'),
            func.sum(PanilhaModel.valor_liquido).label('total_valor_liquido')
        )
        .filter(
            func.to_char(PanilhaModel.data_venda, 'YYYY-MM').in_(year_months)
        )
        .group_by(func.to_char(PanilhaModel.data_venda, 'YYYY-MM')).all()
    )

    forma_pagamento_results = (
        db_session.query(
            func.to_char(PanilhaModel.data_venda, 'YYYY-MM').label('year_month'),
            PanilhaModel.forma_pagamento,
            func.sum(PanilhaModel.valor_bruto).label('total_valor')
        )
        .filter(
            func.to_char(PanilhaModel.data_venda, 'YYYY-MM').in_(year_months)
        )
        .group_by(func.to_char(PanilhaModel.data_venda, 'YYYY-MM'), PanilhaModel.forma_pagamento)
        .all()
    )

    categoria_results = (
        db_session.query(PanilhaModel.categoria_produto, func.count(PanilhaModel.id).label('total_vendas'))
        .filter(PanilhaModel.user_id == user.id)
        .group_by(PanilhaModel.categoria_produto).all()
    )

    vendas_por_mes_results = (
        db_session.query(
            func.count(PanilhaModel.id).label('total_vendas')
        )
        .filter(
            func.to_char(PanilhaModel.data_venda, 'YYYY-MM').in_(year_months)
        )
        .group_by(func.to_char(PanilhaModel.data_venda, 'YYYY-MM')).all()
    )

    produtos_servicos_results = (
        db_session.query(PanilhaModel.nome_produto, func.count(PanilhaModel.id).label('total_produto'))
        .filter(PanilhaModel.user_id == user.id)
        .group_by(PanilhaModel.nome_produto).all()
    )

    total_produtos_servico = sum(item.total_produto for item in produtos_servicos_results)

    vendas_por_mes = list(reversed([res.total_vendas for res in vendas_por_mes_results]))

    total_vendas = sum(item.total_vendas for item in categoria_results)

    categorias_data = [
        {
            "label": item.categoria_produto,
            "value": round((item.total_vendas / total_vendas) * 100, 2) if total_vendas > 0 else 0,
            "id": item.categoria_produto
        }
        for item in categoria_results
    ]

    produto_servico_data = [
        {
            "label": item.nome_produto,
            "value": round((item.total_produto / total_produtos_servico) * 100, 2) if total_produtos_servico > 0 else 0,
            "id": item.nome_produto
        }
        for item in produtos_servicos_results
    ]

    bruto_values = []
    liquido_values = []
    
    for result in faturamento_results:
        bruto_values.append(result.total_valor_bruto)
        liquido_values.append(result.total_valor_liquido)

    dates_formatted = [datetime.strptime(date, "%Y-%m").strftime("%m/%Y") for date in year_months]

    pagamento_data = {
        'Pix': [],
        'Crédito': [],
        'Débito': [],
        'Boleto': []
    }

    total_por_mes = {date: 0 for date in year_months}

    for res in forma_pagamento_results:
        total_por_mes[res.year_month] += res.total_valor

    for date in year_months:
        for metodo in pagamento_data.keys():
            valor = next((res.total_valor for res in forma_pagamento_results if res.year_month == date and res.forma_pagamento == metodo), 0)
            total_mes = total_por_mes[date]
            porcentagem = (valor / total_mes * 100) if total_mes > 0 else 0
            pagamento_data[metodo].append(porcentagem)

    data = {
        "faturamento": [{'bruto': bruto_values}, {'liquido': liquido_values}],
        "vendas_por_forma_pagamento": pagamento_data,
        "vendas_por_categoria": categorias_data,
        "vendas_por_mes": vendas_por_mes,
        "produtos_servicos": produto_servico_data,
        "dates": dates_formatted
    }

    return JSONResponse(
        content=data,
        status_code=status.HTTP_200_OK
    )

    


    
        
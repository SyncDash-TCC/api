from datetime import datetime
import os
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from database.connection import Session
from app.auth_user import UserUseCases
from database.models import PlanilhaModel, UserModel
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


def get_data_dashboard(planilhas: list, user: UserModel, db_session, filters) -> dict:

    unique_dates = set()
    
    for planilha in planilhas:
        year_month = planilha.data_venda.strftime("%Y-%m")
        unique_dates.add(year_month)

    year_months = list(sorted(unique_dates))

    faturamento_results = (
        db_session.query(
            func.date_trunc('month', PlanilhaModel.data_venda).label('year_month'),
            func.sum(PlanilhaModel.valor_bruto).label('total_valor_bruto'),
            func.sum(PlanilhaModel.valor_liquido).label('total_valor_liquido')
        )
        .filter(
            and_(*filters)
        )
        .group_by(func.date_trunc('month', PlanilhaModel.data_venda))
    )

    forma_pagamento_results = (
        db_session.query(
            func.to_char(PlanilhaModel.data_venda, 'YYYY-MM').label('year_month'),
            PlanilhaModel.forma_pagamento,
            func.sum(PlanilhaModel.valor_bruto).label('total_valor')
        )
        .filter(
            and_(*filters)
        )
        .group_by(func.to_char(PlanilhaModel.data_venda, 'YYYY-MM'), PlanilhaModel.forma_pagamento)
        .all()
    )

    categoria_results = (
        db_session.query(PlanilhaModel.categoria_produto, func.count(PlanilhaModel.id).label('total_vendas'))
        .filter(and_(*filters))
        .group_by(PlanilhaModel.categoria_produto).all()
    )

    vendas_por_mes_results = (
        db_session.query(
            func.to_char(PlanilhaModel.data_venda, 'YYYY-MM').label('year_month'),
            func.count(PlanilhaModel.id).label('total_vendas')
        )
        .filter(
            and_(*filters)
        )
        .group_by(func.to_char(PlanilhaModel.data_venda, 'YYYY-MM'))
        .order_by(func.to_char(PlanilhaModel.data_venda, 'YYYY-MM').asc())
        .all() 
    )

    produtos_servicos_results = (
        db_session.query(PlanilhaModel.nome_produto, func.count(PlanilhaModel.id).label('total_produto'))
        .filter(and_(*filters))
        .group_by(PlanilhaModel.nome_produto).all()
    )

    margem_lucro = (
        db_session.query(
            func.to_char(PlanilhaModel.data_venda, 'YYYY-MM').label('year_month'),
            func.sum(PlanilhaModel.valor_liquido).label('total_liquido'),
            func.sum(PlanilhaModel.valor_bruto).label('total_valor'),
            ((func.sum(PlanilhaModel.valor_liquido) - func.sum(PlanilhaModel.valor_bruto)) / func.sum(PlanilhaModel.valor_bruto) * 100).label('margem_lucro_percentual')
        )
        .filter(
            and_(*filters)
        )
        .group_by(func.to_char(PlanilhaModel.data_venda, 'YYYY-MM'))
        .order_by(func.to_char(PlanilhaModel.data_venda, 'YYYY-MM').asc())
        .all()
    )

    margem_lucro_percentage = []
    for item in margem_lucro:
        margem_lucro_percentage.append(round(item.margem_lucro_percentual, 2))

    total_produtos_servico = sum(item.total_produto for item in produtos_servicos_results)

    vendas_por_mes = list([res.total_vendas for res in vendas_por_mes_results])

    total_vendas = sum(item.total_vendas for item in categoria_results)

    categorias_data = [
        {
            "label": item.categoria_produto,
            "value": round((item.total_vendas / total_vendas) * 100, 2) if total_vendas > 0 else 0,
            "id": item.categoria_produto
        }
        for item in categoria_results[:6]
    ]

    if len(categoria_results) > 6:
        outros_total = sum(
            round((item.total_vendas / total_vendas) * 100, 2) if total_vendas > 0 else 0
            for item in categoria_results[6:]
        )
        categorias_data.append({
            "label": "Outros",
            "value": round(outros_total, 2),
            "id": "outros"
        })

    produto_servico_data = [
        {
            "label": item.nome_produto,
            "value": round((item.total_produto / total_produtos_servico) * 100, 2) if total_produtos_servico > 0 else 0,
            "id": item.nome_produto
        }
        for item in produtos_servicos_results[:6]
    ]

    if len(produtos_servicos_results) > 6:
        outros_total = sum(
            round((item.total_produto / total_produtos_servico) * 100, 2) if total_vendas > 0 else 0
            for item in produtos_servicos_results[6:]
        )
        produto_servico_data.append({
            "label": "Outros",
            "value": round(outros_total, 2),
            "id": "outros"
        })

    bruto_values = []
    liquido_values = []
    
    for result in faturamento_results.order_by('year_month').all():
        bruto_values.append(round(result.total_valor_bruto, 2))
        liquido_values.append(round(result.total_valor_liquido, 2))

    dates = db_session.query(func.date_trunc('month', PlanilhaModel.data_venda).label('month_year'))\
        .filter(PlanilhaModel.user_id == user.id)\
        .distinct()\
        .order_by(func.date_trunc('month', PlanilhaModel.data_venda))\
        .all()
    dates_formatted = [
        date[0].strftime("%m/%Y")
        for date in dates
    ]

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
            pagamento_data[metodo].append(round(porcentagem, 2))

    return {
        "faturamento": [{'bruto': bruto_values}, {'liquido': liquido_values}],
        "vendas_por_forma_pagamento": pagamento_data,
        "vendas_por_categoria": categorias_data,
        "vendas_por_mes": vendas_por_mes,
        "produtos_servicos": produto_servico_data,
        "margem_lucro_porcentagem": margem_lucro_percentage,
        "dates": dates_formatted,
        "date_selected": [datetime.strptime(date, '%Y-%m').strftime('%m/%Y') for date in year_months]
    }

def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

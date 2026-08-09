"""
Fixtures compartilhadas dos testes.

Os testes rodam contra o Postgres real do docker-compose (mesmo banco usado em
dev, ver DATABASE_URL no .env) — não há um Postgres "de teste" isolado neste
projeto. Para não sujar/corromper os dados de dev que já existem nesse banco,
cada teste roda dentro de uma transação (com SAVEPOINTs para tolerar os
`session.commit()` que o código da aplicação já faz) que é sempre desfeita
(rollback) no teardown, então nada escrito por um teste sobrevive a ele.
"""
import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from database.connection import engine
from database.models import Base
from app.main import app
from app.depends import get_db_session


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    # No-op se as tabelas já existirem (criadas via alembic no `make create_db`).
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    outer_transaction = connection.begin()

    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    # Padrão de SAVEPOINT: o código da aplicação chama session.commit() em
    # vários lugares (user_register, create_planilha, ...). Sem isso, o
    # primeiro commit encerraria a outer_transaction e os dados vazariam pro
    # banco de dev de verdade. Cada commit interno vira um SAVEPOINT novo.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db_session
    from fastapi.testclient import TestClient
    # raise_server_exceptions=False: replica o comportamento real em produção
    # (uvicorn sem --reload devolve 500 pro cliente em vez de derrubar o
    # processo) em vez do padrão do TestClient de repropagar a exceção pro
    # teste. Ver test_authorization::test_user_a_cannot_update_user_b_planilha.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Cria um usuário direto no banco (bypassando a rota) e devolve
    (user, senha em texto puro)."""
    from database.models import UserModel
    from app.auth_user import crypt_context

    created = []

    def _make(username: str, password: str = "senha123"):
        user = UserModel(username=username, password=crypt_context.hash(password))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created.append(user)
        return user, password

    return _make


@pytest.fixture()
def auth_token():
    """Gera um JWT válido para um username, sem depender da rota /auth/login."""
    import os
    from datetime import datetime, timedelta
    from jose import jwt

    def _token(username: str, expires_in: int = 300):
        payload = {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(minutes=expires_in),
        }
        return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

    return _token

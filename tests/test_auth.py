"""Testes de registro/login de usuário (app/auth_user.py, rotas /auth/*)."""
import uuid

from jose import jwt


def _username():
    # Regex de User.validate_username só aceita [a-zA-Z0-9]+
    return "u" + uuid.uuid4().hex[:12]


def test_register_success(client):
    username = _username()
    resp = client.post("/auth/register", json={"username": username, "password": "senha123"})
    assert resp.status_code == 201
    assert resp.json() == {"message": "User created"}


def test_register_duplicate_username_returns_409(client):
    username = _username()
    payload = {"username": username, "password": "senha123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_login_success_returns_valid_token(client):
    username = _username()
    client.post("/auth/register", json={"username": username, "password": "senha123"})

    resp = client.post("/auth/login", json={"username": username, "password": "senha123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == username
    assert "access_token" in body and body["access_token"]

    # o token emitido precisa ser um JWT válido, assinado com o sub certo
    import os
    payload = jwt.decode(
        body["access_token"],
        os.getenv("SECRET_KEY"),
        algorithms=[os.getenv("ALGORITHM")],
    )
    assert payload["sub"] == username


def test_login_wrong_password_returns_401(client):
    username = _username()
    client.post("/auth/register", json={"username": username, "password": "senha123"})

    resp = client.post("/auth/login", json={"username": username, "password": "senha-errada"})
    assert resp.status_code == 401


def test_login_nonexistent_user_returns_401(client):
    resp = client.post("/auth/login", json={"username": _username(), "password": "qualquer"})
    assert resp.status_code == 401


def test_register_rejects_special_characters_in_username(client):
    resp = client.post("/auth/register", json={"username": "user@name!", "password": "senha123"})
    assert resp.status_code == 422


def test_protected_route_without_token_is_rejected(client):
    resp = client.get("/dashboard/detail")
    assert resp.status_code == 401


def test_protected_route_with_garbage_token_is_rejected(client):
    resp = client.get("/dashboard/detail", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_login_migrates_legacy_sha256_hash_to_bcrypt(client, db_session):
    """Usuários com hash antigo (sha256_crypt, esquema anterior a esta
    revisão) continuam logando normalmente e são migrados pra bcrypt de
    forma transparente no primeiro login pós-migração."""
    from passlib.context import CryptContext
    from database.models import UserModel

    legacy_context = CryptContext(schemes=['sha256_crypt'])
    username = _username()
    user = UserModel(username=username, password=legacy_context.hash("senha123"))
    db_session.add(user)
    db_session.commit()
    assert user.password.startswith("$5$")  # sha256_crypt

    resp = client.post("/auth/login", json={"username": username, "password": "senha123"})
    assert resp.status_code == 200

    db_session.refresh(user)
    assert user.password.startswith("$2b$")  # bcrypt

    # e o hash novo continua validando a mesma senha
    resp2 = client.post("/auth/login", json={"username": username, "password": "senha123"})
    assert resp2.status_code == 200

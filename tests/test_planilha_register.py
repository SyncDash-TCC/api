"""Testes do registro manual de uma venda (POST /planilha/register)."""
import uuid

from database.models import PlanilhaModel


def _username():
    return "u" + uuid.uuid4().hex[:12]


def _payload(**overrides):
    payload = {
        "nome_produto": "Produto Manual",
        "data_venda": "2026-03-01",
        "data_pagamento": "2026-03-05",
        "valor_bruto": "150.50",
        "valor_liquido": "140.00",
        "taxa": "10.50",
        "forma_pagamento": "Pix",
        "categoria": "Categoria A",
    }
    payload.update(overrides)
    return payload


def test_register_single_sale_success(client, make_user, auth_token, db_session):
    user, _ = make_user(_username())
    token = auth_token(user.username)

    resp = client.post(
        "/planilha/register",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(),
    )
    assert resp.status_code == 200

    row = db_session.query(PlanilhaModel).filter(
        PlanilhaModel.user_id == user.id
    ).one()
    assert row.nome_produto == "Produto Manual"
    assert row.valor_bruto == 150.5
    assert row.valor_liquido == 140.0


def test_register_single_sale_accepts_comma_decimal_separator(client, make_user, auth_token):
    """A UI manda o valor bruto como veio do input, que pode ter vírgula
    (ex: "150,50") — o schema normaliza antes de validar como float."""
    user, _ = make_user(_username())
    token = auth_token(user.username)

    resp = client.post(
        "/planilha/register",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(valor_bruto="150,50"),
    )
    assert resp.status_code == 200


def test_register_single_sale_with_invalid_number_returns_422_not_500(
    client, make_user, auth_token
):
    user, _ = make_user(_username())
    token = auth_token(user.username)

    resp = client.post(
        "/planilha/register",
        headers={"Authorization": f"Bearer {token}"},
        json=_payload(valor_bruto="não é um número"),
    )
    assert resp.status_code == 422

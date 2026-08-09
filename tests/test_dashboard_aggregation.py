"""Testes de agregação do dashboard (app/depends.py::get_data_dashboard)."""
import uuid
from datetime import date

from database.models import PlanilhaModel


def _username():
    return "u" + uuid.uuid4().hex[:12]


def _add_planilha(db_session, user_id, **overrides):
    defaults = dict(
        nome_produto="Produto A",
        data_venda=date(2026, 1, 15),
        data_pagamento=date(2026, 1, 20),
        valor_bruto=100.0,
        valor_liquido=95.0,
        taxa=5.0,
        forma_pagamento="Pix",
        categoria_produto="Categoria A",
        user_id=user_id,
    )
    defaults.update(overrides)
    row = PlanilhaModel(**defaults)
    db_session.add(row)
    return row


def test_dashboard_totals_match_seeded_data(client, make_user, auth_token, db_session):
    user, _ = make_user(_username())

    _add_planilha(db_session, user.id, valor_bruto=100.0, valor_liquido=95.0)
    _add_planilha(db_session, user.id, valor_bruto=200.0, valor_liquido=180.0)
    _add_planilha(
        db_session, user.id, valor_bruto=50.0, valor_liquido=45.0,
        categoria_produto="Categoria B",
    )
    db_session.commit()

    token = auth_token(user.username)
    resp = client.get("/dashboard/detail", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["vendas_total"] == 3
    assert data["faturamento_bruto_total"] == 350.0
    assert data["faturamento_liquido_total"] == 320.0
    assert data["produto_mais_vendido"] == "Produto A"


def test_dashboard_categoria_percentages_sum_to_100(client, make_user, auth_token, db_session):
    user, _ = make_user(_username())

    _add_planilha(db_session, user.id, categoria_produto="Categoria A")
    _add_planilha(db_session, user.id, categoria_produto="Categoria A")
    _add_planilha(db_session, user.id, categoria_produto="Categoria B")
    _add_planilha(db_session, user.id, categoria_produto="Categoria B")
    db_session.commit()

    token = auth_token(user.username)
    resp = client.get("/dashboard/detail", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    categorias = resp.json()["vendas_por_categoria"]

    assert {c["label"] for c in categorias} == {"Categoria A", "Categoria B"}
    assert all(c["value"] == 50.0 for c in categorias)


def test_dashboard_with_no_data_does_not_error(client, make_user, auth_token):
    user, _ = make_user(_username())
    token = auth_token(user.username)

    resp = client.get("/dashboard/detail", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendas_total"] is None or data["vendas_total"] == 0
    assert data["vendas_por_categoria"] == []

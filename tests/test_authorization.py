"""Testes de autorização: usuário A não pode ver/editar dados de usuário B."""
import uuid
from datetime import date

from database.models import PlanilhaModel


def _username():
    return "u" + uuid.uuid4().hex[:12]


def _add_planilha(db_session, user_id, categoria="Categoria A"):
    row = PlanilhaModel(
        nome_produto="Produto de B",
        data_venda=date(2026, 2, 10),
        data_pagamento=date(2026, 2, 15),
        valor_bruto=999.0,
        valor_liquido=900.0,
        taxa=99.0,
        forma_pagamento="Pix",
        categoria_produto=categoria,
        user_id=user_id,
    )
    db_session.add(row)
    return row


def test_user_a_dashboard_does_not_include_user_b_data(client, make_user, auth_token, db_session):
    user_a, _ = make_user(_username())
    user_b, _ = make_user(_username())

    _add_planilha(db_session, user_b.id)
    db_session.commit()

    token_a = auth_token(user_a.username)
    resp = client.get("/dashboard/detail", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendas_total"] in (None, 0)


def test_user_a_planilha_list_does_not_include_user_b_rows(
    client, make_user, auth_token, db_session
):
    user_a, _ = make_user(_username())
    user_b, _ = make_user(_username())

    _add_planilha(db_session, user_b.id)
    db_session.commit()

    token_a = auth_token(user_a.username)
    resp = client.get("/planilha/detail", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["planilhas"] == []


def test_user_a_cannot_update_user_b_planilha(client, make_user, auth_token, db_session):
    user_a, _ = make_user(_username())
    user_b, _ = make_user(_username())

    planilha_b = _add_planilha(db_session, user_b.id)
    db_session.commit()
    db_session.refresh(planilha_b)

    token_a = auth_token(user_a.username)
    resp = client.put(
        "/planilha/update",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "id": planilha_b.id,
            "nome_produto": "Produto Hackeado",
            "data_venda": "2026-02-10",
            "data_pagamento": "2026-02-15",
            "valor_bruto": 1.0,
            "valor_liquido": 1.0,
            "taxa": 0.0,
            "forma_pagamento": "Pix",
            "categoria_produto": "Categoria A",
        },
    )
    # A rota filtra por user_id, então a planilha de B não é encontrada pra A
    # e a atualização é recusada (antes da correção isso derrubava com 500
    # não tratado — ver update_vendas em app/routes.py).
    assert resp.status_code == 404

    db_session.refresh(planilha_b)
    assert planilha_b.nome_produto == "Produto de B"


def test_update_nonexistent_planilha_returns_404_not_500(client, make_user, auth_token):
    user, _ = make_user(_username())
    token = auth_token(user.username)

    resp = client.put(
        "/planilha/update",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "id": 999999999,
            "nome_produto": "Produto Fantasma",
            "data_venda": "2026-02-10",
            "data_pagamento": "2026-02-15",
            "valor_bruto": 1.0,
            "valor_liquido": 1.0,
            "taxa": 0.0,
            "forma_pagamento": "Pix",
            "categoria_produto": "Categoria A",
        },
    )
    assert resp.status_code == 404

#!/bin/sh
set -e

# Aplica migrations pendentes a cada boot. Idempotente (alembic só roda o que
# ainda não foi aplicado), então é seguro rodar em todo cold start do free tier.
pipenv run alembic upgrade head

# $PORT é injetada pela plataforma de deploy (Render, Railway, etc). Localmente
# (fora do docker-compose, que já sobrescreve o CMD) cai no default 8000.
# WEB_CONCURRENCY controla quantos workers do uvicorn sobem; em planos free
# com pouca RAM, o padrão seguro é 1.
exec pipenv run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}"

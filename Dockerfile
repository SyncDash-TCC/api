FROM python:3.12

WORKDIR /app

# Copia só o Pipfile/Pipfile.lock primeiro (cache de layer do Docker: só
# reinstala dependências quando eles mudam, não a cada mudança de código).
# Pipfile.lock é a ÚNICA fonte de verdade de versão de dependência do
# projeto — instala exatamente o que está travado nele (--deploy falha se
# Pipfile.lock estiver desatualizado em relação ao Pipfile, em vez de
# re-resolver versões novas silenciosamente).
COPY Pipfile Pipfile.lock /app/

RUN python -m pip install --upgrade pipenv
RUN pipenv install --dev --deploy --ignore-pipfile

COPY . /app/

RUN mkdir -p collected_static/ && mkdir -p media/public/ && mkdir -p media/private/

RUN apt-get update && apt-get install -y make

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Este CMD é o que roda em produção (Render/Railway/etc via `docker build` puro):
# aplica migrations e sobe uvicorn sem --reload, respeitando $PORT.
# Localmente, `docker-compose.yml` sobrescreve isso com `command:` para manter
# hot-reload no dia a dia — não precisa mexer aqui pra desenvolver.
CMD ["/app/entrypoint.sh"]

FROM python:3.12

WORKDIR /app

COPY requirements.txt /app/

RUN python -m pip install --upgrade pipenv

RUN pipenv install -r /app/requirements.txt

COPY . /app/

RUN mkdir -p collected_static/ && mkdir -p media/public/ && mkdir -p media/private/
RUN pipenv install flake8 --dev

RUN apt-get update && apt-get install -y make

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Este CMD é o que roda em produção (Render/Railway/etc via `docker build` puro):
# aplica migrations e sobe uvicorn sem --reload, respeitando $PORT.
# Localmente, `docker-compose.yml` sobrescreve isso com `command:` para manter
# hot-reload no dia a dia — não precisa mexer aqui pra desenvolver.
CMD ["/app/entrypoint.sh"]
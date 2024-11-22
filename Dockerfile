FROM python:3.12

WORKDIR /app

COPY requirements.txt /app/

RUN python -m pip install --upgrade pipenv psycopg2

COPY . /app/

RUN apt-get update && apt-get install -y make gcc libpq-dev && apt-get clean

RUN mkdir -p collected_static/ && mkdir -p media/public/ && mkdir -p media/private/

RUN pipenv run alembic upgrade head

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

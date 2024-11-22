FROM python:3.12

WORKDIR /app

# Certifique-se de que o arquivo `requirements.txt` está no mesmo diretório que o Dockerfile
COPY requirements.txt /app/

# Instale e atualize pipenv
RUN python -m pip install --upgrade pipenv

# Instale as dependências do requirements.txt
RUN pipenv install -r /app/requirements.txt

# Copie o restante dos arquivos do projeto
COPY . /app/

RUN mkdir -p collected_static/ && mkdir -p media/public/ && mkdir -p media/private/
RUN pipenv install flake8 --dev

# Instalar make se necessário
RUN apt-get update && apt-get install -y make
RUN pipenv run alembic upgrade head
RUN docker-compose exec api pipenv run alembic revision --autogenerate -m "replace username with email"
RUN docker-compose exec api pipenv run alembic upgrade head

EXPOSE 8000

# Execute o aplicativo com uvicorn
CMD ["pipenv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
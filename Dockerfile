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

EXPOSE 8000

# Execute o aplicativo com uvicorn
CMD ["pipenv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
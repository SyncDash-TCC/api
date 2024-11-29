FROM python:3.12

WORKDIR /app

COPY requirements.txt /app/

RUN python -m pip install --upgrade pipenv

RUN pipenv install -r /app/requirements.txt

COPY . /app/

RUN mkdir -p collected_static/ && mkdir -p media/public/ && mkdir -p media/private/
RUN pipenv install flake8 --dev

RUN apt-get update && apt-get install -y make

EXPOSE 8000

# CMD ["sh", "-c", "make create_db && make makemigrations-prod && make migrate-prod && pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"]
CMD ["pipenv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
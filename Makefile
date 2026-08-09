r-env:
	pipenv shell

run-dev:
	docker rm api &\
	docker compose run --name api --rm --service-ports api

build:
	docker compose build

create_db:
	pipenv run alembic upgrade head

bash:
	docker exec -it api bash

linter:
	docker compose run api pipenv run flake8

test:
	docker compose run api pipenv run pytest

makemigrations:
	docker-compose exec api pipenv run alembic revision --autogenerate -m "Initial migration"

migrate:
	docker-compose exec api pipenv run alembic upgrade head

makemigrations-prod:
	pipenv run alembic revision --autogenerate -m "Initial migration"

migrate-prod:
	pipenv run alembic upgrade head

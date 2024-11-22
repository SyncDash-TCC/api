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
	docker compose run api flake8

makemigrations:
	docker-compose exec api pipenv run alembic revision --autogenerate -m "replace username with email"

migrate:
	docker-compose exec api pipenv run alembic upgrade head

r-env:
	pipenv shell

run-dev:
	docker rm api &\
	docker compose run --name api --rm --service-ports api

build:
	docker compose build

create_db:
	alembic upgrade head

bash:
	docker exec -it api bash

linter:
	docker compose run api flake8

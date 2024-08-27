r-env:
	pipenv shell

run-dev:
	docker rm api &\
	docker compose run --name api --rm --service-ports api

build:
	docker compose build

create_db:
	python database/init_db.py

bash:
	docker exec -it api bash

linter:
	docker compose run api flake8

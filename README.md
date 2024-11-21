# SyncDash

# How to run

- Create file `.env`
- Run `make r-env`
- Run `make build`
- Run `make run-dev`
- Run `make create_db`

# How to linter

- If you want to run just linter, run `make linter`

# How to run migrations

- alembic revision --autogenerate -m `<nome_migration>`
- alembic upgrade head


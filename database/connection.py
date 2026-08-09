from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = getenv("DATABASE_URL")

# Alguns provedores (Render, Heroku) ainda entregam a connection string com o
# esquema legado "postgres://", que o SQLAlchemy 1.4+ não aceita mais.
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# pool_size baixo pensando em planos free (ex: Render free = 512MB RAM,
# Postgres free = poucas conexões simultâneas disponíveis).
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)
SessionLocal = sessionmaker(bind=engine)

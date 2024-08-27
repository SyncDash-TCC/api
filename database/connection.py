from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
from os import getenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


DATABSE_URL = getenv("DATABASE_URL")

engine = create_async_engine(DATABSE_URL)
async_session = sessionmaker(engine, class_=AsyncSession)
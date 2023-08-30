from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, DB_SCHEMA

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base(metadata=MetaData(schema=DB_SCHEMA))

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()

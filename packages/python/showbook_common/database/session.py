import os
from typing import AsyncGenerator
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager

class DatabaseSessionManager:
    def __init__(self):
        self.engine = None
        self.AsyncSessionLocal = None

    def init(self, database_url: str, testing: bool = False):
        pool_kwargs = {}
        if testing or os.getenv("TESTING") == "true":
            pool_kwargs["poolclass"] = NullPool
        else:
            pool_kwargs["pool_pre_ping"] = True
            pool_kwargs["pool_size"] = 5

        connect_args = {"ssl": False} if "localhost" not in database_url and "127.0.0.1" not in database_url else {}

        self.engine = create_async_engine(
            database_url,
            echo=False,
            connect_args=connect_args,
            **pool_kwargs
        )

        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.AsyncSessionLocal = None

    async def check_db_connection(self) -> None:
        if self.engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized. Call init() first.")
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        if self.AsyncSessionLocal is None:
            raise RuntimeError("DatabaseSessionManager is not initialized. Call init() first.")
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    @asynccontextmanager
    async def get_db_context(self) -> AsyncGenerator[AsyncSession, None]:
        if self.AsyncSessionLocal is None:
            raise RuntimeError("DatabaseSessionManager is not initialized. Call init() first.")
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()


db_manager = DatabaseSessionManager()


@asynccontextmanager
async def transaction_scope(db: AsyncSession):
    if db.in_transaction():
        try:
            yield
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    else:
        async with db.begin():
            yield

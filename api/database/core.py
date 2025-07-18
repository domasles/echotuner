"""
Database core functionality.
SQLAlchemy engine, session management, and connection handling.
"""

import logging

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from config import app_constants

logger = logging.getLogger(__name__)
Base = declarative_base()

class DatabaseCore:
    """Core database functionality with SQLAlchemy async engine."""

    def __init__(self):
        """Initialize the database core."""

        self.database_url = f"sqlite+aiosqlite:///{Path(app_constants.DATABASE_FILEPATH).as_posix()}"

        self.async_session_factory = None
        self.engine = None

    async def initialize(self):
        """Initialize database engine and session factory."""

        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
                connect_args={"check_same_thread": False}
            )

            self.async_session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database core initialized successfully with SQLAlchemy ORM")

        except Exception as e:
            logger.error(f"Failed to initialize database core: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""

        if not self.async_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()

            except Exception:
                await session.rollback()
                raise

            finally:
                await session.close()
    
    async def execute_raw_sql(self, query: str, params: tuple = None) -> any:
        """Execute raw SQL query (for migration compatibility)."""
        
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result
        
    async def close(self):
        """Close database connections."""

        if self.engine:
            await self.engine.dispose()
            logger.info("Database core connections closed")

db_core = DatabaseCore()

def get_session():
    """Get an async database session context manager."""

    return db_core.get_session()

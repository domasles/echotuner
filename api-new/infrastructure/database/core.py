"""
Clean Database Service - Only Connection Management
No domain knowledge, just database core functionality.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from infrastructure.singleton import SingletonServiceBase
from infrastructure.config import app_constants

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

            # Create all tables
            async with self.engine.begin() as conn:
                from infrastructure.database.models import Base as ModelsBase
                await conn.run_sync(ModelsBase.metadata.create_all)

            logger.debug("Database core initialized successfully with SQLAlchemy ORM")

        except Exception as e:
            logger.error(f"Database core initialization failed: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create and provide a database session with proper cleanup."""
        if not self.async_session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        """Close database connections and clean up resources."""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("Database core connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")

# Global database core instance
db_core = DatabaseCore()

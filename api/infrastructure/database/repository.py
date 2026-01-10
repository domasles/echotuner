"""
Generic Repository Pattern - Pure Database Access Layer
Provides CRUD operations without domain knowledge.
"""

import logging
from typing import Type, Optional, List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func, delete, update
from sqlalchemy.orm import selectinload

from .core import db_core

logger = logging.getLogger(__name__)


class GenericRepository:
    """
    Pure, generic database repository.
    Knows nothing about domain models - just provides CRUD operations.
    """

    async def create(self, model_class: Type[Any], data: Dict[str, Any]) -> Any:
        """Create a new record."""
        async with db_core.get_session() as session:
            instance = model_class(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    async def get_by_id(self, model_class: Type[Any], id_value: Any) -> Optional[Any]:
        """Get record by ID."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class).where(model_class.id == id_value))
            return result.scalar_one_or_none()

    async def get_by_field(self, model_class: Type[Any], field: str, value: Any) -> Optional[Any]:
        """Get record by any field."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class).where(getattr(model_class, field) == value))
            return result.scalar_one_or_none()

    async def get_by_conditions(self, model_class: Type[Any], conditions: Dict[str, Any]) -> Optional[Any]:
        """Get record by multiple conditions."""
        async with db_core.get_session() as session:
            query = select(model_class)
            for field, value in conditions.items():
                query = query.where(getattr(model_class, field) == value)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def list_all(self, model_class: Type[Any]) -> List[Any]:
        """List all records."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class))
            return list(result.scalars().all())

    async def list_by_field(self, model_class: Type[Any], field: str, value: Any) -> List[Any]:
        """List records by field value."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class).where(getattr(model_class, field) == value))
            return list(result.scalars().all())

    async def list_with_conditions(
        self,
        model_class: Type[Any],
        conditions: Dict[str, Any],
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[Any]:
        """List records with multiple conditions."""
        async with db_core.get_session() as session:
            query = select(model_class)

            # Apply conditions
            for field, value in conditions.items():
                if isinstance(value, list):
                    query = query.where(getattr(model_class, field).in_(value))
                else:
                    query = query.where(getattr(model_class, field) == value)

            # Apply ordering
            if order_by:
                query = query.order_by(getattr(model_class, order_by))

            # Apply limit
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update(
        self, model_class: Type[Any], id_value: Any, data: Dict[str, Any], id_field: str = "id"
    ) -> Optional[Any]:
        """Update record by ID field."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class).where(getattr(model_class, id_field) == id_value))
            instance = result.scalar_one_or_none()

            if instance:
                for field, value in data.items():
                    setattr(instance, field, value)
                await session.commit()
                await session.refresh(instance)

            return instance

    async def update_by_conditions(
        self, model_class: Type[Any], conditions: Dict[str, Any], data: Dict[str, Any]
    ) -> int:
        """Update records by conditions. Returns number of affected rows."""
        async with db_core.get_session() as session:
            query = update(model_class)

            for field, value in conditions.items():
                query = query.where(getattr(model_class, field) == value)

            query = query.values(**data)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount

    async def delete(self, model_class: Type[Any], id_value: Any, id_field: str = "id") -> bool:
        """Delete record by primary key field."""
        async with db_core.get_session() as session:
            result = await session.execute(select(model_class).where(getattr(model_class, id_field) == id_value))
            instance = result.scalar_one_or_none()

            if instance:
                await session.delete(instance)
                await session.commit()
                return True
            return False

    async def delete_by_conditions(self, model_class: Type[Any], conditions: Dict[str, Any]) -> int:
        """Delete records by conditions. Returns number of deleted rows."""
        async with db_core.get_session() as session:
            query = delete(model_class)

            for field, value in conditions.items():
                query = query.where(getattr(model_class, field) == value)

            result = await session.execute(query)
            await session.commit()
            return result.rowcount

    async def count(self, model_class: Type[Any], conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count records."""
        async with db_core.get_session() as session:
            query = select(func.count()).select_from(model_class)

            if conditions:
                for field, value in conditions.items():
                    query = query.where(getattr(model_class, field) == value)

            result = await session.execute(query)
            return result.scalar()

    async def exists(self, model_class: Type[Any], conditions: Dict[str, Any]) -> bool:
        """Check if record exists."""
        count = await self.count(model_class, conditions)
        return count > 0


# Global repository instance
repository = GenericRepository()

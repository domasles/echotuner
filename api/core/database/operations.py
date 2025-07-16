"""
Database operation decorators and base classes.
Eliminates code duplication and standardizes database operations.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, func

from core.database.decorators import db_write_operation, db_read_operation

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseOperationError(Exception):
    """Custom exception for database operations."""
    pass

class EntityNotFoundError(DatabaseOperationError):
    """Raised when an entity is not found."""
    pass

class OperationFailedError(DatabaseOperationError):
    """Raised when a database operation fails."""
    pass


# Alias for backward compatibility
db_operation = db_write_operation

class BaseCRUDMixin:
    """
    Base mixin providing common CRUD operations for database entities.
    """
    
    @staticmethod
    async def create_entity(session: AsyncSession, model_class, data: Dict[str, Any]):
        """Create a new entity."""
        entity = model_class(**data)
        session.add(entity)
        return entity
    
    @staticmethod
    async def get_entity_by_id(session: AsyncSession, model_class, entity_id: str):
        """Get an entity by its ID."""
        result = await session.execute(select(model_class).where(model_class.id == entity_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_entities_by_filter(session: AsyncSession, model_class, **filters):
        """Get entities by filter criteria."""
        query = select(model_class)
        for key, value in filters.items():
            if hasattr(model_class, key):
                query = query.where(getattr(model_class, key) == value)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_entity(session: AsyncSession, model_class, entity_id: str, data: Dict[str, Any]):
        """Update an entity."""
        query = update(model_class).where(model_class.id == entity_id).values(**data)
        result = await session.execute(query)
        return result.rowcount > 0
    
    @staticmethod
    async def delete_entity(session: AsyncSession, model_class, entity_id: str):
        """Delete an entity."""
        query = delete(model_class).where(model_class.id == entity_id)
        result = await session.execute(query)
        return result.rowcount > 0
    
    @staticmethod
    async def count_entities(session: AsyncSession, model_class, **filters):
        """Count entities by filter criteria."""
        query = select(func.count(model_class.id))
        for key, value in filters.items():
            if hasattr(model_class, key):
                query = query.where(getattr(model_class, key) == value)
        result = await session.execute(query)
        return result.scalar() or 0
    
    @staticmethod
    async def entity_exists(session: AsyncSession, model_class, **filters):
        """Check if an entity exists."""
        query = select(func.count(model_class.id))
        for key, value in filters.items():
            if hasattr(model_class, key):
                query = query.where(getattr(model_class, key) == value)
        result = await session.execute(query)
        return (result.scalar() or 0) > 0


class DatabaseOperationMixin(BaseCRUDMixin):
    """
    Enhanced database operation mixin with additional utility methods.
    """
    
    @staticmethod
    async def get_or_create_entity(session: AsyncSession, model_class, defaults: Dict[str, Any] = None, **filters):
        """Get an entity or create it if it doesn't exist."""
        entity = await DatabaseOperationMixin.get_entities_by_filter(session, model_class, **filters)
        if entity:
            return entity[0], False
        
        create_data = {**filters, **(defaults or {})}
        entity = await DatabaseOperationMixin.create_entity(session, model_class, create_data)
        return entity, True
    
    @staticmethod
    async def bulk_create_entities(session: AsyncSession, model_class, data_list: list):
        """Create multiple entities in bulk."""
        entities = [model_class(**data) for data in data_list]
        session.add_all(entities)
        return entities
    
    @staticmethod
    async def bulk_update_entities(session: AsyncSession, model_class, updates: list):
        """Update multiple entities in bulk."""
        for update_data in updates:
            entity_id = update_data.pop('id')
            query = update(model_class).where(model_class.id == entity_id).values(**update_data)
            await session.execute(query)
    
    @staticmethod
    async def bulk_delete_entities(session: AsyncSession, model_class, entity_ids: list):
        """Delete multiple entities in bulk."""
        query = delete(model_class).where(model_class.id.in_(entity_ids))
        result = await session.execute(query)
        return result.rowcount


class PaginatedDatabaseOperationMixin(DatabaseOperationMixin):
    """
    Database operation mixin with pagination support.
    """
    
    @staticmethod
    async def get_paginated_entities(session: AsyncSession, model_class, page: int = 1, page_size: int = 10, **filters):
        """Get paginated entities."""
        offset = (page - 1) * page_size
        query = select(model_class)
        
        for key, value in filters.items():
            if hasattr(model_class, key):
                query = query.where(getattr(model_class, key) == value)
        
        query = query.offset(offset).limit(page_size)
        result = await session.execute(query)
        entities = result.scalars().all()
        
        total_count = await PaginatedDatabaseOperationMixin.count_entities(session, model_class, **filters)
        
        return {
            'entities': entities,
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size
        }


class TransactionalDatabaseOperationMixin(PaginatedDatabaseOperationMixin):
    """
    Database operation mixin with transaction support.
    """
    
    @staticmethod
    @asynccontextmanager
    async def transaction(session: AsyncSession):
        """Context manager for database transactions."""
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
    
    @staticmethod
    async def execute_in_transaction(session: AsyncSession, operations: list):
        """Execute multiple operations in a single transaction."""
        async with TransactionalDatabaseOperationMixin.transaction(session):
            results = []
            for operation in operations:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(session)
                else:
                    result = operation(session)
                results.append(result)
            return results


# Main database operation class combining all mixins
class DatabaseOperations(TransactionalDatabaseOperationMixin):
    """
    Comprehensive database operations class.
    Provides all CRUD operations with transaction support, pagination, and bulk operations.
    """
    pass


# Backward compatibility aliases
db_ops = DatabaseOperations
BaseDatabaseOperations = DatabaseOperations

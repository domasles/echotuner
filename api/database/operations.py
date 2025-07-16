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
        """Get entity by ID."""
        result = await session.execute(
            select(model_class).where(getattr(model_class, 'id') == entity_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_entity_by_field(session: AsyncSession, model_class, field_name: str, value: Any):
        """Get entity by specific field."""
        result = await session.execute(
            select(model_class).where(getattr(model_class, field_name) == value)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_entities_by_field(session: AsyncSession, model_class, field_name: str, value: Any, limit: Optional[int] = None):
        """Get multiple entities by specific field."""
        query = select(model_class).where(getattr(model_class, field_name) == value)
        if limit:
            query = query.limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_entity_by_id(session: AsyncSession, model_class, entity_id: str, updates: Dict[str, Any]):
        """Update entity by ID."""
        await session.execute(
            update(model_class)
            .where(getattr(model_class, 'id') == entity_id)
            .values(**updates)
        )
    
    @staticmethod
    async def delete_entity_by_id(session: AsyncSession, model_class, entity_id: str):
        """Delete entity by ID."""
        result = await session.execute(
            delete(model_class).where(getattr(model_class, 'id') == entity_id)
        )
        return result.rowcount > 0
    
    @staticmethod
    async def delete_entities_by_field(session: AsyncSession, model_class, field_name: str, value: Any):
        """Delete entities by specific field."""
        result = await session.execute(
            delete(model_class).where(getattr(model_class, field_name) == value)
        )
        return result.rowcount
    
    @staticmethod
    async def count_entities(session: AsyncSession, model_class, field_name: Optional[str] = None, value: Any = None):
        """Count entities, optionally filtered by field."""
        if field_name and value is not None:
            query = select(func.count()).select_from(model_class).where(getattr(model_class, field_name) == value)
        else:
            query = select(func.count()).select_from(model_class)
        
        result = await session.execute(query)
        return result.scalar() or 0

class AuthOperationsMixin(BaseCRUDMixin):
    """Authentication-specific database operations."""
    
    @db_operation("store auth state", return_on_error=False)
    async def store_auth_state_op(self, session: AsyncSession, state_data: Dict[str, Any]) -> bool:
        """Store auth state operation."""
        from database.models import AuthState
        await AuthOperationsMixin.create_entity(session, AuthState, state_data)
        return True
    
    @db_read_operation("validate auth state")
    async def validate_auth_state_op(self, session: AsyncSession, state: str) -> Optional[Dict[str, Any]]:
        """Validate auth state operation."""
        from database.models import AuthState
        auth_state = await AuthOperationsMixin.get_entity_by_field(session, AuthState, 'state', state)
        
        if not auth_state:
            return None
            
        return {
            'device_id': auth_state.device_id,
            'platform': auth_state.platform
        }
    
    @db_operation("create session", return_on_error=False)
    async def create_session_op(self, session: AsyncSession, session_data: Dict[str, Any]) -> bool:
        """Create session operation."""
        from database.models import AuthSession
        await AuthOperationsMixin.create_entity(session, AuthSession, session_data)
        return True
    
    @db_read_operation("validate session")
    async def validate_session_op(self, session: AsyncSession, session_id: str, device_id: str) -> bool:
        """Validate session operation."""
        from database.models import AuthSession
        from sqlalchemy import and_
        
        result = await session.execute(
            select(AuthSession).where(
                and_(
                    AuthSession.session_id == session_id,
                    AuthSession.device_id == device_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

class PlaylistOperationsMixin(BaseCRUDMixin):
    """Playlist-specific database operations."""
    
    @db_operation("save playlist draft", return_on_error=False)
    async def save_playlist_draft_op(self, session: AsyncSession, draft_data: Dict[str, Any]) -> bool:
        """Save playlist draft operation."""
        from database.models import PlaylistDraft
        await PlaylistOperationsMixin.create_entity(session, PlaylistDraft, draft_data)
        return True
    
    @db_read_operation("get playlist draft")
    async def get_playlist_draft_op(self, session: AsyncSession, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist draft operation."""
        from database.models import PlaylistDraft
        draft = await PlaylistOperationsMixin.get_entity_by_id(session, PlaylistDraft, draft_id)
        
        if not draft:
            return None
            
        return {
            'id': draft.id,
            'device_id': draft.device_id,
            'session_id': draft.session_id,
            'prompt': draft.prompt,
            'songs_json': draft.songs_json,
            'is_draft': draft.is_draft,
            'created_at': draft.created_at,
            'updated_at': draft.updated_at,
            'songs': draft.songs,
            'status': draft.status,
            'spotify_playlist_id': draft.spotify_playlist_id,
            'spotify_playlist_url': draft.spotify_playlist_url
        }
    
    @db_operation("delete playlist draft", return_on_error=False)
    async def delete_playlist_draft_op(self, session: AsyncSession, draft_id: str) -> bool:
        """Delete playlist draft operation."""
        from database.models import PlaylistDraft
        return await PlaylistOperationsMixin.delete_entity_by_id(session, PlaylistDraft, draft_id)

class RateLimitOperationsMixin(BaseCRUDMixin):
    """Rate limiting-specific database operations."""
    
    @db_read_operation("get rate limit status")
    async def get_rate_limit_status_op(self, session: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status operation."""
        from database.models import RateLimit
        from sqlalchemy import desc
        
        result = await session.execute(
            select(RateLimit)
            .where(RateLimit.user_id == user_id)
            .order_by(desc(RateLimit.last_request_date))
            .limit(1)
        )
        rate_limit = result.scalar_one_or_none()
        
        if rate_limit:
            return {
                'requests_count': rate_limit.requests_count,
                'last_request_date': rate_limit.last_request_date
            }
        
        return None
    
    @db_operation("update rate limit", return_on_error=False)
    async def update_rate_limit_op(self, session: AsyncSession, rate_limit_data: Dict[str, Any]) -> bool:
        """Update rate limit operation."""
        from database.models import RateLimit
        await RateLimitOperationsMixin.create_entity(session, RateLimit, rate_limit_data)
        return True

class EmbeddingOperationsMixin(BaseCRUDMixin):
    """Embedding cache-specific database operations."""
    
    @db_read_operation("get cached embedding")
    async def get_cached_embedding_op(self, session: AsyncSession, cache_key: str) -> Any:
        """Get cached embedding operation."""
        from database.models import EmbeddingCache
        cached_entry = await EmbeddingOperationsMixin.get_entity_by_field(session, EmbeddingCache, 'cache_key', cache_key)
        
        if cached_entry:
            return cached_entry.response_data
        
        return None
    
    @db_operation("store embedding", return_on_error=False)
    async def store_embedding_op(self, session: AsyncSession, cache_data: Dict[str, Any]) -> bool:
        """Store embedding operation."""
        from database.models import EmbeddingCache
        await EmbeddingOperationsMixin.create_entity(session, EmbeddingCache, cache_data)
        return True
    
    @db_operation("update access count", return_on_error=False)
    async def update_access_count_op(self, session: AsyncSession, cache_key: str, last_accessed: str) -> bool:
        """Update access count operation."""
        from database.models import EmbeddingCache
        await EmbeddingOperationsMixin.update_entity_by_id(
            session, 
            EmbeddingCache, 
            cache_key, 
            {
                'access_count': EmbeddingCache.access_count + 1,
                'last_accessed': last_accessed
            }
        )
        return True

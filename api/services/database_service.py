"""
Database service.
Modern database operations using SQLAlchemy ORM with standardized patterns and error handling.
"""

import hashlib
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, desc, func, delete, update

from core.singleton import SingletonServiceBase
from models import UserContext
from config.app_constants import AppConstants

from database.core import db_core, get_session
from database.models import (
    AuthSession, DeviceRegistry, AuthState, AuthAttempt,
    PlaylistDraft, SpotifyPlaylist, DemoPlaylist,
    UserPersonality, RateLimit, IPAttempt, EmbeddingCache
)
from database.operations import (
    AuthOperationsMixin, PlaylistOperationsMixin, RateLimitOperationsMixin,
    EmbeddingOperationsMixin, db_operation, db_read_operation
)
from utils.input_validator import UniversalValidator
from utils.exceptions import (
    ErrorHandler, handle_service_errors, raise_db_error, raise_auth_error,
    raise_playlist_error, raise_rate_limit_error, ErrorCode
)

logger = logging.getLogger(__name__)

class DatabaseService(SingletonServiceBase):
    """Modern database service using SQLAlchemy ORM with backwards compatibility."""

    def __init__(self):
        super().__init__()

    def _setup_service(self):
        """Initialize database service."""

        self.db_path = AppConstants.DATABASE_FILEPATH  # Keep for compatibility
        self._log_initialization("Database service initialized with SQLAlchemy ORM", logger)

    async def initialize(self):
        """Initialize the ORM and create all tables."""

        try:
            await db_core.initialize()
            logger.info("Database service initialization completed with ORM")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise RuntimeError(UniversalValidator.sanitize_error_message(str(e)))

    @handle_service_errors("store_auth_state")
    async def store_auth_state(self, state: str, device_id: str, platform: str, expires_at: int) -> bool:
        """Store auth state for validation using standardized operations."""
        try:
            async with get_session() as session:
                auth_state = AuthState(
                    state=state,
                    device_id=device_id,
                    platform=platform,
                    created_at=int(datetime.now().timestamp()),
                    expires_at=expires_at
                )
                session.add(auth_state)
                await session.commit()
                return True
        except Exception as e:
            raise_auth_error(f"Failed to store auth state: {e}", ErrorCode.AUTH_STATE_INVALID)

    @handle_service_errors("validate_auth_state")
    async def validate_auth_state(self, state: str) -> Optional[Dict[str, str]]:
        """Validate auth state and return device info using standardized operations."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthState).where(AuthState.state == state)
                )
                auth_state = result.scalar_one_or_none()
                
                if not auth_state:
                    logger.warning(f"Invalid auth state provided: {state}")
                    return None

                return {
                    'device_id': auth_state.device_id,
                    'platform': auth_state.platform
                }
        except Exception as e:
            raise_auth_error(f"Failed to validate auth state: {e}", ErrorCode.AUTH_STATE_INVALID)

    @handle_service_errors("create_session")
    async def create_session(self, session_data: Dict[str, Any]) -> bool:
        """Create a new auth session using standardized operations."""
        try:
            async with get_session() as session:
                auth_session = AuthSession(**session_data)
                session.add(auth_session)
                await session.commit()
                return True
        except Exception as e:
            raise_auth_error(f"Failed to create session: {e}", ErrorCode.AUTH_SESSION_EXPIRED)

    @handle_service_errors("validate_session")
    async def validate_session(self, session_id: str, device_id: str) -> bool:
        """Validate if session exists and belongs to device using standardized operations."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession).where(
                        and_(
                            AuthSession.session_id == session_id,
                            AuthSession.device_id == device_id
                        )
                    )
                )
                return result.scalar_one_or_none() is not None
        except Exception as e:
            raise_auth_error(f"Failed to validate session: {e}", ErrorCode.AUTH_SESSION_EXPIRED)
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession).where(
                        and_(
                            AuthSession.session_id == session_id,
                            AuthSession.device_id == device_id
                        )
                    )
                )
                return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False

    async def get_session_by_device(self, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device."""

        try:
            current_time = int(datetime.now().timestamp())
            
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession.session_id)
                    .where(
                        and_(
                            AuthSession.device_id == device_id,
                            AuthSession.expires_at > current_time
                        )
                    )
                    .order_by(desc(AuthSession.created_at))
                    .limit(1)
                )
                session_row = result.scalar_one_or_none()
                return session_row if session_row else None

        except Exception as e:
            logger.error(f"Failed to get session by device: {e}")
            return None

    async def get_sessions_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a device."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession).where(AuthSession.device_id == device_id)
                )
                sessions = result.scalars().all()
                
                return [
                    {
                        'session_id': s.session_id,
                        'device_id': s.device_id,
                        'platform': s.platform,
                        'spotify_user_id': s.spotify_user_id,
                        'access_token': s.access_token,
                        'refresh_token': s.refresh_token,
                        'expires_at': s.expires_at,
                        'created_at': s.created_at,
                        'last_used_at': s.last_used_at,
                        'account_type': s.account_type or 'normal'
                    }
                    for s in sessions
                ]

        except Exception as e:
            logger.error(f"Get sessions by device error: {e}")
            return []

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(AuthSession).where(AuthSession.session_id == session_id)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False

    async def register_device(self, device_data: Dict[str, Any]) -> bool:
        """Register a new device."""

        try:
            async with get_session() as session:
                device = DeviceRegistry(**device_data)
                session.add(device)  # Use add for insert
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False

    async def validate_device(self, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate that device_id was issued by server and is active."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(DeviceRegistry.is_active).where(DeviceRegistry.device_id == device_id)
                )
                device = result.scalar_one_or_none()

                if not device:
                    return False

                if update_last_seen:
                    await session.execute(
                        update(DeviceRegistry)
                        .where(DeviceRegistry.device_id == device_id)
                        .values(last_seen_timestamp=int(datetime.now().timestamp()))
                    )
                    await session.commit()

                return True

        except Exception as e:
            logger.error(f"Device validation failed: {e}")
            return False

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information including user and device data."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession).where(AuthSession.session_id == session_id)
                )
                auth_session = result.scalar_one_or_none()
                
                if not auth_session:
                    return None

                return {
                    'device_id': auth_session.device_id,
                    'expires_at': auth_session.expires_at,
                    'spotify_user_id': auth_session.spotify_user_id,
                    'access_token': auth_session.access_token,
                    'refresh_token': auth_session.refresh_token,
                    'account_type': auth_session.account_type or 'normal'
                }

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None

    async def update_session_token(self, session_id: str, access_token: str, expires_at: int) -> bool:
        """Update session with new access token."""

        try:
            async with get_session() as session:
                await session.execute(
                    update(AuthSession)
                    .where(AuthSession.session_id == session_id)
                    .values(access_token=access_token, expires_at=expires_at)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to update session token: {e}")
            return False

    async def update_session_last_used(self, session_id: str) -> bool:
        """Update session last used timestamp."""

        try:
            async with get_session() as session:
                await session.execute(
                    update(AuthSession)
                    .where(AuthSession.session_id == session_id)
                    .values(last_used_at=int(datetime.now().timestamp()))
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to update session last used: {e}")
            return False

    async def update_session_expiration(self, session_id: str, expires_at: int) -> bool:
        """Update session expiration time."""

        try:
            async with get_session() as session:
                await session.execute(
                    update(AuthSession)
                    .where(AuthSession.session_id == session_id)
                    .values(expires_at=expires_at)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to update session expiration: {e}")
            return False

    async def revoke_user_sessions(self, spotify_user_id: str) -> bool:
        """Revoke all sessions for a specific user."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(AuthSession).where(AuthSession.spotify_user_id == spotify_user_id)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to revoke user sessions: {e}")
            return False

    async def get_user_active_sessions_count(self, spotify_user_id: str) -> int:
        """Get count of active sessions for a user."""

        try:
            current_time = int(datetime.now().timestamp())
            
            async with get_session() as session:
                result = await session.execute(
                    select(func.count(AuthSession.session_id))
                    .where(
                        and_(
                            AuthSession.spotify_user_id == spotify_user_id,
                            AuthSession.expires_at > current_time
                        )
                    )
                )
                return result.scalar() or 0

        except Exception as e:
            logger.error(f"Failed to get active sessions count: {e}")
            return 0

    @handle_service_errors("get_rate_limit_status")
    async def get_rate_limit_status(self, user_id: str, current_date: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status for a user using standardized operations."""
        try:
            async with get_session() as session:
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
                        'refinements_count': rate_limit.refinements_count,
                        'last_request_date': rate_limit.last_request_date
                    }

                return None
        except Exception as e:
            raise_rate_limit_error(f"Failed to get rate limit status: {e}", ErrorCode.RATE_LIMIT_CHECK_FAILED)

    @handle_service_errors("update_rate_limit_requests")
    async def update_rate_limit_requests(self, user_id: str, current_date: str, requests_count: int) -> bool:
        """Update rate limit requests count using standardized operations."""
        try:
            async with get_session() as session:
                # Get existing refinements count to preserve it
                existing = await self.get_rate_limit_status(user_id, current_date)
                refinements_count = existing['refinements_count'] if existing else 0
                
                rate_limit = RateLimit(
                    user_id=user_id,
                    requests_count=requests_count,
                    refinements_count=refinements_count,
                    last_request_date=current_date,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                session.add(rate_limit)
                await session.commit()
                return True
        except Exception as e:
            raise_rate_limit_error(f"Failed to update rate limit requests: {e}", ErrorCode.RATE_LIMIT_CHECK_FAILED)

    @handle_service_errors("update_rate_limit_refinements")
    async def update_rate_limit_refinements(self, user_id: str, current_date: str, refinements_count: int) -> bool:
        """Update rate limit refinements count using standardized operations."""
        try:
            async with get_session() as session:
                # Get existing requests count to preserve it
                existing = await self.get_rate_limit_status(user_id, current_date)
                requests_count = existing['requests_count'] if existing else 0
                
                rate_limit = RateLimit(
                    user_id=user_id,
                    requests_count=requests_count,
                    refinements_count=refinements_count,
                    last_request_date=current_date,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                session.add(rate_limit)
                await session.commit()
                return True
        except Exception as e:
            raise_rate_limit_error(f"Failed to update rate limit refinements: {e}", ErrorCode.RATE_LIMIT_CHECK_FAILED)

    # ===========================================
    # PLAYLIST OPERATIONS (ORM-based with standardized patterns)
    # ===========================================

    @handle_service_errors("save_playlist_draft")
    async def save_playlist_draft(self, draft_data: Dict[str, Any]) -> bool:
        """Save or update playlist draft using standardized operations."""
        try:
            async with get_session() as session:
                draft = PlaylistDraft(**draft_data)
                session.add(draft)
                await session.commit()
                return True
        except Exception as e:
            raise_playlist_error(f"Failed to save playlist draft: {e}", ErrorCode.PLAYLIST_CREATION_FAILED)

    @handle_service_errors("get_playlist_draft")
    async def get_playlist_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get playlist draft by ID using standardized operations."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(PlaylistDraft).where(PlaylistDraft.id == draft_id)
                )
                draft = result.scalar_one_or_none()
                
                if draft:
                    return {
                        'id': draft.id,
                        'device_id': draft.device_id,
                        'session_id': draft.session_id,
                        'prompt': draft.prompt,
                        'songs_json': draft.songs_json,
                        'refinements_used': draft.refinements_used,
                        'is_draft': draft.is_draft,
                        'created_at': draft.created_at,
                        'updated_at': draft.updated_at,
                        'songs': draft.songs,
                        'status': draft.status,
                        'spotify_playlist_id': draft.spotify_playlist_id,
                        'spotify_playlist_url': draft.spotify_playlist_url
                    }

                return None
        except Exception as e:
            raise_playlist_error(f"Failed to get playlist draft: {e}", ErrorCode.PLAYLIST_NOT_FOUND)

    async def get_user_drafts(self, device_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's playlist drafts."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(PlaylistDraft)
                    .where(PlaylistDraft.device_id == device_id)
                    .order_by(desc(PlaylistDraft.updated_at))
                    .limit(limit)
                )
                drafts = result.scalars().all()
                
                return [
                    {
                        'id': draft.id,
                        'device_id': draft.device_id,
                        'session_id': draft.session_id,
                        'prompt': draft.prompt,
                        'songs_json': draft.songs_json,
                        'refinements_used': draft.refinements_used,
                        'is_draft': draft.is_draft,
                        'created_at': draft.created_at,
                        'updated_at': draft.updated_at
                    }
                    for draft in drafts
                ]

        except Exception as e:
            logger.error(f"Failed to get user drafts: {e}")
            return []

    async def delete_playlist_draft(self, draft_id: str) -> bool:
        """Delete playlist draft."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(PlaylistDraft).where(PlaylistDraft.id == draft_id)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to delete playlist draft: {e}")
            return False

    async def update_draft_refinements(self, draft_id: str, refinements_used: int) -> bool:
        """Update refinements used count for a draft."""

        try:
            async with get_session() as session:
                await session.execute(
                    update(PlaylistDraft)
                    .where(PlaylistDraft.id == draft_id)
                    .values(refinements_used=refinements_used)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to update draft refinements: {e}")
            return False

    # ===========================================
    # USER PERSONALITY OPERATIONS (ORM-based)
    # ===========================================

    async def save_user_personality(self, user_id: str, spotify_user_id: str, user_context: UserContext) -> bool:
        """Save or update user personality data."""

        try:
            async with get_session() as session:
                personality = UserPersonality(
                    user_id=user_id,
                    spotify_user_id=spotify_user_id,
                    user_context=json.dumps(user_context.to_dict()),
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                session.add(personality)
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to save user personality: {e}")
            return False

    async def get_user_personality(self, user_id: str) -> Optional[str]:
        """Get user personality context as JSON string."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(UserPersonality.user_context)
                    .where(UserPersonality.user_id == user_id)
                )
                context = result.scalar_one_or_none()
                return context

        except Exception as e:
            logger.error(f"Failed to get user personality: {e}")
            return None

    # ===========================================
    # DEMO PLAYLIST OPERATIONS (ORM-based)
    # ===========================================

    async def add_demo_playlist(self, playlist_id: str, device_id: str, session_id: str, prompt: str):
        """Add a demo playlist ID to track refinement counts."""

        try:
            async with get_session() as session:
                demo_playlist = DemoPlaylist(
                    playlist_id=playlist_id,
                    device_id=device_id,
                    session_id=session_id,
                    prompt=prompt,
                    refinements_used=0,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                session.add(demo_playlist)
                await session.commit()
                logger.debug(f"Added demo playlist {playlist_id} for device {device_id}")

        except Exception as e:
            logger.error(f"Failed to add demo playlist {playlist_id}: {e}")
            raise

    async def increment_demo_playlist_refinements(self, playlist_id: str):
        """Increment the refinement count for a demo playlist."""

        try:
            async with get_session() as session:
                await session.execute(
                    update(DemoPlaylist)
                    .where(DemoPlaylist.playlist_id == playlist_id)
                    .values(
                        refinements_used=DemoPlaylist.refinements_used + 1,
                        updated_at=datetime.now().isoformat()
                    )
                )
                await session.commit()
                logger.debug(f"Incremented refinement count for demo playlist {playlist_id}")

        except Exception as e:
            logger.error(f"Failed to increment refinements for demo playlist {playlist_id}: {e}")
            raise

    async def get_demo_playlist_refinements(self, playlist_id: str) -> int:
        """Get the refinement count for a demo playlist."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(DemoPlaylist.refinements_used)
                    .where(DemoPlaylist.playlist_id == playlist_id)
                )
                count = result.scalar_one_or_none()
                return count or 0

        except Exception as e:
            logger.error(f"Failed to get demo playlist refinements for {playlist_id}: {e}")
            return 0

    async def get_demo_playlists_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all demo playlist IDs for a device."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(DemoPlaylist)
                    .where(DemoPlaylist.device_id == device_id)
                    .order_by(desc(DemoPlaylist.created_at))
                )
                playlists = result.scalars().all()
                
                return [
                    {
                        'playlist_id': playlist.playlist_id,
                        'prompt': playlist.prompt,
                        'refinements_used': playlist.refinements_used,
                        'created_at': playlist.created_at,
                        'updated_at': playlist.updated_at
                    }
                    for playlist in playlists
                ]

        except Exception as e:
            logger.error(f"Failed to get demo playlists for device {device_id}: {e}")
            return []

    # ===========================================
    # IP RATE LIMITING OPERATIONS (ORM-based)
    # ===========================================

    async def record_ip_attempt(self, attempt_data: dict) -> bool:
        """Record a failed IP attempt."""

        try:
            async with get_session() as session:
                ip_attempt = IPAttempt(**attempt_data)
                session.add(ip_attempt)
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to record IP attempt: {e}")
            return False

    async def get_ip_attempts_count(self, ip_hash: str, since_timestamp: float) -> int:
        """Get count of attempts for an IP since a given timestamp."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(func.count(IPAttempt.id))
                    .where(
                        and_(
                            IPAttempt.ip_hash == ip_hash,
                            IPAttempt.attempted_at > since_timestamp
                        )
                    )
                )
                return result.scalar() or 0

        except Exception as e:
            logger.error(f"Failed to get IP attempts count: {e}")
            return 0

    async def clear_ip_attempts(self, ip_hash: str) -> bool:
        """Clear all attempts for an IP address."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(IPAttempt).where(IPAttempt.ip_hash == ip_hash)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to clear IP attempts: {e}")
            return False

    # ===========================================
    # CLEANUP OPERATIONS (ORM-based)
    # ===========================================

    async def cleanup_expired_auth_attempts(self) -> bool:
        """Clean up expired authentication attempts."""

        try:
            current_time = int(datetime.now().timestamp())
            
            async with get_session() as session:
                await session.execute(
                    delete(AuthAttempt).where(AuthAttempt.expires_at < current_time)
                )
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup expired auth attempts: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and states."""

        try:
            current_time = int(datetime.now().timestamp())
            
            async with get_session() as session:
                # Clean expired sessions
                sessions_result = await session.execute(
                    delete(AuthSession).where(AuthSession.expires_at < current_time)
                )
                sessions_deleted = sessions_result.rowcount
                
                # Clean expired states
                states_result = await session.execute(
                    delete(AuthState).where(AuthState.expires_at < current_time)
                )
                states_deleted = states_result.rowcount
                
                await session.commit()
                return sessions_deleted + states_deleted

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def cleanup_expired_ip_attempts(self, before_timestamp: float) -> int:
        """Clean up expired IP attempts."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    delete(IPAttempt).where(IPAttempt.attempted_at < before_timestamp)
                )
                await session.commit()
                return result.rowcount

        except Exception as e:
            logger.error(f"Failed to cleanup expired IP attempts: {e}")
            return 0

    async def cleanup_device_rate_limits(self, device_id: str):
        """Clean up all rate limit data for a specific device."""

        try:
            device_hash = hashlib.sha256(device_id.encode()).hexdigest()

            async with get_session() as session:
                await session.execute(
                    delete(RateLimit).where(RateLimit.user_id == device_hash)
                )
                await session.commit()
                logger.debug(f"Cleaned up rate limits for device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to cleanup device rate limits: {e}")

    async def cleanup_user_rate_limits(self, user_id: str):
        """Clean up all rate limit data for a specific user ID (for demo accounts)."""

        try:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()

            async with get_session() as session:
                await session.execute(
                    delete(RateLimit).where(RateLimit.user_id == user_hash)
                )
                await session.commit()
                logger.debug(f"Cleaned up rate limits for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup user rate limits: {e}")

    async def cleanup_demo_sessions(self):
        """Clean up all demo account sessions."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(AuthSession).where(AuthSession.account_type == 'demo')
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup demo sessions: {e}")
            raise

    async def cleanup_normal_sessions(self):
        """Clean up all normal account sessions."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(AuthSession).where(
                        or_(
                            AuthSession.account_type == 'normal',
                            AuthSession.account_type.is_(None)
                        )
                    )
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup normal sessions: {e}")
            raise

    async def get_all_sessions_for_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific device."""

        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession.session_id, AuthSession.spotify_user_id, 
                           AuthSession.account_type, AuthSession.expires_at)
                    .where(AuthSession.device_id == device_id)
                )
                sessions = result.all()
                
                return [
                    {
                        "session_id": row.session_id,
                        "spotify_user_id": row.spotify_user_id, 
                        "account_type": row.account_type or 'normal',
                        "expires_at": row.expires_at
                    }
                    for row in sessions
                ]

        except Exception as e:
            logger.error(f"Failed to get sessions for device: {e}")
            return []

    async def cleanup_device_auth_states(self, device_id: str):
        """Clean up all auth states for a specific device."""

        try:
            async with get_session() as session:
                await session.execute(
                    delete(AuthState).where(AuthState.device_id == device_id)
                )
                await session.commit()
                logger.debug(f"Cleaned up auth states for device {device_id[:8]}...")

        except Exception as e:
            logger.error(f"Failed to cleanup device auth states: {e}")

# Create singleton instance
db_service = DatabaseService()

"""
Database servicfrom infrastructure.database.models import (
    AuthSession, DeviceRegistry, AuthState, AuthAttempt, DemoOwnerToken,
    PlaylistDraft, SpotifyPlaylist, DemoPlaylist,
    UserPersonality, RateLimit, IPAttempt, EmbeddingCache
)odern database operations using SQLAlchemy ORM with standardized patterns and error handling.
"""

import hashlib
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, desc, func, delete, update

from application.core.singleton import SingletonServiceBase
from application import UserContext
from infrastructure.config.app_constants import AppConstants

from infrastructure.database.service import db_core, get_session
from infrastructure.database.models import (
    AuthSession, DeviceRegistry, AuthState, AuthAttempt,
    PlaylistDraft, SpotifyPlaylist, DemoPlaylist,
    UserPersonality, RateLimit, IPAttempt, EmbeddingCache, DemoOwnerToken
)
from application.core.database.decorators import (
    db_write_operation, db_read_operation, db_count_operation, 
    db_list_operation, db_bool_operation
)
from domain.shared.validation.validators import UniversalValidator
from domain.shared.exceptions import (
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

    @db_read_operation()
    async def get_session_by_device(self, session, device_id: str) -> Optional[str]:
        """Get the most recent valid session for a device."""
        current_time = int(datetime.now().timestamp())
        
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

    @handle_service_errors("get_sessions_by_device")
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

    @db_bool_operation()
    async def invalidate_session(self, session, session_id: str) -> bool:
        """Invalidate a session."""
        await session.execute(
            delete(AuthSession).where(AuthSession.session_id == session_id)
        )
        return True

    @db_bool_operation()
    async def register_device(self, session, device_data: Dict[str, Any]) -> bool:
        """Register a new device."""
        device = DeviceRegistry(**device_data)
        session.add(device)
        return True

    @db_bool_operation()
    async def validate_device(self, session, device_id: str, update_last_seen: bool = True) -> bool:
        """Validate that device_id was issued by server and is active."""
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

        return True

    @db_read_operation()
    async def get_session_info(self, session, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information including user and device data."""
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

    @handle_service_errors("update_session")
    async def update_session(self, session_id: str, 
                           access_token: str = None, 
                           expires_at: int = None,
                           update_last_used: bool = False) -> bool:
        """Update session with new access token, expiration, and/or last used timestamp."""
        try:
            update_values = {}
            
            if access_token is not None:
                update_values['access_token'] = access_token
            if expires_at is not None:
                update_values['expires_at'] = expires_at
            if update_last_used:
                update_values['last_used_at'] = int(datetime.now().timestamp())
                
            if not update_values:
                return True  # Nothing to update
                
            async with get_session() as session:
                await session.execute(
                    update(AuthSession)
                    .where(AuthSession.session_id == session_id)
                    .values(**update_values)
                )
                await session.commit()
                return True
        except Exception as e:
            raise_auth_error(f"Failed to update session: {e}", ErrorCode.AUTH_SESSION_EXPIRED)

    @db_bool_operation()
    async def revoke_user_sessions(self, session, spotify_user_id: str) -> bool:
        """Revoke all sessions for a specific user."""
        await session.execute(
            delete(AuthSession).where(AuthSession.spotify_user_id == spotify_user_id)
        )
        return True

    @db_count_operation()
    async def get_user_active_sessions_count(self, session, spotify_user_id: str) -> int:
        """Get count of active sessions for a user."""
        current_time = int(datetime.now().timestamp())
        
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
                        'last_request_date': rate_limit.last_request_date
                    }

                return None
        except Exception as e:
            raise_rate_limit_error(f"Failed to get rate limit status: {e}", ErrorCode.RATE_LIMIT_CHECK_FAILED)

    @handle_service_errors("update_rate_limit_requests")
    async def update_rate_limit_requests(self, user_id: str, current_date: str, requests_count: int) -> bool:
        """Update rate limit requests count using upsert operation."""
        try:
            async with get_session() as session:
                # Try to get existing record
                result = await session.execute(
                    select(RateLimit).where(
                        and_(
                            RateLimit.user_id == user_id,
                            RateLimit.last_request_date == current_date
                        )
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    await session.execute(
                        update(RateLimit)
                        .where(
                            and_(
                                RateLimit.user_id == user_id,
                                RateLimit.last_request_date == current_date
                            )
                        )
                        .values(
                            requests_count=requests_count,
                            updated_at=datetime.now().isoformat()
                        )
                    )
                else:
                    # Create new record
                    rate_limit = RateLimit(
                        user_id=user_id,
                        requests_count=requests_count,
                        last_request_date=current_date,
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    session.add(rate_limit)
                
                await session.commit()
                return True
        except Exception as e:
            raise_rate_limit_error(f"Failed to update rate limit requests: {e}", ErrorCode.RATE_LIMIT_CHECK_FAILED)

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

    @db_list_operation()
    async def get_user_drafts(self, session, device_id: str, limit: int = 10, user_id: str = None) -> List[Dict[str, Any]]:
        """Get user's playlist drafts. If user_id is provided, get drafts for all devices of that user."""
        if user_id:
            # Get drafts for all devices of this user by joining with auth_sessions
            result = await session.execute(
                select(PlaylistDraft)
                .join(AuthSession, PlaylistDraft.session_id == AuthSession.session_id)
                .where(and_(
                    AuthSession.spotify_user_id == user_id,
                    PlaylistDraft.is_draft == True
                ))
                .order_by(desc(PlaylistDraft.updated_at))
                .limit(limit)
            )
        else:
            # Get drafts for specific device only (demo mode)
            result = await session.execute(
                select(PlaylistDraft)
                .where(and_(
                    PlaylistDraft.device_id == device_id,
                    PlaylistDraft.is_draft == True
                ))
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
                'is_draft': draft.is_draft,
                'created_at': draft.created_at,
                'updated_at': draft.updated_at
            }
            for draft in drafts
        ]

    @db_bool_operation()
    async def delete_playlist_draft(self, session, draft_id: str) -> bool:
        """Delete playlist draft."""
        await session.execute(
            delete(PlaylistDraft).where(PlaylistDraft.id == draft_id)
        )
        return True

    @handle_service_errors("delete_playlist_drafts_by_sessions") 
    async def delete_playlist_drafts_by_sessions(self, session_ids: List[str]) -> int:
        """Delete playlist drafts by multiple session IDs using ORM."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    delete(PlaylistDraft).where(PlaylistDraft.session_id.in_(session_ids))
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Failed to delete playlist drafts for sessions: {e}")
            raise
            
    # ===========================================
    # USER PERSONALITY OPERATIONS (ORM-based)
    # ===========================================

    @db_bool_operation()
    async def save_user_personality(self, session, user_id: str, spotify_user_id: str, user_context: UserContext) -> bool:
        """Save or update user personality data."""
        # Check if personality already exists
        result = await session.execute(
            select(UserPersonality).where(UserPersonality.user_id == user_id)
        )
        existing = result.scalars().first()
        
        if existing:
            # Update existing personality
            existing.spotify_user_id = spotify_user_id
            existing.user_context = json.dumps(user_context.model_dump())
            existing.updated_at = datetime.now().isoformat()
        else:
            # Create new personality
            personality = UserPersonality(
                user_id=user_id,
                spotify_user_id=spotify_user_id,
                user_context=json.dumps(user_context.model_dump()),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            session.add(personality)
        
        return True

    @db_read_operation()
    async def get_user_personality(self, session, user_id: str) -> Optional[str]:
        """Get user personality context as JSON string."""
        result = await session.execute(
            select(UserPersonality.user_context)
            .where(UserPersonality.user_id == user_id)
        )
        context = result.scalar_one_or_none()
        return context

    @handle_service_errors("delete_user_personality")
    async def delete_user_personality(self, user_id: str) -> bool:
        """Delete user personality by user_id using ORM."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    delete(UserPersonality).where(UserPersonality.user_id == user_id)
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete user personality for {user_id}: {e}")
            raise
            
    # ===========================================
    # DEMO PLAYLIST OPERATIONS (ORM-based)
    # ===========================================

    @db_write_operation()
    async def add_demo_playlist(self, session, playlist_id: str, device_id: str, session_id: str, prompt: str):
        """Add a demo playlist ID to track."""
        demo_playlist = DemoPlaylist(
            playlist_id=playlist_id,
            device_id=device_id,
            session_id=session_id,
            prompt=prompt,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        session.add(demo_playlist)
        logger.debug(f"Added demo playlist {playlist_id} for device {device_id}")
        return True

    @db_list_operation()
    async def get_demo_playlists_for_device(self, session, device_id: str) -> List[Dict[str, Any]]:
        """Get all demo playlist IDs for a device."""
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
                'created_at': playlist.created_at,
                'updated_at': playlist.updated_at
            }
            for playlist in playlists
        ]

    # ===========================================
    # IP RATE LIMITING OPERATIONS (ORM-based)
    # ===========================================

    @db_bool_operation()
    async def record_ip_attempt(self, session, attempt_data: dict) -> bool:
        """Record a failed IP attempt."""
        ip_attempt = IPAttempt(**attempt_data)
        session.add(ip_attempt)
        return True

    @db_count_operation()
    async def get_ip_attempts_count(self, session, ip_hash: str, since_timestamp: float) -> int:
        """Get count of attempts for an IP since a given timestamp."""
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

    @db_bool_operation()
    async def clear_ip_attempts(self, session, ip_hash: str) -> bool:
        """Clear all attempts for an IP address."""
        await session.execute(
            delete(IPAttempt).where(IPAttempt.ip_hash == ip_hash)
        )
        return True

    # ===========================================
    # CLEANUP OPERATIONS (ORM-based)
    # ===========================================



    @db_count_operation()
    async def cleanup_expired_sessions(self, session) -> int:
        """Clean up expired sessions and states."""
        current_time = int(datetime.now().timestamp())
        
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
        
        return sessions_deleted + states_deleted

    @db_count_operation()
    async def cleanup_expired_ip_attempts(self, session, before_timestamp: float) -> int:
        """Clean up expired IP attempts."""
        result = await session.execute(
            delete(IPAttempt).where(IPAttempt.attempted_at < before_timestamp)
        )
        return result.rowcount



    @db_list_operation()
    async def get_all_sessions_for_device(self, session, device_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific device."""
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

    @db_write_operation()
    async def cleanup_device_auth_states(self, session, device_id: str):
        """Clean up all auth states for a specific device."""
        await session.execute(
            delete(AuthState).where(AuthState.device_id == device_id)
        )
        logger.debug(f"Cleaned up auth states for device {device_id[:8]}...")
        return True

    @handle_service_errors("get_sessions_by_account_type")
    async def get_sessions_by_account_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific account type."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(AuthSession).where(AuthSession.account_type == account_type)
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
            logger.error(f"Get sessions by account type error: {e}")
            return []

    @handle_service_errors("delete_auth_sessions_by_account_type")
    async def delete_auth_sessions_by_account_type(self, account_type: str) -> int:
        """Delete auth sessions by account type using ORM."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    delete(AuthSession).where(AuthSession.account_type == account_type)
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Failed to delete auth sessions by account type {account_type}: {e}")
            raise
            
    @handle_service_errors("delete_demo_user_personalities")
    async def delete_demo_user_personalities(self) -> int:
        """Delete all demo user personalities using ORM."""
        try:
            async with get_session() as session:
                result = await session.execute(
                    delete(UserPersonality).where(UserPersonality.user_id.like('demo_user_%'))
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Failed to delete demo user personalities: {e}")
            raise

    @db_list_operation()
    async def get_user_echotuner_spotify_playlist_ids(self, session, user_id: str) -> List[str]:
        """Get EchoTuner Spotify playlist IDs for a user."""
        result = await session.execute(
            select(SpotifyPlaylist.spotify_playlist_id)
            .where(SpotifyPlaylist.user_id == user_id)
        )
        playlist_ids = result.scalars().all()
        return list(playlist_ids)

    @db_bool_operation()
    async def mark_as_added_to_spotify(self, session, playlist_id: str, spotify_playlist_id: str, spotify_url: str, user_id: str, device_id: str, session_id: str, playlist_name: str) -> bool:
        """Mark a playlist draft as added to Spotify."""
        # Update the playlist draft with Spotify information
        await session.execute(
            update(PlaylistDraft)
            .where(PlaylistDraft.id == playlist_id)
            .values(
                spotify_playlist_id=spotify_playlist_id,
                spotify_playlist_url=spotify_url,
                is_draft=False,
                status='completed',
                updated_at=datetime.now().isoformat()
            )
        )
        
        # Create a record in the Spotify playlists table
        spotify_playlist = SpotifyPlaylist(
            spotify_playlist_id=spotify_playlist_id,
            user_id=user_id,
            device_id=device_id,
            session_id=session_id,
            original_draft_id=playlist_id,
            playlist_name=playlist_name,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        session.add(spotify_playlist)
        
        return True

    @db_bool_operation()
    async def remove_spotify_playlist_from_drafts(self, spotify_playlist_id: str) -> bool:
        """Remove Spotify playlist ID from all drafts that reference it"""
        
        try:
            async with get_session() as session:
                await session.execute(
                    update(PlaylistDraft)
                    .where(PlaylistDraft.spotify_playlist_id == spotify_playlist_id)
                    .values(spotify_playlist_id=None, spotify_playlist_url=None)
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove Spotify playlist from drafts: {e}")
            return False

    @db_bool_operation()
    async def store_demo_owner_token(self, session, token_info: Dict[str, Any]) -> bool:
        """Store demo owner token information"""
        
        try:
            # First delete any existing demo owner token
            await session.execute(
                delete(DemoOwnerToken)
            )
            
            # Create new token record
            demo_token = DemoOwnerToken(
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                expires_at=token_info['expires_at'],
                spotify_user_id=token_info['spotify_user_id'],
                created_at=int(datetime.now().timestamp())
            )
            
            session.add(demo_token)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store demo owner token: {e}")
            return False

    @db_read_operation()
    async def get_demo_owner_token(self, session) -> Optional[Dict[str, Any]]:
        """Get demo owner token information"""
        
        try:
            result = await session.execute(
                select(DemoOwnerToken).order_by(desc(DemoOwnerToken.created_at)).limit(1)
            )
            
            token_record = result.scalars().first()
            
            if token_record:
                return {
                    'access_token': token_record.access_token,
                    'refresh_token': token_record.refresh_token,
                    'expires_at': token_record.expires_at,
                    'spotify_user_id': token_record.spotify_user_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get demo owner token: {e}")
            return None

    @db_bool_operation()
    async def clear_demo_owner_token(self, session) -> bool:
        """Clear demo owner token"""
        
        try:
            await session.execute(delete(DemoOwnerToken))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear demo owner token: {e}")
            return False
# Create singleton instance
db_service = DatabaseService()

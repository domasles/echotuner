"""Playlist-related endpoint implementations"""

import logging
import uuid
import re

from fastapi import HTTPException, APIRouter

from core.auth.decorators import debug_only

from models import PlaylistRequest, PlaylistResponse, PlaylistDraftRequest, LibraryPlaylistsRequest, LibraryPlaylistsResponse, SpotifyPlaylistInfo

from config.settings import settings

from services.playlist.generator import playlist_generator_service
from services.playlist.spotify import spotify_playlist_service
from services.ai.prompt import prompt_validator_service
from services.playlist.draft import playlist_draft_service
from services.rate_limiting.rate_limiter import rate_limiter_service
from services.personality.personality import personality_service
from core.auth.middleware import auth_middleware
from services.database.database import db_service
from services.auth.auth import auth_service

from utils.input_validator import InputValidator

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/playlist", tags=["playlists"])

async def require_auth(request: PlaylistRequest):
    if not settings.AUTH_REQUIRED:
        return None

    if not await auth_service.validate_device(request.device_id):
        raise HTTPException(status_code=403, detail="Invalid device ID. Please register device first.")

    if not hasattr(request, 'session_id') or not request.session_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        return user_info

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/generate", response_model=PlaylistResponse)
async def generate_playlist(request: PlaylistRequest):
    """Generate a playlist using AI-powered real-time song search"""

    try:
        sanitized_prompt = InputValidator.validate_prompt(request.prompt)
        validated_device_id = InputValidator.validate_device_id(request.device_id)
        validated_session_id = InputValidator.validate_session_id(request.session_id)
        validated_count = InputValidator.validate_count(request.count, min_count=1, max_count=100)

        user_info = await require_auth(request)

        if user_info and user_info.get('account_type') == 'demo':
            rate_limit_key = validated_device_id

        else:
            rate_limit_key = user_info["spotify_user_id"] if user_info else validated_device_id

        if settings.PLAYLIST_LIMIT_ENABLED and not await rate_limiter_service.can_make_request(rate_limit_key):
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit of {settings.MAX_PLAYLISTS_PER_DAY} playlists reached. Try again tomorrow."
            )

        is_valid_prompt = await prompt_validator_service.validate_prompt(sanitized_prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The prompt doesn't seem to be related to music or mood. Please try a different description."
            )

        user_context = request.user_context

        if not user_context and request.session_id:
            try:
                user_context = await personality_service.get_user_personality(
                    session_id=request.session_id,
                    device_id=request.device_id
                )

            except Exception as e:
                logger.warning(f"Failed to load user personality: {e}")

        if user_context and validated_session_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists(
                    session_id=validated_session_id,
                    device_id=validated_device_id,
                    user_context=user_context
                )

                user_context.favorite_artists = merged_artists

            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.generate_playlist(
            prompt=sanitized_prompt,
            user_context=user_context,
            count=validated_count if settings.DEBUG else settings.MAX_SONGS_PER_PLAYLIST,
            discovery_strategy=request.discovery_strategy or "balanced",
            session_id=request.session_id,
            device_id=request.device_id
        )

        if user_info and user_info.get('account_type') == 'demo':
            playlist_id = str(uuid.uuid4())

            await db_service.add_demo_playlist(
                playlist_id=playlist_id,
                device_id=request.device_id,
                session_id=request.session_id,
                prompt=sanitized_prompt
            )

        else:
            playlist_id = await playlist_draft_service.save_draft(
                device_id=request.device_id,
                session_id=request.session_id,
                prompt=sanitized_prompt,
                songs=songs
            )

        if settings.PLAYLIST_LIMIT_ENABLED:
            await rate_limiter_service.record_request(rate_limit_key)

        return PlaylistResponse(
            songs=songs,
            generated_from=sanitized_prompt,
            total_count=len(songs),
            playlist_id=playlist_id
        )

    except ValueError as e:
        logger.warning(f"Playlist generation input validation failed: {e}")
        sanitized_error = InputValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=400, detail=f"Invalid input: {sanitized_error}")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Playlist generation failed: {e}")
        sanitized_error = InputValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=500, detail=f"Error generating playlist: {sanitized_error}")

@router.post("/update-draft", response_model=PlaylistResponse)
async def update_playlist_draft(request: PlaylistRequest):
    """Update an existing playlist draft"""
    
    try:
        user_info = await require_auth(request)
        playlist_id = request.playlist_id
        current_songs = request.current_songs or []

        logger.info(f"Update draft request - playlist_id: {playlist_id}, current_songs count: {len(current_songs)}")
        logger.info(f"User info: {user_info}")

        if not playlist_id:
            raise HTTPException(status_code=400, detail="Playlist ID is required for updates")

        # Check if this is a demo user
        if user_info and user_info.get('account_type') == 'demo':
            # For demo users, handle differently - don't save to database, just return the response
            logger.info("Demo user - not saving draft to database")
            return PlaylistResponse(
                songs=current_songs,
                generated_from=request.prompt or "Updated playlist",
                total_count=len(current_songs),
                playlist_id=playlist_id
            )

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            logger.warning(f"Draft not found for playlist_id: {playlist_id}")
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        success = await playlist_draft_service.update_draft(
            draft_id=playlist_id,
            songs=current_songs,
            prompt=request.prompt or draft.prompt
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update draft playlist")

        return PlaylistResponse(
            songs=current_songs,
            generated_from=request.prompt or draft.prompt,
            total_count=len(current_songs),
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        sanitized_error = InputValidator.sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail=f"Error updating playlist draft: {sanitized_error}")

@router.post("/library", response_model=LibraryPlaylistsResponse)
async def get_library_playlists(request: LibraryPlaylistsRequest):
    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)
        spotify_user_id = user_info.get("spotify_user_id")
        drafts = []

        try:
            drafts = await playlist_draft_service.get_user_drafts(
                user_id=spotify_user_id,
                device_id=request.device_id,
                session_id=request.session_id,
                include_spotify=False
            )

        except Exception as e:
            logger.warning(f"Failed to get user drafts for {spotify_user_id}: {e}")

        if not drafts:
            logger.debug(f"No user-based drafts found for {spotify_user_id}, falling back to device drafts")

            try:
                drafts = await playlist_draft_service.get_device_drafts(
                    device_id=request.device_id,
                    include_spotify=False
                )

            except Exception as e:
                logger.error(f"Failed to get device drafts: {e}")
                drafts = []

        spotify_playlists = []

        if spotify_playlist_service.is_ready():
            try:
                access_token = await auth_service.get_access_token(request.session_id)

                if access_token:
                    echotuner_playlist_ids = await playlist_draft_service.get_user_echotuner_spotify_playlist_ids(
                        user_info.get('spotify_user_id')
                    )

                    if echotuner_playlist_ids:
                        all_playlists = await spotify_playlist_service.get_user_playlists(access_token)
                        spotify_playlists = []

                        for playlist in all_playlists:
                            if playlist.get('id') in echotuner_playlist_ids:
                                try:
                                    playlist_details = await spotify_playlist_service.get_playlist_details(access_token, playlist['id'])
                                    tracks_count = playlist_details.get('tracks', {}).get('total', 0)

                                except Exception as e:
                                    logger.warning(f"Failed to get fresh track count for playlist {playlist['id']}: {e}")
                                    tracks_count = playlist.get('tracks', {}).get('total', 0)

                                spotify_playlist_info = SpotifyPlaylistInfo(
                                    id=playlist['id'],
                                    name=playlist.get('name', 'Unknown'),
                                    description=playlist.get('description'),
                                    tracks_count=tracks_count,
                                    spotify_url=playlist.get('external_urls', {}).get('spotify'),
                                    images=playlist.get('images', [])
                                )

                                spotify_playlists.append(spotify_playlist_info)

            except Exception as e:
                logger.warning(f"Failed to fetch Spotify playlists: {e}")

        return LibraryPlaylistsResponse(
            drafts=drafts,
            spotify_playlists=spotify_playlists
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get library playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to get library playlists")

@router.post("/drafts")
async def get_draft_playlist(request: PlaylistDraftRequest):
    """Get a specific draft playlist."""

    try:
        draft = await playlist_draft_service.get_draft(request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != request.device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return draft

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get draft playlist {request.playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get draft playlist")

@router.delete("/drafts")
@debug_only
async def delete_draft_playlist(request: PlaylistDraftRequest):
    """Delete a draft playlist."""

    try:
        draft = await playlist_draft_service.get_draft(request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != request.device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if draft.status != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft playlists")

        success = await playlist_draft_service.delete_draft(request.playlist_id)

        if success:
            return {"message": "Draft playlist deleted successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete draft playlist {request.playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

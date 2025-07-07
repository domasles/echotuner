"""Playlist-related endpoint implementations"""

import logging
import uuid
import re

from fastapi import HTTPException

from core.models import PlaylistRequest, PlaylistResponse, LibraryPlaylistsRequest, LibraryPlaylistsResponse, SpotifyPlaylistInfo

from services.spotify_playlist_service import spotify_playlist_service
from services.playlist_generator import playlist_generator_service
from services.playlist_draft_service import playlist_draft_service
from services.prompt_validator import prompt_validator_service
from services.personality_service import personality_service
from services.rate_limiter import rate_limiter_service
from services.auth_middleware import auth_middleware
from services.database_service import db_service
from services.auth_service import auth_service

from config.settings import settings

logger = logging.getLogger(__name__)

def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input to prevent injection attacks"""

    if not text:
        return ""

    if max_length is None:
        max_length = settings.MAX_PROMPT_LENGTH

    text = text[:max_length]
    text = re.sub(r'\s+', ' ', text).strip()
  
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'expression\s*\(',
        r'eval\s*\(',
        r'<.*?onerror.*?>',
        r'<.*?onload.*?>',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text

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

async def generate_playlist(request: PlaylistRequest):
    """Generate a playlist using AI-powered real-time song search"""

    try:
        sanitized_prompt = sanitize_user_input(request.prompt)

        if not sanitized_prompt:
            raise HTTPException(status_code=400, detail="Invalid or empty prompt")

        user_info = await require_auth(request)

        if user_info and user_info.get('account_type') == 'demo':
            rate_limit_key = request.device_id

        else:
            rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id

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

        if user_context and request.session_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists(
                    session_id=request.session_id,
                    device_id=request.device_id,
                    user_context=user_context
                )

                user_context.favorite_artists = merged_artists

            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.generate_playlist(
            prompt=sanitized_prompt,
            user_context=user_context,
            count=request.count if settings.DEBUG else settings.MAX_SONGS_PER_PLAYLIST,
            discovery_strategy=request.discovery_strategy or "balanced"
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
                songs=songs,
                refinements_used=0
            )

        if settings.PLAYLIST_LIMIT_ENABLED:
            await rate_limiter_service.record_request(rate_limit_key)

        return PlaylistResponse(
            songs=songs,
            generated_from=sanitized_prompt,
            total_count=len(songs),
            is_refinement=False,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating playlist: {str(e)}")

async def refine_playlist(request: PlaylistRequest):
    """Refine an existing playlist based on user feedback"""

    try:
        user_info = await require_auth(request)
        current_songs = request.current_songs or []
        refinements_used = 0
        playlist_id = request.playlist_id

        if playlist_id:
            if user_info and user_info.get('account_type') == 'demo':
                refinements_used = await db_service.get_demo_playlist_refinements(playlist_id)
                logger.info(f"Demo playlist {playlist_id} has {refinements_used} refinements used")
                current_songs = request.current_songs or []

                if settings.REFINEMENT_LIMIT_ENABLED and refinements_used >= settings.MAX_REFINEMENTS_PER_PLAYLIST:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Maximum of {settings.MAX_REFINEMENTS_PER_PLAYLIST} AI refinements reached for this playlist."
                    )
            else:
                draft = await playlist_draft_service.get_draft(playlist_id)

                if draft:
                    current_songs = draft.songs
                    refinements_used = draft.refinements_used

                    if settings.REFINEMENT_LIMIT_ENABLED and refinements_used >= settings.MAX_REFINEMENTS_PER_PLAYLIST:
                        raise HTTPException(
                            status_code=429,
                            detail=f"Maximum of {settings.MAX_REFINEMENTS_PER_PLAYLIST} AI refinements reached for this playlist."
                        )

                else:
                    logger.warning(f"Draft playlist {playlist_id} not found, using provided songs")

        else:
            if user_info and user_info.get('account_type') == 'demo':
                rate_limit_key = request.device_id

            else:
                rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id

            if settings.REFINEMENT_LIMIT_ENABLED and not await rate_limiter_service.can_refine_playlist(rate_limit_key):
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum daily refinements reached."
                )

        is_valid_prompt = await prompt_validator_service.validate_prompt(request.prompt)

        if not is_valid_prompt:
            raise HTTPException(
                status_code=400,
                detail="The refinement request doesn't seem to be music-related. Please try a different description."
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

        if user_context and request.session_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists(
                    session_id=request.session_id,
                    device_id=request.device_id,
                    user_context=user_context
                )

                user_context.favorite_artists = merged_artists

            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.refine_playlist(
            original_songs=current_songs,
            refinement_prompt=request.prompt,
            user_context=user_context,
            count=request.count or 30,
            discovery_strategy=request.discovery_strategy or "balanced"
        )

        if playlist_id:
            if user_info and user_info.get('account_type') == 'demo':
                await db_service.increment_demo_playlist_refinements(playlist_id)
                logger.info(f"Incremented demo playlist {playlist_id} refinement count")

            else:
                await playlist_draft_service.update_draft(
                    playlist_id=playlist_id,
                    songs=songs,
                    refinements_used=refinements_used + 1
                )

        else:
            playlist_id = await playlist_draft_service.save_draft(
                device_id=request.device_id,
                session_id=request.session_id,
                prompt=f"Refined: {request.prompt}",
                songs=songs,
                refinements_used=1
            )

            if user_info and user_info.get('account_type') == 'demo':
                await db_service.add_demo_playlist(
                    playlist_id=playlist_id,
                    device_id=request.device_id,
                    session_id=request.session_id,
                    prompt=f"Refined: {request.prompt}"
                )

                await db_service.increment_demo_playlist_refinements(playlist_id)

            if settings.REFINEMENT_LIMIT_ENABLED:
                if user_info and user_info.get('account_type') == 'demo':
                    rate_limit_key = request.device_id

                else:
                    rate_limit_key = user_info["spotify_user_id"] if user_info else request.device_id

                logger.info(f"Recording refinement for rate_limit_key: {rate_limit_key}")
                await rate_limiter_service.record_refinement(rate_limit_key)

        return PlaylistResponse(
            songs=songs,
            generated_from=request.prompt,
            total_count=len(songs),
            is_refinement=True,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining playlist: {str(e)}")

async def update_playlist_draft(request: PlaylistRequest):
    """Update an existing playlist draft without AI refinement (no refinement count increase)"""
    
    try:
        user_info = await require_auth(request)
        playlist_id = request.playlist_id
        current_songs = request.current_songs or []

        if not playlist_id:
            raise HTTPException(status_code=400, detail="Playlist ID is required for updates")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        success = await playlist_draft_service.update_draft(
            playlist_id=playlist_id,
            songs=current_songs,
            refinements_used=draft.refinements_used,
            prompt=request.prompt or draft.prompt
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update draft playlist")

        return PlaylistResponse(
            songs=current_songs,
            generated_from=request.prompt or draft.prompt,
            total_count=len(current_songs),
            is_refinement=False,
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating playlist draft: {str(e)}")

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
            logger.info(f"No user-based drafts found for {spotify_user_id}, falling back to device drafts")

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
                                    refinements_used=0,
                                    max_refinements=0,
                                    can_refine=False,
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

async def get_draft_playlist(playlist_id: str, device_id: str = None):
    """Get a specific draft playlist."""

    try:
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id parameter required")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return draft

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get draft playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get draft playlist")

async def delete_draft_playlist(playlist_id: str, device_id: str = None):
    """Delete a draft playlist."""

    try:
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id parameter required")

        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.device_id != device_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if draft.status != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft playlists")

        success = await playlist_draft_service.delete_draft(playlist_id)

        if success:
            return {"message": "Draft playlist deleted successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete draft playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

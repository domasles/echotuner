"""Playlist-related endpoint implementations"""

import logging
import uuid

from datetime import datetime
from fastapi import HTTPException, APIRouter, Request

from domain.auth.decorators import debug_only
from domain.shared.validation.validators import validate_request, validate_user_request, UniversalValidator

from application import PlaylistRequest, PlaylistResponse, PlaylistDraftRequest, LibraryPlaylistsRequest, LibraryPlaylistsResponse, SpotifyPlaylistInfo

from infrastructure.config.settings import settings
from infrastructure.database.repository import repository
from infrastructure.database.models import UserAccount

from domain.playlist.generator import playlist_generator_service
from domain.playlist.spotify import spotify_playlist_service
from domain.playlist.draft import playlist_draft_service
from infrastructure.rate_limiting.limit_service import rate_limiter_service
from domain.personality.service import personality_service
from infrastructure.auth.oauth_service import oauth_service

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/playlist", tags=["playlists"])

@router.post("/generate", response_model=PlaylistResponse)
@validate_user_request()
async def generate_playlist(request: Request, playlist_request: PlaylistRequest, validated_user_id: str = None):
    """Generate a playlist using AI-powered real-time song search"""

    try:
        # Get user_id from validated header
        user_id = validated_user_id

        # Use user_id as rate limiting key for both shared and normal modes
        if settings.PLAYLIST_LIMIT_ENABLED and not await rate_limiter_service.can_make_request(user_id):
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit of {settings.MAX_PLAYLISTS_PER_DAY} playlists reached. Try again tomorrow."
            )

        user_context = playlist_request.user_context

        # In the new system, personality is tied to user_id instead of session_id/device_id
        if not user_context and user_id:
            try:
                user_context = await personality_service.get_user_personality_by_user_id(user_id)
            except Exception as e:
                logger.warning(f"Failed to load user personality: {e}")

        if user_context and user_id:
            try:
                merged_artists = await personality_service.get_merged_favorite_artists_by_user_id(
                    user_id=user_id,
                    user_context=user_context
                )
                user_context.favorite_artists = merged_artists
            except Exception as e:
                logger.warning(f"Failed to merge favorite artists: {e}")

        songs = await playlist_generator_service.generate_playlist(
            prompt=playlist_request.prompt,
            user_context=user_context,
            count=playlist_request.count if settings.DEBUG else settings.MAX_SONGS_PER_PLAYLIST,
            discovery_strategy=playlist_request.discovery_strategy or "balanced",
            user_id=user_id
        )

        # For shared mode (Google SSO), save as draft like normal mode
        # No more demo/normal distinction - all users get draft functionality
        playlist_id = await playlist_draft_service.save_draft(
            user_id=user_id,
            prompt=playlist_request.prompt,
            songs=songs
        )

        if settings.PLAYLIST_LIMIT_ENABLED:
            await rate_limiter_service.record_request(user_id)

        return PlaylistResponse(
            songs=songs,
            generated_from=playlist_request.prompt,
            total_count=len(songs),
            playlist_id=playlist_id
        )

    except ValueError as e:
        logger.warning(f"Playlist generation input validation failed: {e}")
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=400, detail=f"Invalid input: {sanitized_error}")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Playlist generation failed: {e}")
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))

        raise HTTPException(status_code=500, detail=f"Error generating playlist: {sanitized_error}")

@router.post("/update-draft", response_model=PlaylistResponse)
@validate_user_request()
async def update_playlist_draft(request: Request, playlist_request: PlaylistRequest, validated_user_id: str = None):
    """Update an existing playlist draft"""
    
    try:
        user_id = validated_user_id
        playlist_id = playlist_request.playlistId
        current_songs = playlist_request.currentSongs or []

        logger.info(f"Update draft request - playlist_id: {playlist_id}, current_songs count: {len(current_songs)}")
        logger.info(f"User ID: {user_id}")

        if not playlist_id:
            raise HTTPException(status_code=400, detail="Playlist ID is required for updates")

        # No more demo/normal distinction - all users use the same logic
        draft = await playlist_draft_service.get_draft(playlist_id)
        if not draft:
            logger.warning(f"Draft not found for playlist_id: {playlist_id}")
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        # Update the draft
        success = await playlist_draft_service.update_draft(playlist_id, current_songs, playlist_request.prompt)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update draft")

        return PlaylistResponse(
            songs=current_songs,
            generated_from=playlist_request.prompt or draft.prompt,
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
        sanitized_error = UniversalValidator.sanitize_error_message(str(e))
        raise HTTPException(status_code=500, detail=f"Error updating playlist draft: {sanitized_error}")

@router.post("/library", response_model=LibraryPlaylistsResponse)
@validate_user_request()
async def get_library_playlists(request: Request, library_request: LibraryPlaylistsRequest, validated_user_id: str = None):
    try:
        user_id = validated_user_id
        
        drafts = []

        try:
            drafts = await playlist_draft_service.get_user_drafts(
                user_id=user_id,
                include_spotify=False
            )
        except Exception as e:
            logger.warning(f"Failed to get user drafts for {user_id}: {e}")

        spotify_playlists = []

        # Only get Spotify playlists for normal mode (Spotify OAuth users)
        if spotify_playlist_service.is_ready() and not settings.SHARED:
            try:
                # For normal mode, get Spotify access token from our OAuth service
                access_token = await oauth_service.get_access_token(request.user_id)

                if access_token:
                    echotuner_playlist_ids = await playlist_draft_service.get_user_echotuner_spotify_playlist_ids(
                        request.user_id
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
@validate_request('user_id')
async def get_draft_playlist(request: PlaylistDraftRequest):
    """Get a specific draft playlist."""

    try:
        draft = await playlist_draft_service.get_draft(request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.user_id != request.user_id:
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

        if draft.user_id != request.user_id:
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

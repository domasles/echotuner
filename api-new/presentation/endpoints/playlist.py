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
from domain.auth.service import auth_service
from infrastructure.rate_limiting.limit_service import rate_limiter_service
from domain.personality.service import personality_service

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

        # Unified system - personality is tied to user_id
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
        # All users get draft functionality in the unified system
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
        playlist_id = playlist_request.playlist_id
        current_songs = playlist_request.current_songs or []

        logger.info(f"Update draft request - playlist_id: {playlist_id}, current_songs count: {len(current_songs)}")
        logger.info(f"User ID: {user_id}")

        if not playlist_id:
            raise HTTPException(status_code=400, detail="Playlist ID is required for updates")

        # Unified system - all users use the same logic
        draft = await playlist_draft_service.get_draft(playlist_id)
        if not draft:
            logger.warning(f"Draft not found for playlist_id: {playlist_id}")
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        # Update the draft
        updated_draft_id = await playlist_draft_service.update_draft(
            draft_id=playlist_id,
            user_id=user_id,
            prompt=playlist_request.prompt or draft.prompt,
            songs=current_songs
        )
        if not updated_draft_id:
            raise HTTPException(status_code=500, detail="Failed to update draft")

        return PlaylistResponse(
            songs=current_songs,
            generated_from=playlist_request.prompt or draft.prompt,
            total_count=len(current_songs),
            playlist_id=playlist_id
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to update draft playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to update draft playlist")

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
            all_drafts = await playlist_draft_service.get_user_drafts(
                user_id=user_id,
                include_spotify=False
            )
            # Filter out drafts that have been added to Spotify
            drafts = [draft for draft in all_drafts if draft.status != 'added_to_spotify']
        except Exception as e:
            logger.warning(f"Failed to get user drafts for {user_id}: {e}")

        spotify_playlists = []

        # Get Spotify playlists for both modes
        if spotify_playlist_service.is_ready():
            try:
                # Get access token (works for both shared and normal mode)
                access_token = await auth_service.get_access_token_by_user_id(user_id)

                if access_token:
                    echotuner_playlist_ids = await playlist_draft_service.get_user_echotuner_spotify_playlist_ids(
                        user_id
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
@validate_user_request()
async def get_draft_playlist(request: Request, playlist_draft_request: PlaylistDraftRequest, validated_user_id: str = None):
    """Get a specific draft playlist."""

    try:
        user_id = validated_user_id
        draft = await playlist_draft_service.get_draft(playlist_draft_request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        return draft

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get draft playlist {request.playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get draft playlist")

@router.delete("/drafts")
@validate_user_request()
async def delete_draft_playlist(request: Request, playlist_draft_request: PlaylistDraftRequest, validated_user_id: str = None):
    """Delete a draft playlist."""

    try:
        user_id = validated_user_id
        draft = await playlist_draft_service.get_draft(playlist_draft_request.playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Draft playlist not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if draft.status != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft playlists")

        success = await playlist_draft_service.delete_draft(playlist_draft_request.playlist_id)

        if success:
            return {"message": "Draft playlist deleted successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete draft playlist {playlist_draft_request.playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft playlist")

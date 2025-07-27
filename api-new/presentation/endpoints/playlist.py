"""Playlist endpoint implementations"""

import logging
import uuid

from datetime import datetime
from typing import Union
from fastapi import HTTPException, APIRouter, Request

from domain.auth.decorators import debug_only
from domain.shared.validation.validators import validate_request, validate_user_request, UniversalValidator

from application import PlaylistRequest, PlaylistResponse, LibraryPlaylistsResponse, SpotifyPlaylistInfo, SpotifyPlaylistRequest, SpotifyPlaylistResponse

from infrastructure.config import app_constants
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
router = APIRouter(prefix="/playlists", tags=["playlists"])

@router.post("", response_model=Union[PlaylistResponse, SpotifyPlaylistResponse])
@validate_user_request()
async def generate_or_create_playlist(request: Request, playlist_request: Union[PlaylistRequest, SpotifyPlaylistRequest], validated_user_id: str = None):
    """Generate a new playlist or create a Spotify playlist from draft based on status parameter"""

    try:
        user_id = validated_user_id
        status = request.query_params.get('status', 'draft')
        
        # Validate status parameter - default to 'draft' if invalid
        if status not in ['draft', 'spotify']:
            status = 'draft'
        
        if status == 'spotify':
            # Ensure we have a SpotifyPlaylistRequest for Spotify creation
            if not isinstance(playlist_request, SpotifyPlaylistRequest):
                raise HTTPException(status_code=400, detail="SpotifyPlaylistRequest required for Spotify playlist creation")
                
            # Create Spotify playlist from draft
            playlist_id = request.headers.get('X-Playlist-ID') or request.headers.get('x-playlist-id')
            if not playlist_id:
                raise HTTPException(status_code=400, detail="X-Playlist-ID header is required for Spotify playlist creation")
            
            # Get the draft
            draft = await playlist_draft_service.get_draft(playlist_id)
            if not draft:
                raise HTTPException(status_code=404, detail="Draft playlist not found")
            if draft.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Create Spotify playlist (logic from old spotify endpoint)
            if not spotify_playlist_service.is_ready():
                raise HTTPException(status_code=503, detail="Spotify playlist service not available")

            access_token = await auth_service.get_access_token_by_user_id(user_id)
            if not access_token:
                if settings.SHARED:
                    raise HTTPException(status_code=401, detail="No valid Spotify credentials for shared account")
                else:
                    raise HTTPException(status_code=401, detail="No valid Spotify access token")

            # Use proper fields from SpotifyPlaylistRequest
            playlist_name = playlist_request.name
            description = playlist_request.description or app_constants.DEFAULT_PLAYLIST_DESCRIPTION
            public = playlist_request.public or False
            
            # In shared mode, use songs from request if provided, otherwise use draft songs
            if settings.SHARED and playlist_request.songs:
                songs = playlist_request.songs
            else:
                songs = draft.songs

            spotify_playlist_id, playlist_url = await spotify_playlist_service.create_playlist(
                access_token=access_token,
                playlist_name=playlist_name,
                songs=songs,
                description=description,
                public=public
            )

            await playlist_draft_service.mark_as_added_to_spotify(
                playlist_id=playlist_id,
                spotify_playlist_id=spotify_playlist_id,
                spotify_url=playlist_url,
                user_id=user_id,
                playlist_name=playlist_name
            )

            logger.debug(f"Created Spotify playlist {spotify_playlist_id} from draft {playlist_id}")

            return SpotifyPlaylistResponse(
                success=True,
                spotify_playlist_id=spotify_playlist_id,
                playlist_url=playlist_url,
                message="Playlist created successfully"
            )
        
        else:
            # Generate new playlist (existing logic)
            # Ensure we have a PlaylistRequest for draft generation
            if not isinstance(playlist_request, PlaylistRequest):
                raise HTTPException(status_code=400, detail="PlaylistRequest required for draft generation")
                
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
                    user_context.context['favorite_artists'] = merged_artists
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

@router.put("", response_model=PlaylistResponse)
@validate_user_request()
async def update_playlist_draft(request: Request, playlist_request: PlaylistRequest, validated_user_id: str = None):
    """Update an existing playlist draft"""
    
    try:
        user_id = validated_user_id
        
        # Get playlist ID from headers
        playlist_id = request.headers.get('X-Playlist-ID') or request.headers.get('x-playlist-id')
        if not playlist_id:
            raise HTTPException(status_code=400, detail="X-Playlist-ID header is required for updates")
        
        current_songs = playlist_request.current_songs or []

        logger.info(f"Update draft request - playlist_id: {playlist_id}, current_songs count: {len(current_songs)}")
        logger.info(f"User ID: {user_id}")

        if not playlist_id:
            raise HTTPException(status_code=400, detail="X-Playlist-ID header is required for updates")

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

@router.get("", response_model=LibraryPlaylistsResponse)
@validate_user_request()
async def get_playlists(request: Request, validated_user_id: str = None):
    """Get playlists - all playlists or specific playlist based on X-Playlist-ID header"""
    
    try:
        user_id = validated_user_id
        
        # Check if specific playlist ID is requested
        playlist_id = request.headers.get('X-Playlist-ID') or request.headers.get('x-playlist-id')
        
        if playlist_id:
            # Get specific playlist
            draft = await playlist_draft_service.get_draft(playlist_id)
            if not draft:
                raise HTTPException(status_code=404, detail="Playlist not found")
            if draft.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            return LibraryPlaylistsResponse(
                drafts=[draft],
                spotify_playlists=[]
            )
        
        # Get all playlists (existing library logic)
        status_filter = request.query_params.get('status', 'all')
        
        drafts = []
        spotify_playlists = []

        if status_filter in ['all', 'draft']:
            try:
                all_drafts = await playlist_draft_service.get_user_drafts(
                    user_id=user_id,
                    include_spotify=False
                )
                # Filter out drafts that have been added to Spotify
                drafts = [draft for draft in all_drafts if draft.status != 'added_to_spotify']
            except Exception as e:
                logger.warning(f"Failed to get user drafts for {user_id}: {e}")

        if status_filter in ['all', 'spotify']:
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
        logger.error(f"Failed to get playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to get playlists")

@router.delete("", response_model=dict)
@validate_user_request()
async def delete_playlist(request: Request, validated_user_id: str = None):
    """Delete a specific playlist."""

    try:
        user_id = validated_user_id
        
        # Get playlist ID from headers
        playlist_id = request.headers.get('X-Playlist-ID') or request.headers.get('x-playlist-id')
        if not playlist_id:
            raise HTTPException(status_code=400, detail="X-Playlist-ID header is required")
        
        draft = await playlist_draft_service.get_draft(playlist_id)

        if not draft:
            raise HTTPException(status_code=404, detail="Playlist not found")

        if draft.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if draft.status != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft playlists")

        success = await playlist_draft_service.delete_draft(playlist_id)

        if success:
            return {"message": "Playlist deleted successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to delete playlist")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to delete playlist {playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete playlist")

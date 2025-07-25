"""Spotify-related endpoint implementations"""

import logging

from fastapi import HTTPException, APIRouter

from domain.auth.decorators import debug_only
from domain.shared.validation.validators import validate_request

from application import SpotifyPlaylistRequest, SpotifyPlaylistResponse, SpotifyPlaylistTracksRequest, SpotifyPlaylistTrackRemoveRequest

from domain.playlist.spotify import spotify_playlist_service
from domain.playlist.draft import playlist_draft_service
from infrastructure.auth.oauth_service import oauth_service
from infrastructure.database.repository import repository
from infrastructure.database.models import UserAccount
from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/spotify", tags=["spotify"])

async def require_auth(user_id: str):
    """Validate user authentication with new unified system."""
    if not settings.AUTH_REQUIRED:
        return None

    try:
        # Validate the user exists in our database
        user_account = await repository.get_by_field(UserAccount, "user_id", user_id)
        if not user_account:
            raise HTTPException(status_code=401, detail="Invalid user ID. Please authenticate first.")
        
        return {
            "user_id": user_id,
            "account_type": "shared" if settings.SHARED else "normal"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("/create-playlist", response_model=SpotifyPlaylistResponse)
@validate_request('user_id')
async def create_spotify_playlist(request: SpotifyPlaylistRequest):
    """Create a Spotify playlist from a draft."""

    try:
        user_info = await require_auth(request.user_id)

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        # In shared mode (Google SSO), require songs list since there's no Spotify OAuth
        if settings.SHARED:
            if not request.songs:
                raise HTTPException(status_code=400, detail="Songs list required for shared mode")
            songs = request.songs
            draft = None
        else:
            # Normal mode - get draft playlist
            draft = await playlist_draft_service.get_draft(request.playlist_id)

            if not draft:
                raise HTTPException(status_code=404, detail="Draft playlist not found")

            if draft.user_id != request.user_id:
                raise HTTPException(status_code=403, detail="This draft belongs to a different user")

            songs = draft.songs

        # For normal mode, get Spotify access token
        if not settings.SHARED:
            access_token = await oauth_service.get_access_token(request.user_id)

            if not access_token:
                raise HTTPException(status_code=401, detail="No valid Spotify access token")

            spotify_playlist_id, playlist_url = await spotify_playlist_service.create_playlist(
                access_token=access_token,
                playlist_name=request.name,
                songs=songs,
                description=request.description,
                public=request.public or False
            )

            if draft:
                await playlist_draft_service.mark_as_added_to_spotify(
                    playlist_id=request.playlist_id,
                    spotify_playlist_id=spotify_playlist_id,
                    spotify_url=playlist_url,
                    user_id=request.user_id,
                    playlist_name=request.name
                )

            logger.debug(f"Created Spotify playlist {spotify_playlist_id} from draft {request.playlist_id}")

            return SpotifyPlaylistResponse(
                success=True,
                spotify_playlist_id=spotify_playlist_id,
                playlist_url=playlist_url,
                message="Playlist created successfully"
            )
        else:
            # Shared mode - no Spotify playlist creation, return error or alternative behavior
            raise HTTPException(status_code=400, detail="Spotify playlist creation not available in shared mode")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to create Spotify playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Spotify playlist")

@router.post("/playlist/tracks")
@validate_request('user_id')
async def get_spotify_playlist_tracks(request: SpotifyPlaylistTracksRequest):
    """Get tracks from a Spotify playlist."""

    try:
        user_info = await require_auth(request.user_id)

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        # Only available in normal mode
        if settings.SHARED:
            raise HTTPException(status_code=400, detail="Spotify playlist access not available in shared mode")

        access_token = await oauth_service.get_access_token(request.user_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid Spotify access token")

        tracks = await spotify_playlist_service.get_playlist_tracks(access_token, request.playlist_id)

        return {"tracks": tracks}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get Spotify playlist tracks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Spotify playlist tracks")

@router.delete("/playlist/track")
async def remove_track_from_spotify_playlist(request: SpotifyPlaylistTrackRemoveRequest):
    """Remove a track from a Spotify playlist."""

    try:
        user_info = await require_auth(request.user_id)

        if settings.SHARED:
            raise HTTPException(status_code=400, detail="Spotify playlist modification not available in shared mode")

        access_token = await oauth_service.get_access_token(request.user_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid Spotify access token")

        success = await spotify_playlist_service.remove_track_from_playlist(access_token, request.playlist_id, request.track_uri)

        if success:
            return {"message": "Track removed successfully"}

        else:
            raise HTTPException(status_code=500, detail="Failed to remove track from Spotify")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to remove track from Spotify playlist {request.playlist_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove track from playlist")

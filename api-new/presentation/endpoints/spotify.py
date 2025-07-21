"""Spotify-related endpoint implementations"""

import logging

from fastapi import HTTPException, APIRouter

from domain.auth.decorators import debug_only
from domain.shared.validation.validators import validate_request

from application import SpotifyPlaylistRequest, SpotifyPlaylistResponse, SpotifyPlaylistTracksRequest, SpotifyPlaylistTrackRemoveRequest

from domain.playlist.spotify import spotify_playlist_service
from domain.playlist.draft import playlist_draft_service
from domain.auth.middleware import auth_middleware
from domain.auth.service import auth_service

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/spotify", tags=["spotify"])

@router.post("/create-playlist", response_model=SpotifyPlaylistResponse)
@validate_request('session_id', 'device_id')
async def create_spotify_playlist(request: SpotifyPlaylistRequest):
    """Create a Spotify playlist from a draft."""

    try:
        user_info = await auth_middleware.validate_session_from_request(request.session_id, request.device_id)

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        if user_info and user_info.get('account_type') == 'demo':
            if not request.songs:
                raise HTTPException(status_code=400, detail="Songs list required for demo accounts")

            songs = request.songs
            draft = None

        else:
            draft = await playlist_draft_service.get_draft(request.playlist_id)

            if not draft:
                raise HTTPException(status_code=404, detail="Draft playlist not found")

            songs = draft.songs

        if draft and draft.session_id and draft.session_id != request.session_id:
            draft_user_info = await auth_service.get_user_from_session(draft.session_id)
            current_user_spotify_id = user_info.get('spotify_user_id')
            draft_user_spotify_id = draft_user_info.get('spotify_user_id') if draft_user_info else None

            logger.debug(f"Cross-device check: draft user {draft_user_spotify_id}, current user {current_user_spotify_id}")
            logger.debug(f"Draft user info: {draft_user_info}")
            logger.debug(f"Current user info: {user_info}")

            if current_user_spotify_id != draft_user_spotify_id:
                logger.warning(f"Access denied: draft belongs to user {draft_user_spotify_id}, current user is {current_user_spotify_id}")
                raise HTTPException(status_code=403, detail="This draft belongs to a different user")

        elif draft and not draft.session_id and draft.device_id != request.device_id:
            logger.warning(f"Access denied: draft device {draft.device_id}, current device {request.device_id}")
            raise HTTPException(status_code=403, detail="This draft belongs to a different device")

        access_token = await auth_service.get_access_token(request.session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

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
                user_id=user_info.get('spotify_user_id'),
                device_id=request.device_id,
                session_id=request.session_id,
                playlist_name=request.name
            )

        logger.debug(f"Created Spotify playlist {spotify_playlist_id} from {'draft' if draft else 'demo playlist'} {request.playlist_id}")

        return SpotifyPlaylistResponse(
            success=True,
            spotify_playlist_id=spotify_playlist_id,
            playlist_url=playlist_url,
            message="Playlist created successfully"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to create Spotify playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Spotify playlist")

@router.post("/playlist/tracks")
@validate_request('session_id', 'device_id')
async def get_spotify_playlist_tracks(request: SpotifyPlaylistTracksRequest):
    """Get tracks from a Spotify playlist."""

    try:
        user_info = await auth_service.validate_session_and_get_user(request.session_id, request.device_id)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not spotify_playlist_service.is_ready():
            raise HTTPException(status_code=503, detail="Spotify playlist service not available")

        access_token = await auth_service.get_access_token(request.session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

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
        access_token = await auth_service.get_access_token(request.session_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="No valid access token")

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

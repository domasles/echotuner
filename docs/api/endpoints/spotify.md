# Spotify Endpoints

These endpoints handle Spotify integration for creating playlists and managing tracks.

## POST /spotify/create-playlist

Create a Spotify playlist from a draft.

**Request Body:**
```json
{
    "session_id": "string",
    "device_id": "string", 
    "playlist_id": "string",
    "name": "string",
    "description": "string",
    "public": false
}
```

**Response:**
```json
{
    "success": true,
    "spotify_playlist_id": "string",
    "playlist_url": "string",
    "message": "string"
}
```

## POST /spotify/playlist/tracks

Get tracks from a Spotify playlist.

**Request Body:**
```json
{
    "playlist_id": "string",
    "session_id": "string",
    "device_id": "string"
}
```

**Response:**
```json
{
    "tracks": [
        {
            "id": "string",
            "name": "string", 
            "artists": ["string"],
            "album": "string",
            "uri": "string",
            "external_urls": {
                "spotify": "string"
            }
        }
    ]
}
```

## DELETE /spotify/playlist

Delete or unfollow a Spotify playlist.

**Request Body:**
```json
{
    "playlist_id": "string",
    "session_id": "string",
    "device_id": "string"
}
```

**Response:**
```json
{
  "message": "Playlist deleted/unfollowed successfully"
}
```

## DELETE /spotify/playlist/track

Remove a track from a Spotify playlist.

**Request Body:**
```json
{
    "playlist_id": "string",
    "track_uri": "string",
    "session_id": "string",
    "device_id": "string"
}
```

**Response:**
```json
{
  "message": "Track removed successfully"
}
```

## Error Responses

All Spotify endpoints may return these error responses:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or expired session / No valid access token
- `403 Forbidden`: Insufficient Spotify permissions
- `404 Not Found`: Playlist or track not found
- `500 Internal Server Error`: Failed to perform operation or service error
- `503 Service Unavailable`: Spotify service temporarily unavailable

**Error Format:**
```json
{
  "detail": "string"
}
```

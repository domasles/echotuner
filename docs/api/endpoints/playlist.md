# Playlist Endpoints

Playlist endpoints handle AI-powered playlist generation, refinement, and draft management.

## Core Playlist Operations

### POST `/playlist/generate`

Generate a new playlist using AI-powered real-time song search.

**Request Body:**
```json
{
    "prompt": "upbeat pop songs for working out",
    "session_id": "string",
    "device_id": "string",
    "preferences": {
        "length": 20,
        "energy_level": "high",
        "explicit": false,
        "genres": ["pop", "electronic"],
        "decades": ["2020s", "2010s"]
    }
}
```

**Response:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "title": "Workout Pop Vibes",
    "description": "Upbeat pop songs perfect for your workout",
    "tracks": [
        {
            "id": "spotify-track-id",
            "name": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "duration_ms": 210000,
            "preview_url": "https://p.scdn.co/mp3-preview/...",
            "external_urls": {
                "spotify": "https://open.spotify.com/track/..."
            },
            "energy": 0.8,
            "valence": 0.7,
            "danceability": 0.9
        }
    ],
    "total_tracks": 20,
    "total_duration_ms": 4200000,
    "created_at": "2024-01-01T00:00:00Z",
    "refinements_remaining": 3
}
```

### POST `/playlist/refine`

Refine an existing playlist based on user feedback.

**Request Body:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "session_id": "string",
    "device_id": "string",
    "feedback": {
        "remove_tracks": ["spotify-track-id-1", "spotify-track-id-2"],
        "feedback_text": "Add more energetic songs, remove slow ones",
        "target_length": 25,
        "adjust_energy": "higher"
    }
}
```

**Response:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "title": "Workout Pop Vibes (Refined)",
    "tracks": [...],
    "changes": {
        "added": 7,
        "removed": 2,
        "kept": 18
    },
    "refinements_used": 1,
    "refinements_remaining": 2
}
```

### POST `/playlist/update-draft`

Update playlist draft without AI refinement (no refinement count increase).

**Request Body:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "session_id": "string",
    "device_id": "string",
    "updates": {
        "title": "My Custom Playlist",
        "description": "Custom description",
        "remove_tracks": ["spotify-track-id"],
        "reorder_tracks": [
            {"track_id": "spotify-track-id-1", "new_position": 0},
            {"track_id": "spotify-track-id-2", "new_position": 1}
        ]
    }
}
```

**Response:**
```json
{
  "playlist_id": "uuid-playlist-id",
  "title": "My Custom Playlist",
  "tracks": [...],
  "updated_at": "2024-01-01T00:00:00Z",
  "refinements_remaining": 3
}
```

## Draft Management

### GET `/playlist/drafts/{playlist_id}`

Get a specific draft playlist.

**Path Parameters:**
- `playlist_id`: UUID of the playlist draft

**Query Parameters:**
- `device_id`: Device identifier (optional)

**Response:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "title": "Workout Pop Vibes",
    "description": "AI-generated playlist description",
    "tracks": [...],
    "metadata": {
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "refinements_used": 1,
        "refinements_remaining": 2,
        "original_prompt": "upbeat pop songs for working out"
    },
    "spotify_playlist_id": null
}
```

### DELETE `/playlist/drafts/{playlist_id}`

Delete a draft playlist.

**Path Parameters:**
- `playlist_id`: UUID of the playlist draft

**Query Parameters:**
- `device_id`: Device identifier (optional)

**Response:**
```json
{
  "success": true,
  "message": "Playlist draft deleted successfully",
  "playlist_id": "uuid-playlist-id"
}
```

## Request Parameters

### Playlist Preferences

**Length Options:**
- `10`, `15`, `20`, `25`, `30`, `50` tracks

**Energy Levels:**
- `low`: Calm, relaxing music
- `medium`: Moderate energy
- `high`: Energetic, upbeat music

**Explicit Content:**
- `true`: Include explicit tracks
- `false`: Clean versions only

**Genres:**
- `pop`, `rock`, `hip-hop`, `electronic`, `indie`, `jazz`, `classical`, etc.

**Decades:**
- `1960s`, `1970s`, `1980s`, `1990s`, `2000s`, `2010s`, `2020s`

### Refinement Feedback

**Feedback Types:**
- `remove_tracks`: Array of track IDs to remove
- `feedback_text`: Natural language feedback
- `target_length`: Desired number of tracks
- `adjust_energy`: "higher", "lower", or "same"
- `adjust_valence`: "happier", "sadder", or "same"
- `add_genres`: Array of genres to include more
- `remove_genres`: Array of genres to avoid

## Error Handling

### Common Errors

**Rate Limit Exceeded:**
```json
{
    "error": "rate_limit_exceeded",
    "message": "Daily playlist limit reached",
    "limits": {
        "daily_playlists": 3,
        "refinements_per_playlist": 3
    },
    "reset_time": "2024-01-02T00:00:00Z"
}
```

**Playlist Not Found:**
```json
{
    "error": "playlist_not_found",
    "message": "Playlist draft not found or access denied",
    "playlist_id": "uuid-playlist-id"
}
```

**Invalid Session:**
```json
{
    "error": "invalid_session",
    "message": "Session expired or invalid",
    "session_id": "invalid-session-id"
}
```

**AI Generation Failed:**
```json
{
    "error": "generation_failed",
    "message": "Failed to generate playlist due to AI service error",
    "details": "Temporary service unavailable"
}
```

**Insufficient Tracks:**
```json
{
    "error": "insufficient_tracks",
    "message": "Not enough tracks found matching criteria",
    "found_tracks": 5,
    "requested_tracks": 20,
    "suggestion": "Try broader search criteria or different genres"
}
```

## Best Practices

### Prompt Writing

**Good Prompts:**
- "Energetic rock songs for a road trip"
- "Chill indie music for studying"
- "90s hip-hop classics for a party"

**Avoid:**
- Too specific: "Songs that sound exactly like X by Y"
- Too broad: "Good music"
- Invalid requests: "Non-musical content"

### Refinement Strategy

1. **First refinement**: Remove unwanted tracks, adjust energy
2. **Second refinement**: Fine-tune genres and add specific requests
3. **Third refinement**: Final adjustments and reordering

### Performance Tips

- Use reasonable playlist lengths (10-30 tracks)
- Provide clear, specific prompts
- Use draft updates for simple changes instead of refinements
- Cache playlist data on client side

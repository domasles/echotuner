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
    "count": 20,
    "user_context": {
        "age_range": "25-34",
        "favorite_genres": ["pop", "electronic"],
        "favorite_artists": ["Artist Name"],
        "disliked_artists": ["Artist Name"]
    },
    "discovery_strategy": "balanced"
}
```

**Response:**
```json
{
    "songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id",
            "duration_ms": 210000,
            "popularity": 80,
            "genres": ["pop", "electronic"]
        }
    ],
    "generated_from": "upbeat pop songs for working out",
    "total_count": 20,
    "is_refinement": false,
    "playlist_id": "uuid-playlist-id"
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
    "prompt": "Add more energetic songs, remove slow ones",
    "current_songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id"
        }
    ],
    "count": 25,
    "discovery_strategy": "balanced"
}
```

**Response:**
```json
{
    "songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id",
            "duration_ms": 210000,
            "popularity": 80,
            "genres": ["pop", "electronic"]
        }
    ],
    "generated_from": "Add more energetic songs, remove slow ones",
    "total_count": 25,
    "is_refinement": true,
    "playlist_id": "uuid-playlist-id"
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
    "songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id"
        }
    ]
}
```

**Response:**
```json
{
    "songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id",
            "duration_ms": 210000,
            "popularity": 80,
            "genres": ["pop", "electronic"]
        }
    ],
    "generated_from": "Manual update",
    "total_count": 20,
    "is_refinement": false,
    "playlist_id": "uuid-playlist-id"
}
```

## Draft Management

### POST `/playlist/library`

Get user's library playlists including drafts and created Spotify playlists.

**Request Body:**
```json
{
    "session_id": "string",
    "device_id": "string"
}
```

**Response:**
```json
{
    "drafts": [
        {
            "id": "uuid-playlist-id",
            "device_id": "string",
            "session_id": "string",
            "prompt": "upbeat pop songs for working out",
            "songs": [
                {
                    "title": "Song Title",
                    "artist": "Artist Name",
                    "album": "Album Name",
                    "spotify_id": "spotify-track-id",
                    "duration_ms": 210000,
                    "popularity": 80,
                    "genres": ["pop", "electronic"]
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "refinements_used": 0,
            "status": "draft",
            "spotify_playlist_id": null
        }
    ],
    "spotify_playlists": [
        {
            "id": "spotify-playlist-id",
            "name": "My Workout Playlist",
            "description": "Created with EchoTuner",
            "tracks_count": 20,
            "refinements_used": 0,
            "max_refinements": 0,
            "can_refine": false,
            "spotify_url": "https://open.spotify.com/playlist/...",
            "images": [
                {
                    "url": "https://i.scdn.co/image/...",
                    "height": 640,
                    "width": 640
                }
            ]
        }
    ]
}
```

### POST `/playlist/drafts`

Get a specific draft playlist.

**Request Body:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "device_id": "string"
}
```

**Response:**
Returns a `PlaylistDraft` object:
```json
{
    "id": "uuid-playlist-id",
    "device_id": "string",
    "session_id": "string",
    "prompt": "upbeat pop songs for working out",
    "songs": [
        {
            "title": "Song Title",
            "artist": "Artist Name",
            "album": "Album Name",
            "spotify_id": "spotify-track-id",
            "duration_ms": 210000,
            "popularity": 80,
            "genres": ["pop", "electronic"]
        }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "refinements_used": 0,
    "status": "draft",
    "spotify_playlist_id": null
}
```

### DELETE `/playlist/drafts`

Delete a draft playlist.

**Request Body:**
```json
{
    "playlist_id": "uuid-playlist-id",
    "device_id": "string"
}
```

**Response:**
```json
{
    "message": "Draft playlist deleted successfully"
}
```

## Error Handling

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
    "detail": "Daily limit of 5 playlists reached. Try again tomorrow."
}
```

**Refinement Limit Exceeded:**
```json
{
    "detail": "Maximum of 3 AI refinements reached for this playlist."
}
```

**Playlist Not Found:**
```json
{
    "detail": "Draft playlist not found"
}
```

**Access Denied:**
```json
{
    "detail": "Access denied"
}
```

**Invalid Prompt:**
```json
{
    "detail": "The prompt doesn't seem to be related to music or mood. Please try a different description."
}
```

**Invalid Input:**
```json
{
    "detail": "Invalid input: string"
}
```

**Generation Failed:**
```json
{
    "detail": "Error generating playlist: sanitized_error_message"
}
```

**Authentication Required:**
```json
{
    "detail": "Authentication required"
}
```

**Invalid Device:**
```json
{
    "detail": "Invalid device ID. Please register device first."
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

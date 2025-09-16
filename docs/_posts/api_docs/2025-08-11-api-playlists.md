---
title: Playlist Generation API
date: 2025-08-11 13:30:00 +0000
categories: [API Documentation, Playlists]
tags: [api, playlists, generation, ai, music]
---

# Playlist Generation API

The Playlist API is the core of EchoTuner's functionality, providing AI-powered playlist generation and management. It supports both draft creation and direct Spotify playlist creation.

## Base Path: `/playlists`

## Endpoints

### Generate or Create Playlist

```http
POST /playlists?status={draft|spotify}
```

Generate a new AI playlist (draft) or create a Spotify playlist from an existing draft.

#### Query Parameters
- `status`: **Optional** - `draft` (default) or `spotify`

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID
- `X-Playlist-ID`: **Required for Spotify creation** - Draft playlist ID

#### Request Body (Draft Generation)

```json
{
  "prompt": "Energetic workout music with electronic beats",
  "discovery_strategy": "balanced",
  "user_context": {
    "context": {
      "favorite_artists": ["Daft Punk", "Justice"],
      "favorite_genres": ["electronic", "house"],
      "energy_preference": "high"
    }
  }
}
```

#### Request Body (Spotify Creation)

```json
{
  "name": "My Workout Playlist",
  "description": "AI-generated workout playlist",
  "public": false,
  "songs": [
    {
      "title": "One More Time",
      "artist": "Daft Punk",
      "spotify_id": "0DiWol3AO6WpXZgp0goxAV"
    }
  ]
}
```

#### Response (Draft Generation)

```json
{
  "songs": [
    {
      "title": "One More Time",
      "artist": "Daft Punk",
      "spotify_id": "0DiWol3AO6WpXZgp0goxAV",
      "preview_url": "https://p.scdn.co/mp3-preview/...",
      "external_urls": {
        "spotify": "https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV"
      }
    }
  ],
  "generated_from": "Energetic workout music with electronic beats",
  "total_count": 25,
  "playlist_id": "playlist_12345"
}
```

#### Response (Spotify Creation)

```json
{
  "spotify_playlist_id": "37i9dQZF1DX0XUsuxWHRQd",
  "playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd"
}
```

#### Example (Draft Generation)

```bash
curl -X POST "https://echotuner-api.domax.lt/playlists?status=draft" \
  -H "X-User-ID: user_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Chill lo-fi hip hop for studying",
    "discovery_strategy": "exploration"
  }'
```

#### Example (Spotify Creation)

```bash
curl -X POST "https://echotuner-api.domax.lt/playlists?status=spotify" \
  -H "X-User-ID: user_12345" \
  -H "X-Playlist-ID: playlist_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Study Vibes",
    "description": "Perfect lo-fi tracks for concentration",
    "public": false
  }'
```

---

### Update Playlist

```http
PUT /playlists
```

Update an existing draft playlist.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID
- `X-Playlist-ID`: **Required** - Playlist ID to update

#### Request Body

```json
{
  "prompt": "Updated prompt for playlist regeneration",
  "discovery_strategy": "conservative"
}
```

#### Response

Same format as draft generation response.

---

### Get User Playlists

```http
GET /playlists
```

Retrieve all playlists (drafts and Spotify) for the authenticated user.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "playlists": [
    {
      "id": "playlist_12345",
      "prompt": "Energetic workout music",
      "created_at": "2025-08-11T13:30:00Z",
      "songs_count": 25,
      "status": "draft",
      "spotify_playlist_id": null
    },
    {
      "id": "playlist_67890",
      "prompt": "Chill evening vibes",
      "created_at": "2025-08-10T20:15:00Z",
      "songs_count": 30,
      "status": "spotify",
      "spotify_playlist_id": "37i9dQZF1DX0XUsuxWHRQd",
      "spotify_url": "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd"
    }
  ],
  "total_count": 2
}
```

---

### Get Specific Playlist

```http
GET /playlists/{playlist_id}
```

Retrieve details of a specific playlist.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "id": "playlist_12345",
  "prompt": "Energetic workout music",
  "created_at": "2025-08-11T13:30:00Z",
  "songs": [
    {
      "title": "One More Time",
      "artist": "Daft Punk",
      "spotify_id": "0DiWol3AO6WpXZgp0goxAV",
      "preview_url": "https://p.scdn.co/mp3-preview/...",
      "external_urls": {
        "spotify": "https://open.spotify.com/track/0DiWol3AO6WpXZgp0goxAV"
      }
    }
  ],
  "songs_count": 25,
  "status": "draft"
}
```

---

### Delete Playlist

```http
DELETE /playlists/{playlist_id}
```

Delete a draft playlist (does not delete Spotify playlists).

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "message": "Playlist deleted successfully"
}
```

## Request Models

### PlaylistRequest (Draft Generation)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | ✅ | Description of desired playlist |
| `discovery_strategy` | string | ❌ | `balanced`, `exploration`, `conservative` |
| `user_context` | UserContext | ❌ | User preferences and context |

### SpotifyPlaylistRequest (Spotify Creation)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Playlist name |
| `description` | string | ❌ | Playlist description |
| `public` | boolean | ❌ | Make playlist public (default: false) |
| `songs` | array | ❌ | Song list (required in shared mode) |

### UserContext

| Field | Type | Description |
|-------|------|-------------|
| `context` | object | User preferences object |
| `context.favorite_artists` | array | List of favorite artists |
| `context.favorite_genres` | array | Preferred music genres |
| `context.energy_preference` | string | Energy level preference |
| `context.decade_preference` | array | Preferred decades |

## Discovery Strategies

### Balanced (Default)
- Mix of familiar and new music
- Moderate exploration of similar artists
- Safe recommendations with some variety

### Exploration
- Focus on discovering new music
- Less weight on user's known preferences
- Higher chance of unexpected recommendations

### Conservative
- Stick closely to user's known preferences
- Minimal exploration
- Safe, predictable recommendations

## Rate Limiting

Playlist generation is subject to rate limiting:

- **Daily Limit**: Configurable per user (default: varies by plan)
- **Rate Limit Status**: Check with `/user/rate-limit-status`
- **Limit Exceeded**: Returns 429 status code

## Error Handling

### Common Errors

#### 400 Bad Request - Invalid Prompt
```json
{
  "detail": "Invalid input: Prompt cannot be empty"
}
```

#### 404 Not Found - No Songs Generated
```json
{
  "detail": "No songs could be generated for your request. Please try a different prompt or check your preferences."
}
```

#### 429 Too Many Requests - Rate Limited
```json
{
  "detail": "Daily limit of 10 playlists reached. Try again tomorrow."
}
```

#### 503 Service Unavailable - Spotify Service Down
```json
{
  "detail": "Spotify playlist service not available"
}
```

## Best Practices

### Effective Prompts
- Be specific about mood, genre, or activity
- Include context like "for working out" or "for relaxation"
- Mention preferred energy level or tempo
- Include specific artists or songs as reference

### Good Examples
- "Upbeat pop songs for morning workout, similar to Dua Lipa"
- "Mellow acoustic guitar music for reading, indie folk style"
- "90s hip-hop classics with strong beats for driving"

### Poor Examples
- "Good music" (too vague)
- "Songs" (no context)
- "Music I like" (no specific criteria)

## Next Steps

- **[Spotify Integration API](/posts/api-spotify/)** - Create playlists directly on Spotify
- **[User Preferences API](/posts/api-personality/)** - Manage user music preferences
- **[Configuration API](/posts/api-config/)** - Get playlist generation limits and settings

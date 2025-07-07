# Personality Endpoints

These endpoints handle user personality preferences for AI-powered playlist generation.

## POST /personality/save

Save user personality preferences.

**Request Body:**
```json
{
  "session_id": "string",
  "device_id": "string",
  "personality": {
    "music_taste": {
      "preferred_genres": ["pop", "rock", "electronic"],
      "disliked_genres": ["country", "heavy metal"],
      "openness_to_new_music": 0.8,
      "mainstream_vs_underground": 0.3
    },
    "listening_habits": {
      "typical_listening_time": "evening",
      "preferred_playlist_length": 45,
      "skip_frequency": "rarely",
      "volume_preference": "moderate"
    },
    "mood_preferences": {
      "energy_level": 0.7,
      "emotional_tone": "positive",
      "preferred_activities": ["working", "relaxing", "exercising"]
    },
    "discovery_preferences": {
      "artist_diversity": 0.6,
      "temporal_range": "last_10_years",
      "language_preference": ["english", "spanish"],
      "instrumental_tolerance": 0.4
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Personality preferences saved successfully",
  "personality_id": "string"
}
```

## GET /personality/load

Load user personality preferences.

**Headers:**
- Requires device ID for session identification

**Response:**
```json
{
  "personality": {
    "music_taste": {
      "preferred_genres": ["pop", "rock", "electronic"],
      "disliked_genres": ["country", "heavy metal"],
      "openness_to_new_music": 0.8,
      "mainstream_vs_underground": 0.3
    },
    "listening_habits": {
      "typical_listening_time": "evening",
      "preferred_playlist_length": 45,
      "skip_frequency": "rarely",
      "volume_preference": "moderate"
    },
    "mood_preferences": {
      "energy_level": 0.7,
      "emotional_tone": "positive",
      "preferred_activities": ["working", "relaxing", "exercising"]
    },
    "discovery_preferences": {
      "artist_diversity": 0.6,
      "temporal_range": "last_10_years",
      "language_preference": ["english", "spanish"],
      "instrumental_tolerance": 0.4
    }
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## POST /personality/clear

Clear user personality preferences.

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
  "success": true,
  "message": "Personality preferences cleared successfully"
}
```

## Personality Schema

The personality object contains the following categories:

### Music Taste
- `preferred_genres`: Array of preferred music genres
- `disliked_genres`: Array of genres to avoid
- `openness_to_new_music`: Float 0-1 (0 = stick to familiar, 1 = very experimental)
- `mainstream_vs_underground`: Float 0-1 (0 = underground, 1 = mainstream)

### Listening Habits
- `typical_listening_time`: When the user usually listens to music
- `preferred_playlist_length`: Preferred playlist duration in minutes
- `skip_frequency`: How often the user skips songs ("never", "rarely", "sometimes", "often")
- `volume_preference`: Preferred volume level ("low", "moderate", "high")

### Mood Preferences
- `energy_level`: Float 0-1 (0 = calm/chill, 1 = high energy)
- `emotional_tone`: Overall emotional preference ("positive", "neutral", "melancholic", "varied")
- `preferred_activities`: Array of activities the music is for

### Discovery Preferences
- `artist_diversity`: Float 0-1 (0 = few artists, 1 = many different artists)
- `temporal_range`: Time period for music ("any", "last_year", "last_5_years", "last_10_years", "classic")
- `language_preference`: Array of preferred languages
- `instrumental_tolerance`: Float 0-1 (0 = only vocals, 1 = only instrumental)

## Error Responses

- `400 Bad Request`: Invalid personality data or request format
- `401 Unauthorized`: Invalid or expired session
- `404 Not Found`: No personality data found for user
- `500 Internal Server Error`: Server error

**Error Format:**
```json
{
  "detail": "string",
  "error": "string"
}
```

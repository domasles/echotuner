---
title: Personality & Preferences API
date: 2025-08-11 14:15:00 +0000
categories: [API Documentation, AI]
tags: [api, personality, preferences, music, ai]
---

# Personality & Preferences API

The Personality API manages user music preferences, personality data, and artist/genre preferences that help improve AI playlist generation. This data is used to personalize recommendations and enhance the quality of generated playlists.

## Base Path: `/personality`

## Endpoints

### Save User Personality

```http
PUT /personality
```

Save or update user's music personality and preferences.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Request Body

```json
{
  "context": {
    "favorite_artists": [
      "Daft Punk",
      "Justice",
      "Moderat",
      "Bonobo"
    ],
    "disliked_artists": [
      "Artist Name"
    ],
    "favorite_genres": [
      "electronic",
      "house",
      "ambient",
      "downtempo"
    ],
    "decade_preference": [
      "2000s",
      "2010s"
    ],
    "energy_preference": "medium",
    "valence_preference": "positive",
    "danceability_preference": "high",
    "mood_preferences": [
      "focus",
      "relaxation",
      "workout"
    ],
    "listening_contexts": [
      "work",
      "study",
      "exercise",
      "commute"
    ],
    "tempo_preference": "moderate",
    "instrumentalness_preference": "mixed",
    "acousticness_preference": "low"
  }
}
```

#### Response

```json
{
  "user_id": "user_12345",
  "personality_saved": true,
  "artists_count": 4,
  "genres_count": 4,
  "preferences_updated": "2025-08-11T14:15:00Z",
  "message": "Personality preferences saved successfully"
}
```

#### Example

```bash
curl -X PUT "https://api.echotuner.app/personality" \
  -H "X-User-ID: user_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "favorite_artists": ["Radiohead", "Thom Yorke"],
      "favorite_genres": ["alternative", "electronic"],
      "energy_preference": "medium"
    }
  }'
```

---

### Get User Personality

```http
GET /personality
```

Retrieve user's saved personality and preferences.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "user_id": "user_12345",
  "context": {
    "favorite_artists": [
      "Radiohead",
      "Thom Yorke",
      "Aphex Twin"
    ],
    "disliked_artists": [],
    "favorite_genres": [
      "alternative",
      "electronic",
      "experimental"
    ],
    "decade_preference": [
      "1990s",
      "2000s"
    ],
    "energy_preference": "medium",
    "valence_preference": "neutral",
    "mood_preferences": [
      "focus",
      "creativity"
    ]
  },
  "last_updated": "2025-08-11T14:15:00Z",
  "artists_count": 3,
  "genres_count": 3
}
```

---

### Search Artists

```http
POST /personality/artists/search
```

Search for artists to add to preferences.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Request Body

```json
{
  "query": "radiohead",
  "limit": 10
}
```

#### Response

```json
{
  "query": "radiohead",
  "artists": [
    {
      "name": "Radiohead",
      "spotify_id": "4Z8W4fKeB5YxbusRsdQVPb",
      "popularity": 85,
      "genres": [
        "alternative rock",
        "art rock",
        "melancholia",
        "oxford indie",
        "permanent wave",
        "rock"
      ],
      "images": [
        {
          "height": 640,
          "url": "https://i.scdn.co/image/ab6761610000e5eb...",
          "width": 640
        }
      ],
      "external_urls": {
        "spotify": "https://open.spotify.com/artist/4Z8W4fKeB5YxbusRsdQVPb"
      }
    }
  ],
  "total_results": 1
}
```

#### Example

```bash
curl -X POST "https://api.echotuner.app/personality/artists/search" \
  -H "X-User-ID: user_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "daft punk",
    "limit": 5
  }'
```

---

### Get Followed Artists (Spotify Integration)

```http
GET /personality/artists/followed
```

Get user's followed artists from Spotify (normal mode only).

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "followed_artists": [
    {
      "name": "Radiohead",
      "spotify_id": "4Z8W4fKeB5YxbusRsdQVPb",
      "genres": [
        "alternative rock",
        "art rock"
      ],
      "popularity": 85,
      "external_urls": {
        "spotify": "https://open.spotify.com/artist/4Z8W4fKeB5YxbusRsdQVPb"
      }
    }
  ],
  "total_count": 15,
  "message": "Retrieved followed artists from Spotify"
}
```

---

### Delete User Personality

```http
DELETE /personality
```

Delete all personality data for the user.

#### Headers
- `X-User-ID`: **Required** - Authenticated user ID

#### Response

```json
{
  "success": true,
  "message": "Personality data deleted successfully"
}
```

## Request Models

### UserContext

| Field | Type | Max Count | Description |
|-------|------|-----------|-------------|
| `favorite_artists` | array | 50 | Preferred artists |
| `disliked_artists` | array | 25 | Artists to avoid |
| `favorite_genres` | array | 20 | Preferred music genres |
| `decade_preference` | array | 10 | Preferred decades |
| `energy_preference` | string | - | Energy level: `low`, `medium`, `high` |
| `valence_preference` | string | - | Mood: `negative`, `neutral`, `positive` |
| `danceability_preference` | string | - | Danceability: `low`, `medium`, `high` |
| `mood_preferences` | array | 10 | Contextual moods |
| `listening_contexts` | array | 10 | When/where music is played |
| `tempo_preference` | string | - | Tempo: `slow`, `moderate`, `fast` |
| `instrumentalness_preference` | string | - | Vocals: `vocal`, `mixed`, `instrumental` |
| `acousticness_preference` | string | - | Production: `electronic`, `mixed`, `acoustic` |

### ArtistSearchRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | Artist search query |
| `limit` | integer | ❌ | Max results (default: 10, max: 50) |

## Personality Data Usage

### AI Playlist Generation

User personality data is automatically used in playlist generation to:

- **Artist Selection**: Favor/avoid artists based on preferences
- **Genre Filtering**: Include preferred genres, avoid disliked ones
- **Audio Features**: Match energy, valence, and other preferences
- **Contextual Recommendations**: Consider mood and listening context

### Recommendation Engine

The AI uses personality data to:

1. **Weight Preferences**: Higher weight for favorite artists/genres
2. **Apply Filters**: Exclude disliked content
3. **Feature Matching**: Match audio characteristics to preferences
4. **Contextual Adaptation**: Adjust recommendations based on mood/context

### Data Privacy

- **User Control**: Users can view, edit, and delete their data
- **Secure Storage**: Preferences stored securely and encrypted
- **No Sharing**: Data is never shared with third parties
- **Anonymization**: Analytics use anonymized data only

## Preference Guidelines

### Favorite Artists (Max: 50)
- Include artists you genuinely enjoy
- Add variety across different styles within your taste
- Update regularly as your taste evolves
- Consider both mainstream and niche artists

### Disliked Artists (Max: 25)
- Artists you strongly want to avoid
- Use sparingly - only for strong dislikes
- Consider if it's the artist or just specific songs

### Favorite Genres (Max: 20)
- Broad genres you enjoy
- Subgenres for more specific preferences
- Balance specificity with variety
- Update as you discover new genres

### Audio Preferences
- **Energy**: How energetic you like your music
- **Valence**: How positive/upbeat vs melancholic
- **Danceability**: How much you like rhythmic, danceable music
- **Acousticness**: Preference for acoustic vs electronic production

## Error Handling

### Common Errors

#### 400 Bad Request - Validation Error
```json
{
  "detail": "Invalid input: Too many favorite artists (maximum: 50)"
}
```

#### 404 Not Found - No Personality Data
```json
{
  "detail": "No personality data found for user"
}
```

#### 413 Payload Too Large
```json
{
  "detail": "Request payload too large"
}
```

### Validation Limits

The API enforces strict limits on personality data:

- **Favorite Artists**: 50 maximum
- **Disliked Artists**: 25 maximum  
- **Favorite Genres**: 20 maximum
- **Decade Preferences**: 10 maximum
- **String Fields**: Various length limits
- **Array Fields**: Count limits per type

## Integration Examples

### React Preferences Form

```javascript
import { useState, useEffect } from 'react';

const PersonalityForm = ({ userId }) => {
  const [preferences, setPreferences] = useState({
    favorite_artists: [],
    favorite_genres: [],
    energy_preference: 'medium'
  });

  // Load existing preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await fetch('/personality', {
          headers: { 'X-User-ID': userId }
        });
        
        if (response.ok) {
          const data = await response.json();
          setPreferences(data.context);
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
      }
    };

    loadPreferences();
  }, [userId]);

  // Save preferences
  const savePreferences = async () => {
    try {
      const response = await fetch('/personality', {
        method: 'PUT',
        headers: {
          'X-User-ID': userId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ context: preferences })
      });

      if (response.ok) {
        alert('Preferences saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); savePreferences(); }}>
      {/* Form fields for preferences */}
      <button type="submit">Save Preferences</button>
    </form>
  );
};
```

### Artist Search Component

```javascript
const ArtistSearch = ({ userId, onArtistSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const searchArtists = async () => {
    if (!query) return;

    try {
      const response = await fetch('/personality/artists/search', {
        method: 'POST',
        headers: {
          'X-User-ID': userId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query, limit: 10 })
      });

      const data = await response.json();
      setResults(data.artists);
    } catch (error) {
      console.error('Artist search failed:', error);
    }
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for artists..."
      />
      <button onClick={searchArtists}>Search</button>
      
      {results.map(artist => (
        <div key={artist.spotify_id} onClick={() => onArtistSelect(artist)}>
          <img src={artist.images[0]?.url} alt={artist.name} width="50" />
          <span>{artist.name}</span>
          <span>{artist.genres.join(', ')}</span>
        </div>
      ))}
    </div>
  );
};
```

## Next Steps

- **[Playlist Generation API](/posts/api-playlists/)** - Use personality data in playlist creation
- **[User Management API](/posts/api-users/)** - Manage user accounts and settings
- **[Spotify Integration API](/posts/api-spotify/)** - Connect with Spotify for followed artists

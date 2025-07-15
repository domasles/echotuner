# User Endpoints

These endpoints handle user-related operations like fetching followed artists and searching for artists.

## GET /personality/followed-artists

Get user's followed artists from Spotify.

**Parameters:**
- `limit` (query, optional): Number of artists to return (default: 50, max: 50)

**Headers:**
- `session_id`: Session ID for authentication
- `device_id`: Device ID for authentication

**Response:**
```json
{
    "artists": [
        {
            "id": "string",
            "name": "string",
            "genres": ["string"],
            "popularity": 75,
            "followers": {
                "total": 1000000
            },
            "images": [
                {
                    "url": "string",
                    "height": 640,
                    "width": 640
                }
            ],
            "external_urls": {
                "spotify": "string"
            }
        }
    ]
}
```

## POST /personality/search-artists

Search for artists on Spotify.

**Request Body:**
```json
{
  "session_id": "string",
  "device_id": "string",
  "query": "string",
  "limit": 20
}
```

**Response:**
```json
{
    "artists": [
        {
            "id": "string",
            "name": "string",
            "genres": ["string"],
            "popularity": 75,
            "followers": {
                "total": 1000000
            },
            "images": [
                {
                    "url": "string",
                    "height": 640,
                    "width": 640
                }
            ],
            "external_urls": {
                "spotify": "string"
            }
        }
    ]
}
```

## Error Responses

All user endpoints may return these error responses:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or expired session
- `500 Internal Server Error`: Failed to search artists or get followed artists

**Error Format:**
```json
{
    "detail": "string"
}
```

## Notes

- All user endpoints require valid Spotify authentication
- The `/personality/followed-artists` endpoint returns artists the user follows on Spotify
- The `/personality/search-artists` endpoint searches the Spotify catalog
- Results are paginated where applicable

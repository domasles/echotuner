# User Endpoints

These endpoints handle user-related operations like fetching followed artists and searching for artists.

## GET /user/followed-artists

Get user's followed artists from Spotify.

**Parameters:**
- `limit` (query, optional): Number of artists to return (default: 50, max: 50)

**Headers:**
- Requires valid session authentication via device ID

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
    ],
    "total": 25,
    "next": "string",
    "previous": null
}
```

## POST /user/search-artists

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
    ],
    "total": 100,
    "offset": 0,
    "limit": 20
}
```

## Error Responses

All user endpoints may return these error responses:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or expired session
- `403 Forbidden`: Insufficient Spotify permissions
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Error Format:**
```json
{
  "detail": "string",
  "error": "string"
}
```

## Notes

- All user endpoints require valid Spotify authentication
- The `/user/followed-artists` endpoint returns artists the user follows on Spotify
- The `/user/search-artists` endpoint searches the Spotify catalog
- Results are paginated where applicable

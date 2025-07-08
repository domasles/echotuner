# Authentication Endpoints

The authentication system handles Spotify OAuth flow, session management, and device registration.

## Overview

EchoTuner uses Spotify OAuth 2.0 for user authentication. The system supports both demo mode (shared account) and individual user accounts.

## Endpoints

### POST `/auth/init`

Initialize Spotify OAuth flow.

**Request Body:**
```json
{
    "device_id": "string",
    "device_info": {
        "platform": "string",
        "version": "string"
    }
}
```

**Response:**
```json
{
    "auth_url": "https://accounts.spotify.com/authorize?...",
    "state": "unique_state_token"
}
```

### GET `/auth/callback`

Handle Spotify OAuth callback (called by Spotify).

**Query Parameters:**
- `code`: Authorization code from Spotify
- `state`: State token from init request
- `error`: Error code if authorization failed

**Response:**
- Redirects to success/error page
- Sets session cookies

### POST `/auth/validate`

Validate an existing session.

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
    "valid": true,
    "user_id": "string",
    "account_type": "premium|free",
    "expires_at": "2024-01-01T00:00:00Z"
}
```

### GET `/auth/check-session`

Check if a session exists for polling.

**Query Parameters:**
- `device_id`: Device identifier

**Response:**
```json
{
    "session_exists": true,
    "session_id": "string"
}
```

### POST `/auth/rate-limit-status`

Get rate limit status for authenticated user.

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
    "playlists_remaining": 5,
    "refinements_remaining": 3,
    "reset_time": "2024-01-01T00:00:00Z"
}
```

### POST `/auth/register-device`

Register a new device with the system.

**Request Body:**
```json
{
    "device_info": {
        "platform": "iOS|Android",
        "version": "1.0.0-beta",
        "model": "iPhone 14"
    }
}
```

**Response:**
```json
{
    "device_id": "uuid-generated-device-id",
    "registered_at": "2024-01-01T00:00:00Z"
}
```

### POST `/auth/demo-playlist-refinements`

Get refinement count for demo playlists.

**Request Body:**
```json
{
    "playlist_id": "string",
    "device_id": "string"
}
```

**Response:**
```json
{
    "refinements_used": 2,
    "refinements_remaining": 1,
    "max_refinements": 3
}
```

### POST `/auth/logout`

Logout and clear all device data.

**Request Body:**
```json
{
    "device_id": "string",
    "session_id": "string"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

### GET `/auth/account_type/{session_id}`

Get account type for a session.

**Path Parameters:**
- `session_id`: Session identifier

**Response:**
```json
{
    "account_type": "premium|free",
    "features": ["playlist_creation", "high_quality_audio"]
}
```

## Debug Endpoints

### POST `/auth/cleanup` (debug only)

Clean up expired sessions and auth attempts.

**Response:**
```json
{
    "cleaned_sessions": 15,
    "cleaned_attempts": 8,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Authentication Flow

1. **Device Registration**: Register device with `/auth/register-device`
2. **OAuth Init**: Call `/auth/init` to get Spotify authorization URL
3. **User Authorization**: User authorizes app in browser
4. **Callback Handling**: Spotify calls `/auth/callback` with auth code
5. **Session Validation**: Use `/auth/validate` to check session status
6. **API Calls**: Include session_id in subsequent API requests

## Error Handling

### Common Error Codes

- `400`: Invalid request parameters
- `401`: Invalid or expired session
- `403`: Insufficient permissions or rate limit exceeded
- `429`: Rate limit exceeded
- `500`: Internal server error

### Example Error Response

```json
{
    "error": "invalid_session",
    "message": "Session has expired or is invalid",
    "code": 401
}
```

## Rate Limiting

Rate limits are applied per device/user:

- **Free accounts**: 3 playlists per day, 3 refinements per playlist
- **Premium accounts**: Higher limits or unlimited (configurable)
- **Demo mode**: Shared limits across all users

Limits reset daily at midnight UTC.

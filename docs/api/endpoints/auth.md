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
    "platform": "string"
}
```

**Response:**
```json
{
    "auth_url": "https://accounts.spotify.com/authorize?...",
    "state": "unique_state_token",
    "device_id": "string"
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
    "spotify_user_id": "string"
}
```

### GET `/auth/check-session`

Check if a session exists for polling.

**Headers:**
- `device_id`: Device identifier

**Response (success):**
```json
{
    "session_id": "string",
    "device_id": "string"
}
```

**Response (no session):**
```json
{
    "session_id": null
}
```

**Response (missing device_id):**
```json
{
    "message": "Device ID required in headers",
    "success": false
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
    "device_id": "string",
    "requests_made_today": 2,
    "max_requests_per_day": 5,
    "refinements_used": 1,
    "max_refinements": 3,
    "can_make_request": true,
    "can_refine": true,
    "reset_time": "2024-01-01T00:00:00Z",
    "playlist_limit_enabled": true,
    "refinement_limit_enabled": true
}
```

### POST `/auth/register-device`

Register a new device with the system.

**Request Body:**
```json
{
    "platform": "string",
    "app_version": "string",
    "device_fingerprint": "string"
}
```

**Response:**
```json
{
    "device_id": "uuid-generated-device-id",
    "registration_timestamp": 1704067200
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
    "playlist_id": "string",
    "refinements_used": 2,
    "max_refinements": 3,
    "can_refine": true
}
```

### POST `/auth/logout`

Logout and clear all device data.

**Headers:**
- `device_id`: Device identifier

**Response (success):**
```json
{
    "message": "Logged out successfully and cleared device data",
    "success": true
}
```

**Response (missing device_id):**
```json
{
    "message": "Device ID required for logout",
    "success": false
}
```

**Response (error):**
```json
{
    "message": "Logout failed",
    "success": false,
    "error": "string"
}
```

### POST `/auth/account-type`

Get account type for a session.

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
    "account_type": "normal"
}
```

## Debug Endpoints

### POST `/auth/cleanup` (debug only)

Clean up expired sessions and auth attempts.

**Response:**
```json
{
    "message": "Cleanup completed successfully"
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

- `400`: Invalid request parameters or missing required fields
- `401`: Invalid or expired session
- `403`: Insufficient permissions (e.g., demo account restrictions)
- `404`: Session not found
- `500`: Internal server error or service unavailable
- `503`: Service temporarily unavailable

### Example Error Response

```json
{
    "detail": "Invalid or expired session"
}
```

## Rate Limiting

Rate limits are applied per device/user:

- **Free accounts**: 3 playlists per day, 3 refinements per playlist
- **Premium accounts**: Higher limits or unlimited (configurable)
- **Demo mode**: Shared limits across all users

Limits reset daily at midnight UTC.

---
title: Authentication API
date: 2025-08-11 13:15:00 +0000
categories: [API Documentation, Authentication]
tags: [api, auth, oauth, spotify, google]
---

# Authentication API

The Authentication API provides OAuth 2.0 integration with Spotify and Google for secure user authentication. It supports both normal mode (individual Spotify accounts) and shared mode (single owner account with Google authentication).

## Base Path: `/auth`

## Endpoints

### Initialize Authentication Flow

```http
POST /auth/init
```

Initialize the authentication flow based on server mode and session UUID.

#### Headers
- `X-Session-UUID`: **Required** - Valid UUID for the session

#### Response
```json
{
  "auth_url": "https://accounts.spotify.com/authorize?...",
  "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "authenticate",
  "message": "Authentication URL generated"
}
```

#### Shared Mode Response (Owner Setup Required)
```json
{
  "auth_url": "https://api.echotuner.app/auth/setup",
  "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "setup_required",
  "message": "Owner setup required. An external browser window will open to complete the setup process."
}
```

#### Example
```bash
curl -X POST "https://api.echotuner.app/auth/init" \
  -H "X-Session-UUID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json"
```

---

### Setup Page (Shared Mode Only)

```http
GET /auth/setup
```

Provides owner setup page for shared mode. Redirects to Spotify OAuth for initial owner credential setup.

#### Response
- **Success**: Redirects to Spotify OAuth
- **Already Setup**: JSON response indicating setup is complete
- **Normal Mode**: 404 error

---

### Spotify OAuth Callback

```http
GET /auth/spotify/callback
```

Handles the OAuth callback from Spotify after user authorization.

#### Query Parameters
- `code`: **Required** - Authorization code from Spotify
- `state`: OAuth state parameter (contains session UUID for user auth)
- `error`: Error code if authorization failed

#### Response
- **Success**: HTML page confirming successful authentication
- **Error**: HTML error page with details

---

### Google OAuth Callback

```http
GET /auth/google/callback
```

Handles the OAuth callback from Google (shared mode only).

#### Query Parameters
- `code`: **Required** - Authorization code from Google
- `state`: OAuth state parameter
- `error`: Error code if authorization failed

#### Response
- **Success**: HTML page confirming successful authentication
- **Error**: HTML error page with details

---

### Check Authentication Status

```http
GET /auth/status
```

Poll the authentication status for a given session (used by mobile apps and web clients).

#### Headers
- `X-Session-UUID`: **Required** - Session UUID to check

#### Response
```json
{
  "status": "completed",
  "user_id": "user_12345"
}
```

or

```json
{
  "status": "pending"
}
```

#### Example
```bash
curl -X GET "https://api.echotuner.app/auth/status" \
  -H "X-Session-UUID: 550e8400-e29b-41d4-a716-446655440000"
```

## Authentication Flow

### Normal Mode Flow

1. **Initialize**: Call `/auth/init` with session UUID
2. **Authorize**: User visits returned auth URL (Spotify OAuth)
3. **Callback**: Spotify redirects to `/auth/spotify/callback`
4. **Poll Status**: App polls `/auth/status` until completion
5. **Complete**: Receive user ID for authenticated requests

### Shared Mode Flow

#### First Time Setup (Owner)
1. **Initialize**: Call `/auth/init` (returns setup URL)
2. **Setup**: Owner visits setup page
3. **Authorize**: Owner authorizes Spotify account
4. **Complete**: Owner credentials stored

#### User Authentication
1. **Initialize**: Call `/auth/init` with session UUID
2. **Authorize**: User visits Google OAuth URL
3. **Callback**: Google redirects to `/auth/google/callback`
4. **Poll Status**: App polls `/auth/status` until completion
5. **Complete**: Receive user ID for authenticated requests

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "detail": "X-Session-UUID header is required"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid session or expired authentication"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Authentication initialization failed"
}
```

## Security Considerations

- **Session UUIDs**: Must be valid UUID format
- **State Parameter**: Used to prevent CSRF attacks
- **Token Storage**: Access tokens are securely stored server-side
- **Rate Limiting**: Applied to prevent abuse

## Mobile Implementation

For mobile apps using the authentication flow:

```javascript
// 1. Generate session UUID
const sessionUuid = crypto.randomUUID();

// 2. Initialize auth
const response = await fetch('/auth/init', {
  method: 'POST',
  headers: {
    'X-Session-UUID': sessionUuid,
    'Content-Type': 'application/json'
  }
});

const { auth_url } = await response.json();

// 3. Open browser for auth
window.open(auth_url);

// 4. Poll for completion
const pollAuth = async () => {
  const statusResponse = await fetch('/auth/status', {
    headers: { 'X-Session-UUID': sessionUuid }
  });
  
  const { status, user_id } = await statusResponse.json();
  
  if (status === 'completed') {
    // Store user_id for future requests
    localStorage.setItem('user_id', user_id);
    return user_id;
  } else {
    // Continue polling
    setTimeout(pollAuth, 2000);
  }
};

pollAuth();
```

## Next Steps

- **[Playlist Generation API](/posts/api-playlists/)** - Generate playlists with your authenticated user
- **[User Profile API](/posts/api-users/)** - Manage user profiles and preferences

---
title: Authentication API
date: 2025-08-11 13:15:00 +0000
categories: [API Documentation, Authentication]
tags: [api, auth, oauth, spotify, google]
---

# Authentication API

The Authentication API provides OAuth 2.0 integration with Spotify and Google for secure user authentication. It supports both normal mode (individual Spotify accounts) and shared mode (single owner account with Google authentication).

Authentication is token-based. After completing the OAuth flow, clients receive an opaque **session token** which must be sent as `X-Auth-Token` on all subsequent authenticated requests.

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
  "auth_url": "https://echotuner-api.domax.lt/auth/setup",
  "session_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "action": "setup_required",
  "message": "Owner setup required. An external browser window will open to complete the setup process."
}
```

#### Example
```bash
curl -X POST "https://echotuner-api.domax.lt/auth/init" \
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

#### Response (completed)
```json
{
  "status": "completed",
  "session_token": "a3f9c2e1..."
}
```

#### Response (still waiting)
```json
{
  "status": "pending"
}
```

> **Important**: Store the `session_token` securely. It is required as `X-Auth-Token` on all subsequent API calls. The session UUID is no longer needed after this point.

#### Example
```bash
curl -X GET "https://echotuner-api.domax.lt/auth/status" \
  -H "X-Session-UUID: 550e8400-e29b-41d4-a716-446655440000"
```

---

### Logout

```http
POST /auth/logout
```

Invalidate the current session token server-side.

#### Headers
- `X-Auth-Token`: **Required** - The session token to revoke

#### Response
```json
{
  "message": "Logged out successfully"
}
```

#### Example
```bash
curl -X POST "https://echotuner-api.domax.lt/auth/logout" \
  -H "X-Auth-Token: a3f9c2e1..."
```

---

## Authentication Flow

### Normal Mode Flow

1. **Initialize**: `POST /auth/init` with session UUID -> receive `auth_url`
2. **Authorize**: User opens `auth_url` in browser (Spotify OAuth)
3. **Callback**: Spotify redirects to `/auth/spotify/callback`
4. **Poll Status**: App polls `GET /auth/status` every ~2 s until `status == "completed"`
5. **Store Token**: Save `session_token` from the completed response
6. **Authenticate**: Send `X-Auth-Token: <session_token>` on all subsequent requests

### Shared Mode Flow

#### First-Time Setup (Owner)
1. **Initialize**: `POST /auth/init` -> receives `action: "setup_required"`
2. **Setup**: Owner visits the setup URL in a browser
3. **Authorize**: Owner authorizes with their Spotify account
4. **Complete**: Owner credentials stored; server is ready for users

#### User Authentication
1. **Initialize**: `POST /auth/init` -> receive Google OAuth `auth_url`
2. **Authorize**: User opens `auth_url` (Google OAuth)
3. **Callback**: Google redirects to `/auth/google/callback`
4. **Poll Status**: App polls `GET /auth/status` until `status == "completed"`
5. **Store Token**: Save `session_token`
6. **Authenticate**: Send `X-Auth-Token: <session_token>` on all subsequent requests

---

## Using the Session Token

All endpoints that require authentication expect:

```http
X-Auth-Token: <session_token>
```

The server looks up the token in its database, resolves the user server-side, and authorizes the request. The internal user identity is never exposed to clients. Sending an invalid or expired token returns `401 Unauthorized`.

---

## Session Token Expiry

Session tokens expire after the configured `SESSION_TOKEN_EXPIRY_DAYS` period (default: 7 days). A token is invalidated only when it expires or is explicitly revoked (for example, every device that had the token logs out). When an expired token is used the server returns:

```json
{
  "detail": "Session token expired"
}
```

The client should re-authenticate by starting a fresh auth flow.

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
- **Token Storage**: The opaque session token is the only credential ever sent to clients
- **User Identity**: Internal user IDs are never exposed to clients
- **Rate Limiting**: Applied to prevent abuse

## Mobile Implementation

For mobile apps (Flutter, React Native, etc.):

```javascript
// 1. Generate session UUID
const sessionUuid = crypto.randomUUID();

// 2. Initialize auth
const initRes = await fetch('/auth/init', {
  method: 'POST',
  headers: { 'X-Session-UUID': sessionUuid }
});
const { auth_url } = await initRes.json();

// 3. Open browser for OAuth
window.open(auth_url);

// 4. Poll for completion
const pollAuth = async () => {
  const statusRes = await fetch('/auth/status', {
    headers: { 'X-Session-UUID': sessionUuid }
  });
  const { status, session_token } = await statusRes.json();

  if (status === 'completed') {
    // Persist the session token for all future requests
    localStorage.setItem('session_token', session_token);
    return session_token;
  }
  // Continue polling
  setTimeout(pollAuth, 2000);
};

await pollAuth();

// 5. Use token on subsequent requests
const playlist = await fetch('/playlists', {
  headers: { 'X-Auth-Token': localStorage.getItem('session_token') }
});
```

## Next Steps

- **[Playlist Generation API](/posts/api-playlists/)** - Generate playlists with your authenticated user
- **[User Profile API](/posts/api-users/)** - Manage user profiles and preferences

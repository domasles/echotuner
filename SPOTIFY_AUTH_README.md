# EchoTuner Spotify OAuth Implementation

This implementation adds a comprehensive Spotify OAuth authentication system to EchoTuner with session management and rate limiting.

## Features Implemented

### Backend (Python FastAPI)

1. **Spotify OAuth Integration**
   - Complete OAuth 2.0 flow with authorization code grant
   - Secure token management with refresh token support
   - User info retrieval from Spotify API

2. **Session Management**
   - UUID4-based session IDs for security
   - Platform-aware device identification
   - SQLite database for session storage
   - Automatic session expiration and cleanup

3. **Authentication Middleware**
   - Request validation for all protected endpoints
   - Session validation against device ID to prevent spoofing
   - Graceful error handling for invalid/expired sessions

4. **Enhanced API Endpoints**
   - `/auth/init` - Initialize OAuth flow
   - `/auth/callback` - Handle Spotify callback
   - `/auth/validate` - Validate existing sessions
   - Protected playlist generation endpoints

### Frontend (Flutter)

1. **Authentication Flow**
   - Beautiful login screen with Spotify branding
   - Platform-specific OAuth handling (WebView for mobile, popup for web)
   - Automatic session persistence and restoration

2. **Session Management**
   - Cross-platform session storage (SharedPreferences)
   - Automatic device ID generation and management
   - Session validation on app startup

3. **Auth-Protected UI**
   - AuthWrapper that shows login screen when not authenticated
   - Seamless transition to main app after authentication
   - Logout functionality in settings

4. **Platform Independence**
   - Works on web, iOS, Android, and desktop
   - Handles OAuth callbacks appropriately for each platform
   - Consistent UI across all platforms

## Security Features

1. **Session Security**
   - UUID4 session IDs prevent prediction
   - Device ID binding prevents session hijacking
   - Automatic session expiration
   - Secure storage of tokens

2. **Rate Limiting Integration**
   - Sessions tied to rate limiting system
   - Device-specific quotas
   - Prevents abuse through multiple accounts

3. **State Validation**
   - OAuth state parameter validation
   - CSRF protection in auth flow
   - Temporary state storage with expiration

## Database Schema

### `auth_sessions` table
- `session_id` (TEXT PRIMARY KEY) - UUID4 session identifier
- `device_id` (TEXT NOT NULL) - Unique device identifier  
- `platform` (TEXT NOT NULL) - Platform type (web, android, ios, etc.)
- `spotify_user_id` (TEXT) - Spotify user ID
- `access_token` (TEXT) - Spotify access token
- `refresh_token` (TEXT) - Spotify refresh token
- `expires_at` (INTEGER) - Token expiration timestamp
- `created_at` (INTEGER) - Session creation timestamp
- `last_used_at` (INTEGER) - Last activity timestamp

### `auth_states` table
- `state` (TEXT PRIMARY KEY) - OAuth state parameter
- `device_id` (TEXT NOT NULL) - Associated device
- `platform` (TEXT NOT NULL) - Platform type
- `created_at` (INTEGER) - State creation timestamp
- `expires_at` (INTEGER) - State expiration timestamp

## Configuration

### API Environment Variables
```bash
# Spotify OAuth
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback

# Authentication
AUTH_REQUIRED=true
SESSION_EXPIRE_HOURS=24
```

### Flutter Environment Variables
```bash
API_BASE_URL=http://localhost:8000
```

## User Flow

1. **First Visit**
   - User opens app
   - AuthWrapper detects no session
   - Login screen appears with Spotify branding
   - User clicks "Connect with Spotify"

2. **OAuth Flow**
   - App requests auth URL from API
   - API generates OAuth URL with state parameter
   - User redirected to Spotify authorization
   - User grants permissions
   - Spotify redirects back to API callback

3. **Session Creation**
   - API exchanges code for tokens
   - API creates session with UUID4 ID
   - API returns success page with session ID
   - App stores session ID locally
   - AuthWrapper detects authentication
   - User sees main app interface

4. **Subsequent Visits**
   - App validates stored session with API
   - If valid, user goes directly to main app
   - If invalid, user sees login screen again

5. **Logout**
   - User clicks logout in settings
   - App clears local session storage
   - API invalidates session in database
   - User returns to login screen

## API Request Flow

All playlist generation requests now require:
```json
{
  "prompt": "user prompt",
  "device_id": "device_identifier", 
  "session_id": "uuid4_session_id",
  "user_context": {...}
}
```

The API validates the session_id against the device_id before processing any requests.

## Error Handling

- **401 Unauthorized**: Invalid or missing session
- **403 Forbidden**: Session/device mismatch (anti-spoofing)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side auth issues

## Testing the Implementation

1. Start the API: `python main.py`
2. Start the Flutter app: `flutter run`
3. Test login flow with real Spotify credentials
4. Verify session persistence across app restarts
5. Test logout and re-login functionality
6. Verify rate limiting works with authenticated sessions

This implementation provides a robust, secure, and user-friendly authentication system that meets all the specified requirements while maintaining the app's beautiful design and cross-platform compatibility.

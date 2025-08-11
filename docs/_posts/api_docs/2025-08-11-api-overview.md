---
title: API Overview
date: 2025-08-11 13:00:00 +0000
categories: [API Documentation, Overview]
tags: [api, overview, endpoints, rest]
pin: true
---

# EchoTuner API Documentation

The EchoTuner API is a comprehensive REST API that powers both the web and mobile applications. It provides endpoints for authentication, playlist generation, Spotify integration, user management, and AI-powered music recommendations.

## Base URL

```
https://api.echotuner.app
```

## Authentication

The API uses OAuth 2.0 for authentication with support for both Spotify and Google providers. All authenticated endpoints require either:

- **X-User-ID** header with a valid user identifier
- **X-Session-UUID** header for session-based authentication

## API Categories

### 🔐 Authentication (`/auth`)
Handle user authentication and OAuth flows
- OAuth initialization and callbacks
- Session management
- Multi-provider support (Spotify, Google)

### 🎵 Playlists (`/playlists`)
Core playlist functionality
- AI-powered playlist generation
- Draft management
- Spotify playlist creation

### 🎧 Spotify Integration (`/spotify`)
Direct Spotify API integration
- Create playlists on Spotify
- Manage existing playlists
- Track operations

### 👤 User Management (`/user`)
User profile and account management
- Profile information
- Rate limiting status
- Account settings

### 🧠 Personality & Preferences (`/personality`)
User music preferences and personality data
- Save/retrieve music preferences
- Artist search and management
- Genre preferences

### 🤖 AI Services (`/ai`)
AI model information and testing
- Available models
- Model testing (debug only)

### ⚙️ Configuration (`/config`)
Application configuration and health
- Health checks
- Client configuration
- Feature flags

### 🖥️ Server Information (`/server`)
Server mode and status
- Server mode detection
- System information

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Playlist Generation**: Maximum playlists per day (configurable)
- **User Requests**: Rate limited per user ID
- **Global Limits**: Overall API rate limiting

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

Error responses include:

```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional error information"
}
```

## Common Headers

### Required Headers
- `Content-Type: application/json`
- `X-User-ID: {user_id}` (for authenticated endpoints)

### Optional Headers
- `X-Session-UUID: {session_uuid}` (for session-based auth)
- `X-Playlist-ID: {playlist_id}` (for playlist operations)

## Server Modes

EchoTuner supports two operational modes:

### Normal Mode
- Individual user Spotify authentication
- Personal playlists and preferences
- Full OAuth flow per user

### Shared Mode
- Single owner Spotify account
- Google OAuth for user authentication
- Shared playlist creation capabilities

## Getting Started

1. **[Authentication Guide](/posts/api-authentication/)** - Set up OAuth and get access tokens
2. **[Playlist Generation](/posts/api-playlists/)** - Generate AI-powered playlists
3. **[Spotify Integration](/posts/api-spotify/)** - Create playlists on Spotify
4. **[User Management](/posts/api-users/)** - Manage user profiles and preferences

## API Status

Check the API health and status:

```bash
curl https://api.echotuner.app/config/health
```

For detailed endpoint documentation, explore the specific API category guides linked above.

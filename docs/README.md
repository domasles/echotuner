# EchoTuner Documentation

Welcome to the EchoTuner documentation! EchoTuner is an AI-powered playlist generation system that creates personalized music playlists using real-time song search and mood analysis.

## Documentation Structure

### Quick Start Guides
- [API Quick Start](api/quick-start.md) - Get the API running locally or with Docker
- [App Quick Start](app/quick-start.md) - Build and run the Flutter app

### API Documentation
- [Authentication Endpoints](api/endpoints/auth.md) - User authentication and session management
- [Config Endpoints](api/endpoints/config.md) - Configuration and health endpoints
- [Playlist Endpoints](api/endpoints/playlist.md) - Playlist generation and management
- [Spotify Endpoints](api/endpoints/spotify.md) - Spotify integration endpoints
- [User Endpoints](api/endpoints/user.md) - User data and artist search
- [Personality Endpoints](api/endpoints/personality.md) - User personality preferences
- [AI Endpoints](api/endpoints/ai.md) - AI model management
- [Server Endpoints](api/endpoints/server.md) - Server status and mode information

### API Customization
- [Custom AI Providers](api/customization/ai-providers.md) - Add your own AI providers
- [Environment Configuration](api/customization/environment.md) - Configure .env settings
- [Security & Rate Limiting](api/customization/security.md) - Customize security features

### App Documentation
- [App Customization](app/customization.md) - Themes, widgets, and UI customization
- [App Deployment](app/deployment.md) - Build and deploy for different platforms

## Getting Started

1. **For API Developers**: Start with the [API Quick Start](api/quick-start.md) to get the backend running
2. **For app Developers**: Check the [App Quick Start](app/quick-start.md) to build the Flutter app
3. **For Customization**: Explore the customization guides for both API and app components

## System Architecture

EchoTuner consists of two main components:

- **API (Python/FastAPI)**: Backend service handling AI playlist generation, Spotify integration, and user management
- **App (Flutter/Dart)**: Cross-platform mobile app for iOS and Android

The system supports multiple AI providers (Ollama, OpenAI, Google) and can be deployed with Docker for easy setup.

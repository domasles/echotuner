# EchoTuner API

The EchoTuner API is a production-ready RESTful service that generates personalized music playlists using artificial intelligence and real-time Spotify integration.

## What It Does

EchoTuner transforms natural language prompts into curated music playlists. Describe your mood, activity, or music preferences in plain language, and the API uses AI to understand your intent and creates a playlist by searching Spotify's catalog in real-time.

## Key Capabilities

- **AI-Powered Understanding**: Processes natural language to understand musical intent and mood
- **Multiple AI Providers**: Support for local Ollama models, OpenAI, Google AI, and custom endpoints
- **Real-Time Music Search**: Live integration with Spotify's catalog for current, relevant songs
- **User Personality Learning**: Adapts to user preferences over time for personalized recommendations
- **Production Ready**: Comprehensive error handling, rate limiting, and security features
- **Session Management**: Secure OAuth2 authentication with automatic cleanup

## Documentation

For setup, configuration, deployment, and API reference, see the complete documentation:

**[API Documentation](../docs/api/)**

- [Quick Start Guide](../docs/api/quick-start.md) - Get the API running in minutes
- [Environment Configuration](../docs/api/customization/environment.md) - Configure AI providers and settings
- [API Endpoints](../docs/api/endpoints/) - Complete endpoint reference
- [Custom AI Providers](../docs/api/customization/ai-providers.md) - Add your own AI providers
- [Security & Rate Limiting](../docs/api/customization/security.md) - Production security features

## Architecture

EchoTuner API is built with:

- **Python 3.8+** with FastAPI for high-performance async web framework
- **SQLite** for lightweight data storage and session management
- **aiohttp** for asynchronous HTTP client operations
- **Multiple AI provider support** with auto-discovery and fallback systems
- **Spotify Web API** for real-time music search and playlist creation
- **Docker support** for easy deployment and scaling

---
title: Welcome to EchoTuner Documentation
date: 2025-08-11 10:00:00 +0000
tags: [introduction, overview, getting-started]
pin: true
---

# Welcome to EchoTuner

EchoTuner is an AI-powered music discovery platform that creates personalized playlists based on natural language prompts. Using advanced machine learning and the Spotify Web API, EchoTuner transforms your musical ideas into carefully curated playlists.

## What is EchoTuner?

EchoTuner combines artificial intelligence with music streaming to create a unique playlist generation experience. Simply describe the mood, activity, or vibe you're looking for, and our AI will generate a personalized playlist that matches your request.

### Key Features

- **AI-Powered Generation**: Describe your ideal playlist in natural language
- **Spotify Integration**: Seamless connection with your Spotify account
- **Personalized Experience**: Learn from your music taste and preferences
- **Multiple Auth Modes**: Flexible authentication for different use cases
- **Cross-Platform**: Available as web app and mobile application
- **Privacy-Focused**: Your data stays secure with multiple privacy options

## How It Works

1. **Connect**: Authenticate with Spotify or use Google login with shared Spotify
2. **Describe**: Tell us what kind of music you want in natural language
3. **Generate**: Our AI analyzes your request and creates a custom playlist
4. **Enjoy**: Listen, save, and share your personalized playlists

### Example Prompts

- *"Upbeat indie rock for a morning workout"*
- *"Chill electronic music for studying"*
- *"90s alternative rock for nostalgia"*
- *"Jazz standards for a dinner party"*
- *"High-energy pop for a road trip"*

## Architecture Overview

EchoTuner consists of three main components:

### API Server (FastAPI)
- **REST API**: RESTful endpoints for all functionality
- **Authentication**: Multiple OAuth providers (Spotify, Google)
- **AI Integration**: Natural language processing for playlist generation
- **Database**: User preferences, history, and playlist data
- **Rate Limiting**: Built-in protection and usage management

### Mobile App (Flutter)
- **Cross-Platform**: iOS and Android support
- **Intuitive UI**: Simple and clean interface for playlist generation
- **Offline Support**: Cache playlists for offline viewing
- **Real-time Sync**: Live updates with the API server

### Web App (Flutter Web)
- **Browser-Based**: No installation required
- **Responsive Design**: Works on desktop and mobile browsers
- **PWA Support**: Progressive Web App capabilities
- **Full Feature Set**: Complete functionality in the browser

## Getting Started

### For Users
- **[Web App Access](https://echotuner.domax.lt)**: Use EchoTuner in your browser

### For Developers
- **[API Documentation](/categories/api-documentation/)**: Complete API reference
- **[Authentication Guide](/posts/api-authentication/)**: OAuth implementation

## API Documentation

Comprehensive documentation for developers and integrators:

- **[Authentication](/posts/api-authentication/)** - OAuth flows and security
- **[Playlist Generation](/posts/api-playlists/)** - Core playlist creation endpoints
- **[Spotify Integration](/posts/api-spotify/)** - Spotify Web API integration
- **[User Management](/posts/api-users/)** - User profiles and preferences
- **[AI Services](/posts/api-personality/)** - AI and personality features
- **[Server Configuration](/posts/api-config/)** - Server setup and management

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLite/PostgreSQL**: Database for user data and preferences
- **OpenAI/Anthropic**: AI services for natural language processing
- **Spotify Web API**: Music data and playlist creation
- **Docker**: Containerized deployment

### Frontend
- **Flutter**: Cross-platform mobile and web development
- **Material Design**: Consistent and modern UI components
- **Dart**: Programming language for Flutter applications

### Infrastructure
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Reverse proxy and static file serving
- **Redis**: Caching and session management (optional)
- **GitHub Actions**: CI/CD and automated deployments

## Authentication Modes

EchoTuner supports multiple authentication modes to fit different use cases:

### 1. Spotify OAuth
- Full access to personal Spotify account
- Create playlists directly in your Spotify library
- Access to your saved music and preferences
- Highest rate limits and full feature access

### 2. Google + Shared Spotify (Recommended)
- Google authentication for user accounts
- Shared Spotify account for playlist creation
- Good for organizations or shared environments
- Moderate rate limits with full generation features

## Privacy and Security

- **Data Minimization**: We only collect necessary data for functionality
- **Secure Storage**: All sensitive data is encrypted and securely stored
- **User Control**: You control what data is shared and with whom
- **Transparency**: Clear privacy policy and data usage information
- **GDPR Compliant**: Full compliance with European privacy regulations

## Community and Support

- **GitHub Repository**: [github.com/domasles/echotuner](https://github.com/domasles/echotuner)
- **Issue Tracking**: Report bugs and request features on GitHub
- **Discussions**: Community discussions and support
- **Documentation**: This comprehensive documentation site

## Roadmap

### Future Plans
- **Additional Streaming Services**: Apple Music, YouTube Music support
- **Desktop Applications**: Native desktop apps for Windows, macOS, Linux
- **Machine Learning**: Improved AI models for better recommendations

## License

EchoTuner is open-source software licensed under the MIT License. See the [LICENSE](https://github.com/domasles/echotuner/blob/main/LICENSE) file for details.

---

Ready to start generating amazing playlists? Check out our [API Documentation](/categories/api-documentation/) or use the web app to get started!

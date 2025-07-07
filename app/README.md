# EchoTuner App

The EchoTuner application is a cross-platform Flutter app that provides an intuitive interface for AI-powered playlist generation and music discovery.

## What It Does

EchoTuner lets you create personalized playlists by simply describing what you want to hear. The app connects to the EchoTuner API to process your natural language requests and generates playlists tailored to your mood, activity, or musical preferences using real-time Spotify integration.

## Key Features

- **Natural Language Interface**: Describe your music preferences in plain language
- **Cross-Platform**: Single codebase runs on Android, iOS, Web, and Desktop
- **Real-Time Spotify Integration**: Direct playlist creation and synchronization with your Spotify account
- **User Personality Learning**: Adapts to your music taste over time for better recommendations
- **Library Management**: Track your draft playlists and created playlists
- **Demo Mode Support**: Works in both demo and authenticated modes
- **Smart Rate Limiting**: Visual indicators for usage quotas and limits
- **Secure Authentication**: Complete Spotify OAuth2 integration with session management

## Documentation

For setup, development, customization, and deployment instructions, see the complete documentation:

**[App Documentation](../docs/app/)**

- [Quick Start Guide](../docs/app/quick-start.md) - Get the app running in minutes
- [Customization Guide](../docs/app/customization.md) - Themes, widgets, and UI customization
- [Deployment Guide](../docs/app/deployment.md) - Build and deploy for different platforms

## Architecture

EchoTuner App is built with:

- **Flutter 3.0+** for cross-platform development
- **Dart** programming language
- **Provider pattern** for state management
- **HTTP client** for API communication with session management
- **Shared preferences** for local storage and demo mode support
- **Material Design 3** for modern UI components
- **WebView integration** for cross-platform OAuth authentication

## App Structure

- **Authentication System**: Complete OAuth2 flow with platform-specific handling
- **Session Management**: Automatic session persistence and restoration across app launches
- **Personality Service**: User preference learning with local/cloud sync based on account type
- **Rate Limiting Interface**: Visual progress indicators for usage quotas
- **Demo Mode Support**: Automatic detection and adaptation to demo backend configurations
- **Cross-Platform Navigation**: Consistent UI across mobile, web, and desktop platforms

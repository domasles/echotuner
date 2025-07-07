![EchoTuner Logo](./EchoTunerLogo.svg)

# EchoTuner - AI-Powered Playlist Generation Platform

EchoTuner transforms natural language descriptions into personalized music playlists using artificial intelligence and real-time Spotify integration. Describe your mood, activity, or music preferences in plain language, and EchoTuner creates the perfect playlist for you.

## What Makes EchoTuner Different

**Built for Developers, By Developers**: Unlike centralized music services, EchoTuner runs entirely on your infrastructure. This means no rate limits, no data collection, and complete control over your music discovery experience.

**Real AI Understanding**: Uses advanced language models to understand complex musical requests like "upbeat indie rock for a rainy morning" or "nostalgic 90s hits for a road trip."

**Live Music Discovery**: Searches Spotify's current catalog in real-time, ensuring you get fresh, relevant songs rather than static playlists.

## Platform Components

- **🔧 API Backend** - Production-ready FastAPI service with modular AI provider support
- **📱 Flutter App** - Cross-platform mobile and desktop application  
- **🤖 AI System** - Support for local Ollama models, OpenAI, Google AI, and custom providers
- **🎵 Spotify Integration** - Real-time search, playlist creation, and user preference learning

## Documentation

Complete setup and usage documentation is available in the `docs/` directory:

📖 **[Documentation Hub](docs/README.md)**

- **[API Documentation](docs/api/)** - Backend setup, configuration, and API reference
- **[App Documentation](docs/app/)** - Flutter app development and deployment  
- **[Quick Start Guides](docs/README.md)** - Get running in minutes

## Quick Setup

**Docker (Recommended):**
```bash
git clone https://github.com/your-repo/echotuner.git
cd echotuner
docker-compose up -d
```

**Manual Setup:**
```bash
# API Backend
cd api && cp .env.sample .env  # Add your Spotify credentials
python main.py

# Flutter App  
cd app && cp .env.sample .env  # Configure API endpoint
flutter run
```

For detailed setup instructions, see the [Getting Started guide](docs/README.md).

## Project Philosophy

EchoTuner embraces the "run it yourself" philosophy. Instead of fighting Spotify's restrictive API quotas and review processes, we lean into local deployment. This approach gives you:

- **No Rate Limits** - Your Spotify developer credentials, your rules
- **Complete Privacy** - Your music data never leaves your infrastructure
- **Full Control** - Customize, modify, and extend however you want
- **No Dependencies** - No external services that can disappear or change terms

This isn't just a music app—it's a template for building personal-scale software that you own completely.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# EchoTuner App Quick Start

This guide will help you get the EchoTuner Flutter app up and running quickly.

## Prerequisites

- **Flutter SDK**: Version 3.0 or higher
- **Dart SDK**: Version 3.0 or higher  
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)
- **VS Code** with Flutter extension (recommended)
- **Docker** (optional, for deployment)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd echotuner/app
```

### 2. Copy Necessary Files
```bash
cp .env.example .env  # Copy environment configuration
cp AndroidManifest.xml.sample android/app/src/profile/AndroidManifest.xml  # Copy Android manifest
```

### 3. Create Project Files
```bash
flutter create .
```

### 4. Install Dependencies
```bash
flutter pub get
```

### 5. Build JSON Serializers
```bash
dart run build_runner build --delete-conflicting-outputs
```

### 6. Generate Icons
```bash
dart run flutter_launcher_icons
```

### 7. Run the App

#### Development Mode
```bash
flutter run
```

#### Specific Platform
```bash
# Android
flutter run -d android

# iOS  
flutter run -d ios

# Web
flutter run -d chrome

# Desktop
flutter run -d windows # or macos, linux
```

## Docker Deployment
Docker deployment is the recommended approach for production environments to ensure consistent builds and easy deployment.
For that you'll need to have Docker and Docker Compose installed.
After you've set up the app and the API, you can build and run it using Docker:

```bash
docker compose up --build
```

## Key Features

### AI-Powered Playlist Generation
- Generate playlists using natural language prompts
- Personalized recommendations based on music taste
- Real-time Spotify song search integration

### Spotify Authentication
- Secure OAuth flow
- Session management
- Device registration

### Modern UI
- Material Design 3
- Dark/Light theme support
- Responsive design for all screen sizes

### Cross-Platform
- Android, iOS, Web, and Desktop support
- Native performance
- Platform-specific optimizations

## Configuration

### API Configuration
Located in `lib/config/api_config.dart`:
- `baseUrl`: Your EchoTuner API server URL
- `debugMode`: Enable/disable debug features
- `timeoutDuration`: API request timeout

### App Configuration  
Located in `lib/config/app_config.dart`:
- App name and version
- Feature flags
- Default settings

### Theme Configuration
Located in `lib/config/theme_config.dart`:
- Color schemes
- Typography
- Component themes

## Development Tips

### Hot Reload
Flutter's hot reload allows instant code changes:
- Press `r` in the terminal to hot reload
- Press `R` for hot restart
- Press `h` for help

### Debugging
- Use `debugPrint()` for logging
- Flutter Inspector for widget debugging
- Network traffic monitoring in debug mode

### Testing
```bash
# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Integration tests
flutter drive --target=test_driver/app.dart
```

## Building for Production

### Android APK
```bash
flutter build apk --release
```

### Android App Bundle
```bash
flutter build appbundle --release
```

### iOS App
```bash
flutter build ios --release
```

### Web
```bash
flutter build web --release
```

### Desktop
```bash
# Windows
flutter build windows --release

# macOS  
flutter build macos --release

# Linux
flutter build linux --release
```

## Troubleshooting

### Common Issues

#### Dependency Issues
```bash
flutter clean
flutter pub get
```

#### Build Issues
```bash
flutter doctor
flutter doctor --android-licenses  # Android only
```

#### API Connection Issues
- Verify API server is running
- Check network connectivity
- Validate API configuration

### Getting Help

- Check [Flutter documentation](https://docs.flutter.dev/)
- Review API documentation in `docs/api/`
- Check GitHub issues for known problems

## Next Steps

- Read the [Customization Guide](customization.md)
- Explore [Deployment Options](deployment.md)
- Review [API Integration](api-integration.md)

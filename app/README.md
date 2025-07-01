![EchoTuner Logo](../EchoTunerLogo.svg)

# EchoTuner App - AI-Powered Music Discovery Application

The EchoTuner application provides a user-friendly interface for AI-powered playlist generation and music discovery. Built with Flutter, it offers cross-platform compatibility and seamless integration with the EchoTuner API backend for intelligent music recommendations.

**Current Version: 1.6.0-alpha+1**

## Overview

The EchoTuner app delivers an intuitive experience for creating personalized playlists through natural language prompts. Users can describe their mood, preferences, or activities, and the app leverages AI-powered backend services to generate tailored music recommendations with support for multiple AI providers.

**Key Features:**
- **Natural Language Interface**: Describe your music preferences in plain language
- **AI-Powered Recommendations**: Intelligent playlist generation with flexible AI model support
- **Cross-Platform Compatibility**: Built with Flutter for Android, iOS, Desktop and Web
- **User Personality System**: Comprehensive preference learning and personalized recommendations
- **Real-Time Music Discovery**: Live integration with Spotify streaming service
- **Spotify Integration**: Direct playlist creation and synchronization
- **Library Management**: Track drafts and created playlists with silent refresh system
- **Song Management**: Add, remove, and reorder songs with Spotify sync
- **Smart Limit Indicators**: Visual rate limiting with floating progress bars

## Prerequisites

### Flutter Installation

**Important**: Flutter must be cloned from its GitHub repository as the latest release to ensure compatibility with required packages and features.

1. **Clone Flutter from GitHub:**
   ```bash
   git clone https://github.com/flutter/flutter.git
   ```

   **Windows Installation Location Warning:**
   
   Consider creating a directory at `%USERPROFILE%` (C:\Users\{username}) or `%LOCALAPPDATA%` (C:\Users\{username}\AppData\Local).
   
   **Warning:** don't install Flutter to a directory or path that meets one or both of the following conditions:
   - The path contains special characters or spaces.
   - The path requires elevated privileges.
   
   As an example, `C:\Program Files` meets both conditions.

2. **Add Flutter to your PATH**
    - **Windows**: Add `[PATH_TO_FLUTTER_INSTALLATION_DIRECTORY]\bin` to your system PATH environment variable.
    - **macOS/Linux**: Add `export PATH="$PATH:[PATH_TO_FLUTTER_INSTALLATION_DIRECTORY]/bin"` to your shell configuration file (e.g., `.bashrc`, `.zshrc`).

3. **Verify Flutter installation:**
   ```bash
   flutter doctor
   ```
   After running this command, ensure all checks are resolved.

### Additional Requirements

- **Android Studio** (for Android development)
- **VS Code** or **Android Studio** Flutter plugins
- **Xcode** (for iOS development, macOS only)
- **Visual Studio** (for Windows development, Windows only) 
- **Running EchoTuner API**: The backend service must be operational

Opening your IDE with the Flutter plugin make sure you locate the Flutter SDK path correctly.
For complete Flutter installation instructions and required dependencies for building on Linux, visit the [official Flutter documentation](https://docs.flutter.dev/get-started/install).

**Warning:** installing Flutter SDK from VSCode extensions or other package managers may lead to compatibility issues with required packages and features. It's recommended to clone Flutter from its official GitHub repository.

## Installation

### Quick Setup

1. **Navigate to the app directory:**
   ```bash
   cd echotuner/app
   ```

2. **Copy over .env.sample to .env:**
   ```bash
   cp .env.sample .env
   ```
   Don't forget to Configure Spotify API credentials in the generated `.env` file

3. **Generate flutter project files:**
   ```bash
   flutter create .
   ```

4. **Generate model files:**
   ```bash
   dart run flutter_launcher_icons build_runner build
   ```

5. **Run the app:**
   ```bash
   flutter run
   ```
   You'll be greeted with the device selection screen, where you can choose to run the app on an emulator or a connected device. After selecting a device, the app will start, and you can begin testing its features.

### Backend Service Setup

The EchoTuner app requires the API backend to be running. For complete backend installation instructions, see the [API installation guide](../api/README.md).

## Running the Application

### Development Mode

1. **Start an emulator or connect a physical device:**
   ```bash
   # List available devices
   flutter devices
   
   # Start Android emulator
   flutter emulators --launch <emulator_id>
   ```

2. **Run the application:**
   ```bash
   flutter run
   ```

3. **Hot reload during development:**
   - Press `r` in the terminal for hot reload
   - Press `R` for hot restart
   - Press `q` to quit

## Development Setup

### Code Generation

The app uses code generation for models and serialization:

```bash
# Generate model files
flutter packages pub run build_runner build

# Watch for changes and auto-generate
flutter packages pub run build_runner watch
```

### Testing

```bash
# Run unit tests
flutter test

# Run integration tests
flutter test integration_test/
```

## Dependencies

Key Flutter packages used in the project:

- **HTTP Client**: For API communication
- **State Management**: Provider for state management
- **Navigation**: Flutter's built-in navigation system
- **JSON Serialization**: For API data handling with json_annotation
- **URL Launcher**: For opening Spotify links
- **Build Runner**: For code generation

For complete dependency list, see `pubspec.yaml`.

## Build and Release

### Debug Build

```bash
# Android
flutter build apk --debug

# iOS
flutter build ios --debug
```

### Release Build

```bash
# Android
flutter build apk --release

# iOS
flutter build ios --release
```

## Integration with EchoTuner API

The app integrates with the EchoTuner API for authentication and playlist generation:

1. **Authentication Flow**: Spotify OAuth via API endpoints
2. **Session Management**: Secure session validation with device binding
3. **API Communication**: Authenticated requests with session IDs
4. **Result Processing**: Display generated playlists with auth context
5. **Error Handling**: Graceful handling of auth failures and session expiration

For API documentation and integration details, refer to the [API documentation](../api/README.md).

## Troubleshooting

### Common Issues

**Flutter Doctor Issues:**
```bash
flutter doctor -v
```

**Dependencies:**
```bash
# Install dependencies
dart pub get

# Generate JSON serialization code (required after model changes)
dart run build_runner build --delete-conflicting-outputs
```

**Package Resolution:**
```bash
dart clean
dart pub get
```

**Build Issues:**
```bash
dart clean
dart pub get
dart run build_runner build --delete-conflicting-outputs
```

**Authentication Issues:**
- Verify backend API is running with auth enabled
- Check Spotify OAuth credentials in API configuration
- Ensure proper redirect URI setup in Spotify Developer Dashboard
- Test OAuth flow in different browsers/platforms
- Clear app storage and retry authentication

**API Connection Issues:**
- Verify backend service is running
- Check network connectivity and firewall settings
- Ensure API endpoints are correctly configured

### Platform-Specific Issues

**Android:**
- Verify Android SDK and build tools installation
- Check minimum SDK version compatibility
- Ensure device/emulator API level compatibility

**iOS:**
- Verify Xcode installation and command line tools
- Check iOS deployment target compatibility
- Ensure proper provisioning profiles for device testing

## Support

For comprehensive support and additional resources:

- **Flutter Issues**: Check the [Flutter GitHub repository](https://github.com/flutter/flutter/issues)
- **EchoTuner Issues**: Use project GitHub Issues for app-specific problems
- **API Integration**: Refer to [API documentation](../api/README.md)
- **General Setup**: See [master documentation](../README.md)
- **Flutter Documentation**: [Official Flutter docs](https://docs.flutter.dev/)

For development guidelines and contribution information, refer to the project root documentation.

## Features

### Authentication System

The app includes a comprehensive Spotify OAuth authentication system:

- **Spotify OAuth Integration**: Secure OAuth 2.0 flow with beautiful UI
- **Cross-Platform Support**: Works on web, mobile, and desktop platforms  
- **Session Management**: Automatic session persistence and restoration
- **AuthWrapper**: Seamless transition between login and main app
- **Platform-Specific Handling**: WebView for mobile, popup for web platforms
- **Secure Storage**: Device-specific session storage with automatic cleanup

**User Flow:**
1. **First Visit**: Login screen with Spotify branding
2. **OAuth Flow**: Platform-appropriate authentication handling
3. **Session Creation**: Automatic session storage and validation
4. **Subsequent Visits**: Direct access to main app with session validation
5. **Logout**: Clean session removal and return to login screen

### Rate Limiting Interface

The app includes smart rate limiting visualization:

- **Floating Indicators**: Pill-shaped progress bars show current usage
- **Conditional Visibility**: Indicators only appear when backend limits are enabled
- **Real-Time Updates**: Usage statistics update after each playlist/refinement action
- **Visual Feedback**: Color-coded progress (green → orange → red) based on usage
- **Smart Positioning**: Indicators float next to UI elements without overlap

**Home Screen**: Shows daily playlist limit status
**Playlist Screen**: Shows refinement usage for current playlist

# EchoTuner App - AI-Powered Music Discovery Application

The EchoTuner application provides a user-friendly interface for AI-powered playlist generation and music discovery. Built with Flutter, it offers cross-platform compatibility and seamless integration with the EchoTuner API backend for intelligent music recommendations.

## Overview

The EchoTuner app delivers an intuitive app experience for creating personalized playlists through natural language prompts. Users can describe their mood, preferences, or activities, and the app leverages AI-powered backend services to generate tailored music recommendations.

**Key Features:**
- **Natural Language Interface**: Describe your music preferences in plain language
- **AI-Powered Recommendations**: Intelligent playlist generation through backend API integration
- **Cross-Platform Compatibility**: Built with Flutter for Android, iOS, Desktop and Web
- **Real-Time Music Discovery**: Live integration with music streaming services
- **Personalized Experience**: Adaptive recommendations based on user preferences

**Current Status**: In active development - coming soon for direct music discovery

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

### Additional Requirements

- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)
- **VS Code** or **Android Studio** with Flutter plugins
- **Running EchoTuner API**: The backend service must be operational

For complete Flutter installation instructions, visit the [official Flutter documentation](https://docs.flutter.dev/get-started/install).

**Warning:** installing Flutter SDK from VSCode extensions or other package managers may lead to compatibility issues with required packages and features. It's recommended to clone Flutter from its official GitHub repository.

## Installation

### Quick Setup

1. **Navigate to the app directory:**
   ```bash
   cd echotuner/app
   ```

2. **Install Flutter dependencies:**
   ```bash
   flutter pub get
   ```

3. **Generate model files:**
   ```bash
   flutter packages pub run build_runner build
   ```

4. **Verify device connectivity:**
   ```bash
   flutter devices
   ```

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

## Configuration

### API Endpoint Configuration

Configure the backend API endpoint in the app's configuration files:

```dart
// lib/config/api_config.dart
class ApiConfig {
  static const String baseUrl = 'http://localhost:8000';
  static const String apiVersion = 'v1';
}
```

### Platform-Specific Configuration

**Android**: Configuration in `android/app/src/main/AndroidManifest.xml`
**iOS**: Configuration in `ios/Runner/Info.plist`

## Project Structure

```
app/
├── lib/
│   ├── main.dart              # Application entry point
│   ├── config/                # Configuration files
│   ├── models/                # Data models
│   ├── providers/             # State management
│   ├── screens/               # UI screens
│   └── services/              # API services
├── android/                   # Android-specific configuration
├── ios/                       # iOS-specific configuration
├── web/                       # Web platform files
└── pubspec.yaml               # Dependencies and metadata
```

## Dependencies

Key Flutter packages used in the project:

- **HTTP Client**: For API communication
- **State Management**: Provider or Bloc for state management
- **Navigation**: Flutter's built-in navigation system
- **JSON Serialization**: For API data handling

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

The app integrates with the EchoTuner API for playlist generation:

1. **User Input**: Natural language music preferences
2. **API Communication**: Secure requests to backend service
3. **Result Processing**: Display generated playlists
4. **Music Integration**: Connect with streaming services

For API documentation and integration details, refer to the [API documentation](../api/README.md).

## Troubleshooting

### Common Issues

**Flutter Doctor Issues:**
```bash
flutter doctor -v
```

**Package Resolution:**
```bash
flutter clean
flutter pub get
```

**Build Issues:**
```bash
flutter clean
flutter pub get
flutter packages pub run build_runner build --delete-conflicting-outputs
```

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

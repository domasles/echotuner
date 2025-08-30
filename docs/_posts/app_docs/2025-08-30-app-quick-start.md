---
title: EchoTuner App Quick Start
date: 2025-08-30 14:00:00 +0000
categories: [Flutter, Web, Mobile, Deployment]
tags: [flutter, quick-start, setup, docker, web, mobile]
---

# EchoTuner App Quick Start

This guide provides step-by-step instructions to get the **EchoTuner Flutter app** running locally or in a Docker environment.

## Prerequisites

- **Flutter SDK**: Version 3.0 or higher  
- **Dart SDK**: Version 3.0 or higher  
- **Android Studio** (for Android development)  
- **Xcode** (macOS only, for iOS development)  
- **VS Code** with Flutter extension (recommended)  
- **Docker** (optional, for deployment)  

---

## Local Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd echotuner/app
```

### 2. Create Flutter Project Files

```bash
flutter create .
```

### 3. Copy Sample Files

```bash
cp samples/.env.sample .env
cp samples/AndroidManifest.xml android/app/src/profile/AndroidManifest.xml
cp samples/index.html web/index.html
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

---

## Running the App

**Development Mode**

```bash
flutter run
```

**Platform-Specific**

```bash
# Android
flutter run -d android

# iOS
flutter run -d ios

# Web
flutter run -d chrome

# Desktop
flutter run -d windows   # or macos, linux
```

> **Note**: Include the `.env` file in your `pubspec.yaml` assets section if you want environment variables to be loaded in local Flutter builds.

---

## Docker Deployment

EchoTuner provides two deployment approaches:

### Option 1: Pre-built Images (Recommended)

Uses pre-built images from GitHub Container Registry. Ensure `.env` files are present in:

- `app/`  
- `api/`  

Database files will be mounted at `api/storage`.

```bash
docker compose up
```

> Use `-d` flag to run in detached mode.

### Option 2: Local Build

```bash
docker compose up --build
```

> This builds containers locally; otherwise, Docker Compose uses pre-built GHCR images.

---

## Key Features

- **AI-Powered Playlist Generation**  
  Generate playlists using natural language prompts, personalized recommendations, and real-time Spotify search.

- **Spotify Authentication**  
  Secure OAuth flow, session management, and device registration.

- **Modern UI**  
  Material 3 design, responsive layout, dark/light themes.

- **Cross-Platform**  
  Android, iOS, Web, and Desktop support with native performance.

---

## Development Tips

- **Hot Reload**: Press `r` in terminal  
- **Hot Restart**: Press `R`  
- **Logging**: Use `AppLogger.debug()`  
- **Debugging**: Flutter Inspector and network monitoring  

---

## Building for Production

```bash
# Android APK
flutter build apk --release

# Android App Bundle
flutter build appbundle --release

# iOS
flutter build ios --release

# Web
flutter build web --release

# Desktop
flutter build windows --release
flutter build macos --release
flutter build linux --release
```

---

## Troubleshooting

### Dependencies

```bash
flutter clean
flutter pub get
```

### Build Issues

```bash
flutter doctor
flutter doctor --android-licenses
```

### API Connection

- Ensure API server is running  
- Verify network connectivity  
- Check API configuration  

---

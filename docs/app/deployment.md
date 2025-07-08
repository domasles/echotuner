# EchoTuner App Deployment

This guide covers deploying the EchoTuner Flutter app to various platforms.

## Prerequisites

- Completed app development and testing
- Valid developer accounts for target platforms
- Proper API server deployment and configuration
- Code signing certificates (iOS/macOS)

## Android Deployment

### 1. Prepare for Release

#### Configure `android/app/build.gradle`:

```gradle
android {
    compileSdkVersion 34
    
    defaultConfig {
        applicationId "com.yourcompany.echotuner"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "1.0.0"
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### Configure signing in `android/key.properties`:

```properties
storePassword=your_store_password
keyPassword=your_key_password
keyAlias=your_key_alias
storeFile=../keys/release.keystore
```

### 2. Generate Keystore

```bash
keytool -genkey -v -keystore android/keys/release.keystore -keyalg RSA -keysize 2048 -validity 10000 -alias release
```

### 3. Build Release APK

```bash
flutter build apk --release
```

### 4. Build App Bundle (Recommended)

```bash
flutter build appbundle --release
```

### 5. Upload to Google Play Console

1. Create app in [Google Play Console](https://play.google.com/console)
2. Upload App Bundle (`.aab` file)
3. Complete store listing
4. Submit for review

## iOS Deployment

### 1. Configure iOS Settings

#### Update `ios/Runner/Info.plist`:

```xml
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>EchoTuner</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.echotuner</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <!-- Add required permissions -->
    <key>NSMicrophoneUsageDescription</key>
    <string>This app needs microphone access for music recognition features.</string>
</dict>
</plist>
```

### 2. Configure Xcode Project

1. Open `ios/Runner.xcworkspace` in Xcode
2. Select signing team
3. Configure app identifier
4. Set deployment target (iOS 12.0+)

### 3. Build for Release

```bash
flutter build ios --release
```

### 4. Archive and Upload

1. In Xcode: Product → Archive
2. Upload to App Store Connect
3. Complete app metadata
4. Submit for App Store review

## Web Deployment

### 1. Build Web Release

```bash
flutter build web --release
```

### 2. Configure Web Settings

#### Update `web/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <base href="/">
    <meta charset="UTF-8">
    <meta name="description" content="AI-powered playlist generation">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="EchoTuner">
    <link rel="apple-touch-icon" href="icons/Icon-192.png">
    <title>EchoTuner</title>
    <link rel="manifest" href="manifest.json">
</head>
<body>
    <script src="flutter.js" defer></script>
    <script>
        window.addEventListener('load', function(ev) {
            _flutter.loader.loadEntrypoint({
                serviceWorker: {
                    serviceWorkerVersion: serviceWorkerVersion,
                },
            }).then(function(engineInitializer) {
                return engineInitializer.initializeEngine();
            }).then(function(appRunner) {
                return appRunner.runApp();
            });
        });
    </script>
</body>
</html>
```

### 3. Deploy to Hosting

#### Firebase Hosting

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy
```

#### Netlify

1. Connect GitHub repository
2. Set build command: `flutter build web`
3. Set publish directory: `build/web`
4. Deploy

#### Vercel

```bash
npm install -g vercel
vercel --prod
```

## Desktop Deployment

### Windows

#### 1. Build Windows Release

```bash
flutter build windows --release
```

#### 2. Create Installer (Optional)

Use NSIS or Inno Setup to create installer:

```nsis
; example.nsi
!define APP_NAME "EchoTuner"
!define APP_VERSION "1.0.0"

Name "${APP_NAME}"
OutFile "${APP_NAME}-${APP_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"

Section "Install"
    SetOutPath $INSTDIR
    File /r "build\windows\runner\Release\*"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\echotuner.exe"
SectionEnd
```

### macOS

#### 1. Build macOS Release

```bash
flutter build macos --release
```

#### 2. Code Signing

```bash
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" build/macos/Build/Products/Release/EchoTuner.app
```

#### 3. Create DMG

```bash
hdiutil create -volname "EchoTuner" -srcfolder build/macos/Build/Products/Release/EchoTuner.app -ov -format UDZO EchoTuner.dmg
```

### Linux

#### 1. Build Linux Release

```bash
flutter build linux --release
```

#### 2. Create AppImage (Optional)

Use `linuxdeploy` to create portable AppImage:

```bash
linuxdeploy --appdir build/linux/x64/release/bundle --create-desktop-file --icon-file assets/icon.png --executable build/linux/x64/release/bundle/echotuner --appimage
```

## Environment Configuration

### Build Flavors

#### Configure flavors in `android/app/build.gradle`:

```gradle
android {
    flavorDimensions "version"
    productFlavors {
        development {
            dimension "version"
            applicationIdSuffix ".dev"
            versionNameSuffix "-dev"
        }
        staging {
            dimension "version"
            applicationIdSuffix ".staging"
            versionNameSuffix "-staging"
        }
        production {
            dimension "version"
        }
    }
}
```

#### Build specific flavors:

```bash
flutter build apk --flavor development
flutter build apk --flavor staging
flutter build apk --flavor production
```

## Performance Optimization

### Build Optimization

#### `pubspec.yaml`:

```yaml
flutter:
    uses-material-design: true

    # Only include needed assets
    assets:
        - assets/icons/
        - assets/logos/logo.png

    # Tree-shake unused icons
    fonts:
        - family: Roboto
            fonts:
                - asset: fonts/Roboto-Regular.ttf
                - asset: fonts/Roboto-Bold.ttf

                weight: 700
```

#### Build flags:

```bash
# Optimize for size
flutter build apk --release --tree-shake-icons --split-debug-info=debug-info

# Optimize for performance  
flutter build apk --release --dart-define=flutter.inspector.structuredErrors=false
```

## Security Considerations

### API Keys and Secrets

1. **Never commit secrets to version control**
2. Use environment variables or secure build parameters
3. Implement certificate pinning for API calls
4. Obfuscate sensitive code

#### Code obfuscation:

```bash
flutter build apk --release --obfuscate --split-debug-info=debug-info
```

### App Security

- Enable ProGuard/R8 for Android
- Implement root/jailbreak detection
- Use secure storage for sensitive data
- Validate all user inputs

## Monitoring and Analytics

### Crash Reporting

#### Configure Firebase Crashlytics:

```dart
// main.dart
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

void main() async {
    WidgetsFlutterBinding.ensureInitialized();

    if (!kDebugMode) {
        FirebaseCrashlytics.instance.setCrashlyticsCollectionEnabled(true);
        FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError;
    }

    runApp(MyApp());
}
```

### Performance Monitoring

```dart
// Track custom metrics
FirebasePerformance.instance
    .newTrace('playlist_generation')
    .start();
```

## Troubleshooting

### Common Build Issues

#### Android signing errors:
```bash
# Check keystore
keytool -list -v -keystore android/keys/release.keystore

# Clean and rebuild
flutter clean
flutter pub get
flutter build apk --release
```

#### iOS provisioning issues:
- Verify certificates in Xcode
- Check bundle identifier matches provisioning profile
- Ensure all devices are registered

#### Web deployment issues:
- Check CORS settings on API server
- Verify base href in index.html
- Test with `flutter run -d chrome --web-renderer html`

## Next Steps

- Set up monitoring and alerting
- Plan app store optimization (ASO)
- Implement user feedback collection
- Schedule regular security audits

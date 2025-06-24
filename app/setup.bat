@echo off

REM EchoTuner Flutter App Setup Script for Windows

echo Setting up EchoTuner Flutter App...

REM Check if Flutter is installed
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Flutter is not installed. Please install Flutter first:
    echo https://docs.flutter.dev/get-started/install
    pause
    exit /b 1
)

echo Flutter found

REM Get Flutter dependencies
echo Getting Flutter dependencies...
flutter pub get

REM Generate model files
echo Generating model files...
flutter packages pub run build_runner build

echo Flutter app setup complete!
echo.
echo Next steps:
echo 1. Make sure you have an Android emulator or iOS simulator running
echo 2. Or connect a physical device
echo 3. Run the app with: flutter run
echo 4. Make sure the API server is running on localhost:8000
echo.
pause

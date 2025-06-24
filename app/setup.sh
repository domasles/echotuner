#!/bin/bash

# EchoTuner Flutter App Setup Script

echo "Setting up EchoTuner Flutter App..."

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "Flutter is not installed. Please install Flutter first:"
    echo "https://docs.flutter.dev/get-started/install"
    exit 1
fi

echo "Flutter found"

# Get Flutter dependencies
echo "Getting Flutter dependencies..."
flutter pub get

# Generate model files
echo "Generating model files..."
flutter packages pub run build_runner build

echo "Flutter app setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure you have an Android emulator or iOS simulator running"
echo "2. Or connect a physical device"
echo "3. Run the app with: flutter run"
echo "4. Make sure the API server is running on localhost:8000"
echo ""

class AppConstants {
    static const String appName = 'EchoTuner';
    static const String appVersion = '1.4.0-alpha+1';
    static const String appDescription = 'AI-powered Spotify playlist generator';

    static const String defaultApiHost = 'localhost';
    static const int defaultApiPort = 8000;

    static const int authPollingMaxAttempts = 150;
    static const Duration authPollingInterval = Duration(seconds: 2);
    static const Duration authStateExpiry = Duration(minutes: 10);

    static const Duration messageDisplayDuration = Duration(seconds: 2);
    static const Duration quickPromptDelay = Duration(milliseconds: 500);

    static const double bottomNavigationHeight = 80.0;
    static const double fabBottomMargin = 16.0;
    static const double messageBottomMargin = 16.0;

    static const double progressBarHeight = 4.0;

    // Border Radius Constants
    static const double smallRadius = 8.0;
    static const double mediumRadius = 12.0;
    static const double largeRadius = 16.0;
    static const double extraLargeRadius = 20.0;
    static const double pillRadius = 24.0;
    static const double circularRadius = 28.0;

    // Button Specific Radius
    static const double buttonRadius = 24.0;
    static const double chipRadius = 20.0;
    static const double cardRadius = 16.0;
    static const double inputRadius = 16.0;
    static const double dialogRadius = 20.0;
    static const double messageRadius = 16.0;

    // Spacing Constants
    static const double smallSpacing = 8.0;
    static const double mediumSpacing = 16.0;
    static const double largeSpacing = 24.0;
    static const double extraLargeSpacing = 32.0;

    // Padding Constants
    static const double smallPadding = 8.0;
    static const double mediumPadding = 16.0;
    static const double largePadding = 24.0;
    static const double extraLargePadding = 32.0;

    // Icon Sizes
    static const double smallIconSize = 16.0;
    static const double mediumIconSize = 24.0;
    static const double largeIconSize = 32.0;
    static const double extraLargeIconSize = 48.0;

    // Animation Durations
    static const Duration fastAnimation = Duration(milliseconds: 150);
    static const Duration normalAnimation = Duration(milliseconds: 300);
    static const Duration slowAnimation = Duration(milliseconds: 500);

    // Personality Question Types
    static const int maxFavoriteArtists = 12;
    static const int maxDislikedArtists = 20;
    static const int maxFavoriteGenres = 10;

    static const List<String> clientGeneratedPrefixes = [
        'android_',
        'ios_',
        'web_',
        'unknown_',
    ];

    static const String featureComingSoon = 'Feature coming soon!';
    static const String genericErrorMessage = 'An unexpected error occurred. Please try again.';
    static const String networkErrorMessage = 'Network error. Please check your connection.';
    static const String authTimeoutMessage = 'Authentication timed out. Please try again.';
    static const String authFailedMessage = 'Authentication failed or timed out.';

    static const String authSuccessMessage = 'Successfully connected to Spotify';
    static const String logoutSuccessMessage = 'Successfully logged out';
}

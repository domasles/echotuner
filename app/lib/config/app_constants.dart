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
    static const int maxRefinementsDefault = 3;
    static const int maxPlaylistsDefault = 3;

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

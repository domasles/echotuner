class AppConstants {
    static const String appName = 'EchoTuner';
    static const String appVersion = '1.5.0-alpha';
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
    static const double messageBottomMargin = 90.0;
    static const double progressBarHeight = 4.0;
    static const double appBarHeight = 56.0;
    static const double tabBarHeight = 48.0;

    static const double tinyRadius = 2.0;
    static const double smallRadius = 8.0;
    static const double mediumRadius = 12.0;
    static const double largeRadius = 16.0;
    static const double extraLargeRadius = 20.0;
    static const double pillRadius = 24.0;
    static const double circularRadius = 28.0;

    static const double buttonRadius = 24.0;
    static const double chipRadius = 20.0;
    static const double cardRadius = 16.0;
    static const double inputRadius = 16.0;
    static const double dialogRadius = 20.0;
    static const double dialogWidth = 400.0;
    static const double messageRadius = 16.0;
    static const double snackbarRadius = 16.0;
    static const double modalRadius = 20.0;
    static const double avatarRadius = 20.0;

    static const double tinySpacing = 4.0;
    static const double smallSpacing = 8.0;
    static const double mediumSpacing = 16.0;
    static const double largeSpacing = 24.0;
    static const double extraLargeSpacing = 32.0;
    static const double massiveSpacing = 48.0;

    static const double tinyIconSize = 16.0;
    static const double smallIconSize = 20.0;
    static const double mediumIconSize = 24.0;
    static const double largeIconSize = 32.0;
    static const double extraLargeIconSize = 48.0;
    static const double massiveIconSize = 64.0;

    static const double tinyPadding = 4.0;
    static const double smallPadding = 8.0;
    static const double smallMediumPadding = 12.0;
    static const double mediumPadding = 16.0;
    static const double largePadding = 24.0;
    static const double extraLargePadding = 32.0;

    static const double screenPaddingMobile = 16.0;
    static const double screenPaddingTablet = 24.0;
    static const double screenPaddingDesktop = 32.0;

    static const double tinyFontSize = 10.0;
    static const double smallFontSize = 12.0;
    static const double mediumFontSize = 14.0;
    static const double largeFontSize = 16.0;
    static const double extraLargeFontSize = 18.0;
    static const double titleFontSize = 20.0;
    static const double headingFontSize = 24.0;
    static const double displayFontSize = 32.0;

    static const double buttonHeight = 48.0;
    static const double inputHeight = 48.0;
    static const double listItemHeight = 56.0;
    static const double chipHeight = 32.0;
    static const double toolbarHeight = 56.0;

    static const double messageHorizontalPadding = 12.0;
    static const double messageVerticalPadding = 8.0;
    static const double messageLeftRightMargin = 20.0;
    static const double messageBottomPosition = 90.0;
    static const double messageFontSize = 14.0;
    static const double messageBorderWidth = 1.0;

    static const Duration fastAnimation = Duration(milliseconds: 150);
    static const Duration normalAnimation = Duration(milliseconds: 300);
    static const Duration slowAnimation = Duration(milliseconds: 500);

    static const int maxFavoriteArtists = 12;
    static const int maxDislikedArtists = 20;
    static const int maxFavoriteGenres = 10;

    static const double mobileBreakpoint = 600.0;
    static const double tabletBreakpoint = 1024.0;
    static const double desktopBreakpoint = 1440.0;

    static const int mobileGridColumns = 2;
    static const int tabletGridColumns = 3;
    static const int desktopGridColumns = 4;
    static const double gridSpacing = 16.0;
    static const double cardElevation = 2.0;

    static const double maxContentWidth = 1200.0;
    static const double dialogWidthMobile = 0.9;
    static const double dialogWidthTablet = 0.7;
    static const double dialogWidthDesktop = 0.5;

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

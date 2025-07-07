# EchoTuner App Customization

This guide covers how to customize the EchoTuner Flutter app for your needs.

## Theme Customization

### Color Schemes

Edit `lib/config/theme_config.dart` to customize colors:

```dart
class ThemeConfig {
    static ColorScheme lightColorScheme = ColorScheme.fromSeed(
        seedColor: Colors.deepPurple,  // Change primary color
        brightness: Brightness.light,
    );

    static ColorScheme darkColorScheme = ColorScheme.fromSeed(
        seedColor: Colors.deepPurple,  // Change primary color
        brightness: Brightness.dark,
    );
}
```

### Custom Color Palette
```dart
class AppColors {
    // Primary colors
    static const Color primary = Color(0xFF6B73FF);
    static const Color primaryVariant = Color(0xFF3F4FFF);

    // Secondary colors
    static const Color secondary = Color(0xFF03DAC6);
    static const Color secondaryVariant = Color(0xFF018786);

    // Surface colors
    static const Color surface = Color(0xFF121212);
    static const Color background = Color(0xFF000000);

    // Text colors
    static const Color onPrimary = Color(0xFFFFFFFF);
    static const Color onSurface = Color(0xFFFFFFFF);
}
```

### Typography

Customize fonts in `lib/config/theme_config.dart`:

```dart
class ThemeConfig {
    static TextTheme textTheme = const TextTheme(
        displayLarge: TextStyle(
        fontFamily: 'Roboto',
        fontSize: 57,
        fontWeight: FontWeight.w400,
        ),

        headlineLarge: TextStyle(
            fontFamily: 'Roboto',
            fontSize: 32,
            fontWeight: FontWeight.w600,
        ),
        // Add more text styles...
    );
}
```

## App Configuration

### Feature Flags

Enable/disable features in `lib/config/app_config.dart`:

```dart
class AppConfig {
    // Feature flags
    static const bool enablePersonalityFeatures = true;
    static const bool enableOfflineMode = false;
    static const bool enableAnalytics = true;
    static const bool enablePushNotifications = false;

    // Playlist settings
    static const int maxPlaylistLength = 100;
    static const int defaultPlaylistLength = 25;
    static const int maxRefinements = 5;

    // UI settings
    static const bool showDebugInfo = false;
    static const bool enableHapticFeedback = true;
}
```

## Custom Widgets

### Creating Reusable Components

Create custom widgets in `lib/widgets/custom/`:

```dart
// lib/widgets/custom/custom_button.dart
class CustomButton extends StatelessWidget {
    final String text;
    final VoidCallback? onPressed;
    final ButtonStyle? style;
    final Widget? icon;

    const CustomButton({
        Key? key,
        required this.text,
        this.onPressed,
        this.style,
        this.icon,
    }) : super(key: key);

    @override
    Widget build(BuildContext context) {
        return ElevatedButton(
            onPressed: onPressed,
            style: style ?? _defaultStyle(context),

            child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                    if (icon != null) ...[
                        icon!,
                        const SizedBox(width: 8),
                    ],

                    Text(text),
                ],
            ),
        );
    }

    ButtonStyle _defaultStyle(BuildContext context) {
        return ElevatedButton.styleFrom(
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
        ),
        );
    }
}
```

### Custom Playlist Card

```dart
// lib/widgets/playlist/custom_playlist_card.dart
class CustomPlaylistCard extends StatelessWidget {
    final Playlist playlist;
    final VoidCallback? onTap;
    final VoidCallback? onPlay;
    final VoidCallback? onShare;

    const CustomPlaylistCard({
        Key? key,
        required this.playlist,
        this.onTap,
        this.onPlay,
        this.onShare,
    }) : super(key: key);

    @override
    Widget build(BuildContext context) {
        return Card(
        elevation: 4,
        margin: const EdgeInsets.all(8),

        child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12),
            child: Container(
            padding: const EdgeInsets.all(16),

            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                Row(
                    children: [
                        // Playlist artwork
                        Container(
                            width: 60,
                            height: 60,
                            decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(8),
                                color: Theme.of(context).colorScheme.primaryContainer,
                            ),

                            child: Icon(
                                Icons.music_note,
                                color: Theme.of(context).colorScheme.onPrimaryContainer,
                            ),
                        ),

                        const SizedBox(width: 16),
                        // Playlist info
                        Expanded(
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Text(
                                        playlist.name,
                                        style: Theme.of(context).textTheme.titleMedium,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                    ),

                                    const SizedBox(height: 4),
                                    Text(
                                        '${playlist.tracks.length} songs',
                                        style: Theme.of(context).textTheme.bodySmall,
                                    ),
                                ],
                            ),
                        ),
                        // Action buttons
                        Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                                if (onPlay != null)
                                    IconButton(
                                        onPressed: onPlay,
                                        icon: const Icon(Icons.play_arrow),
                                    ),

                                if (onShare != null)
                                    IconButton(
                                        onPressed: onShare,
                                        icon: const Icon(Icons.share),
                                    ),
                            ],
                        ),
                    ],
                ),
                if (playlist.description.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                    playlist.description,
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    ),
                ],
                ],
            ),
            ),
        ),
        );
    }
}
```

## State Management

### Custom Providers

Create custom providers in `lib/providers/custom/`:

```dart
// lib/providers/custom/settings_provider.dart
class SettingsProvider extends ChangeNotifier {
    bool _darkMode = false;
    bool _hapticFeedback = true;
    double _audioQuality = 0.8;

    bool get darkMode => _darkMode;
    bool get hapticFeedback => _hapticFeedback;
    double get audioQuality => _audioQuality;

    void toggleDarkMode() {
        _darkMode = !_darkMode;

        notifyListeners();
        _saveSettings();
    }

    void setHapticFeedback(bool enabled) {
        _hapticFeedback = enabled;

        notifyListeners();
        _saveSettings();
    }

    void setAudioQuality(double quality) {
        _audioQuality = quality;

        notifyListeners();
        _saveSettings();
    }

    Future<void> _saveSettings() async {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('darkMode', _darkMode);
        await prefs.setBool('hapticFeedback', _hapticFeedback);
        await prefs.setDouble('audioQuality', _audioQuality);
    }

    Future<void> loadSettings() async {
        final prefs = await SharedPreferences.getInstance();
        _darkMode = prefs.getBool('darkMode') ?? false;
        _hapticFeedback = prefs.getBool('hapticFeedback') ?? true;
        _audioQuality = prefs.getDouble('audioQuality') ?? 0.8;
        notifyListeners();
    }
}
```

## Custom Screens

### Adding New Screens

Create new screens in `lib/screens/custom/`:

```dart
// lib/screens/custom/analytics_screen.dart
class AnalyticsScreen extends StatefulWidget {
    const AnalyticsScreen({Key? key}) : super(key: key);

    @override
    State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Music Analytics'),
            ),

            body: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                children: [
                    _buildStatsCard(),

                    const SizedBox(height: 16),
                    _buildGenreChart(),

                    const SizedBox(height: 16),
                    _buildRecentActivity(),
                ],
                ),
            ),
        );
    }

    Widget _buildStatsCard() {
        return Card(
            child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                        _buildStatItem('Playlists', '12'),
                        _buildStatItem('Songs', '284'),
                        _buildStatItem('Hours', '15.2'),
                    ],
                ),
            ),
        );
    }

    Widget _buildStatItem(String label, String value) {
        return Column(
            children: [
                Text(
                    value,
                    style: Theme.of(context).textTheme.headlineMedium,
                ),

                Text(
                    label,
                    style: Theme.of(context).textTheme.bodySmall,
                ),
            ],
        );
    }

    // Add more widgets...
}
```

## Navigation Customization

### Custom Route Transitions

```dart
// lib/utils/custom_route.dart
class CustomRoute<T> extends PageRouteBuilder<T> {
    final Widget child;
    final RouteTransitionsBuilder? transition;

    CustomRoute({required this.child, this.transition, RouteSettings? settings}) : super(
        settings: settings,
        pageBuilder: (context, animation, _) => child,
        transitionsBuilder: transition ?? _defaultTransition,
        transitionDuration: const Duration(milliseconds: 300),
    );

    static Widget _defaultTransition(
        BuildContext context,
        Animation<double> animation,
        Animation<double> secondaryAnimation,
        Widget child,
    ) {
        return SlideTransition(
            position: Tween<Offset>(
                begin: const Offset(1.0, 0.0),
                end: Offset.zero,
            ).animate(animation),

            child: child,
        );
    }
}
```

## Performance Optimization

### Image Caching

```dart
// lib/utils/image_cache.dart
class CustomImageCache {
    static final Map<String, ImageProvider> _cache = {};

    static ImageProvider getImage(String url) {
        if (_cache.containsKey(url)) return _cache[url]!;
        final provider = CachedNetworkImageProvider(url);

        _cache[url] = provider;

        return provider;
    }

    static void clearCache() {
        _cache.clear();
    }
}
```

### List Optimization

```dart
// Use ListView.builder for large lists
ListView.builder(
    itemCount: playlists.length,
    itemBuilder: (context, index) {
        return PlaylistCard(playlist: playlists[index]);
    },
)

// Use AutomaticKeepAliveClientMixin for expensive widgets
class ExpensiveWidget extends StatefulWidget with AutomaticKeepAliveClientMixin {
    @override
    bool get wantKeepAlive => true;

    // Widget implementation...
}
```

## Building Custom Animations

### Hero Animations

```dart
// Shared element transitions
Hero(
    tag: 'playlist-${playlist.id}',
    child: PlaylistCard(playlist: playlist),
)
```

### Custom Transitions

```dart
// lib/animations/custom_animations.dart
class SlideInAnimation extends StatelessWidget {
    final Widget child;
    final Duration duration;
    final Curve curve;

    const SlideInAnimation({
        Key? key,
        required this.child,
        this.duration = const Duration(milliseconds: 300),
        this.curve = Curves.easeInOut,
    }) : super(key: key);

    @override
    Widget build(BuildContext context) {
        return TweenAnimationBuilder<Offset>(
            tween: Tween<Offset>(
                begin: const Offset(0, 1),
                end: Offset.zero,
            ),

            duration: duration,
            curve: curve,

            builder: (context, offset, child) {
                return Transform.translate(
                    offset: Offset(0, offset.dy * 100),
                    child: child,
                );
            },

            child: child,
        );
    }
}
```

## Debugging and Testing

### Custom Debug Panel

```dart
// lib/debug/debug_panel.dart
class DebugPanel extends StatelessWidget {
    @override
    Widget build(BuildContext context) {
        if (!AppConfig.showDebugInfo) return const SizedBox.shrink();

        return Container(
            padding: const EdgeInsets.all(8),
            color: Colors.red.withOpacity(0.1),

            child: Column(
                children: [
                    Text('Debug Mode'),
                    Text('Build: ${AppConfig.buildNumber}'),
                ],
            ),
        );
    }
}
```

## Next Steps

- Review [Deployment Guide](deployment.md)
- Check [API Integration](api-integration.md)
- Explore [Testing Strategies](testing.md)

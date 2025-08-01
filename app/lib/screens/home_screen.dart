import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../providers/playlist_provider.dart';
import '../widgets/info_message_widget.dart';
import '../config/app_constants.dart';
import '../config/app_colors.dart';
import '../systems/discovery_system.dart';

import 'playlist_screen.dart';
import 'settings_screen.dart';
import 'library_screen.dart';
import 'personality_screen.dart';

class HomeScreen extends StatefulWidget {
    const HomeScreen({super.key});

    @override
    State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver, DiscoveryMixin {
    final TextEditingController _promptController = TextEditingController();

    int _selectedIndex = 0;
    bool _hasText = false;
    Key _libraryKey = UniqueKey();

    final List<String> _quickPrompts = [
        "I'm feeling happy and energetic",
        "Something chill and relaxing",
        "Pump me up for a workout",
        "I'm feeling nostalgic",
        "Perfect for a road trip",
        "Help me focus while studying",
        "Romantic dinner vibes",
        "I'm feeling sad and want to embrace it",
        "Upbeat electronic dance music",
        "Cozy acoustic coffee shop vibes",
        "Indie folk for a rainy day"
    ];

    @override
    void initState() {
        super.initState();
        WidgetsBinding.instance.addObserver(this);
        _promptController.addListener(_onTextChanged);

        WidgetsBinding.instance.addPostFrameCallback((_) {
            _refreshDailyLimit();
            initializeDiscovery();
        });
    }

    void _refreshDailyLimit() async {
        final playlistProvider = context.read<PlaylistProvider>();
        await playlistProvider.refreshRateLimitStatus();
    }

    void _onTextChanged() {
        setState(() {
            _hasText = _promptController.text.trim().isNotEmpty;
        });
    }

    @override
    void dispose() {
        WidgetsBinding.instance.removeObserver(this);

        _promptController.removeListener(_onTextChanged);
        _promptController.dispose();

        super.dispose();
    }

    @override
    void didChangeAppLifecycleState(AppLifecycleState state) {
        super.didChangeAppLifecycleState(state);

        if (state == AppLifecycleState.resumed) {
            _refreshDailyLimit();

            if (_selectedIndex == 2) {
                setState(() {
                    _libraryKey = UniqueKey();
                });
            }
        }
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            body: SafeArea(
                child: _buildCurrentScreen(),
            ),

            bottomNavigationBar: _buildBottomNavigationBar(),
            floatingActionButton: FloatingActionButton(
                onPressed: () {
                    Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const SettingsScreen()),
                    );
                },

                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.textPrimary,
                child: const Icon(Icons.settings_rounded),
            ),
        );
    }

    Widget _buildCurrentScreen() {
        switch (_selectedIndex) {
            case 0:
                return _buildHomeScreen();

            case 1:
                return _buildPersonalityScreen();

            case 2:
                return _buildLibraryScreen();

            default:
                return _buildHomeScreen();
        }
    }

    Widget _buildHomeScreen() {
        return Consumer<PlaylistProvider>(
            builder: (context, playlistProvider, child) {
                return Stack(
                    children: [
                        Column(
                            children: [
                                Expanded(
                                    child: SingleChildScrollView(
                                        child: Padding(
                                            padding: const EdgeInsets.all(AppConstants.largePadding),
                                            child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                    _buildHeader(),
                                                    const SizedBox(height: 40),

                                                    _buildPromptInput(playlistProvider),
                                                    const SizedBox(height: 32),

                                                    _buildQuickPrompts(playlistProvider),
                                                    const SizedBox(height: 100),
                                                ],
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),

                        _buildBottomInfoMessages(playlistProvider),
                        _buildBottomLimitIndicator(playlistProvider),
                    ],
                );
            },
        );
    }

    Widget _buildPersonalityScreen() {
        return const PersonalityScreen();
    }

    Widget _buildLibraryScreen() {
        return LibraryScreen(key: _libraryKey);
    }

    Widget _buildHeader() {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                    AppConstants.appName,
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                    ),
                ),

                const SizedBox(height: 8),
                Text(
                    'Create a custom music playlist with the help of AI and natural language processing',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontSize: 16,
                        color: AppColors.textSecondary,
                        height: 1.4,
                    ),
                ),
            ],
        );
    }

    Widget _buildPromptInput(PlaylistProvider provider) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
                TextField(
                    controller: _promptController,
                    maxLines: null,
                    minLines: 3,
                    style: const TextStyle(color: AppColors.textPrimary, fontSize: 16),

                    decoration: InputDecoration(
                        hintText: 'Describe your ideal playlist...',
                        hintStyle: const TextStyle(
                            color: AppColors.textTertiary,
                            fontSize: 16,
                            height: 1.4,
                        ),
                    ),
                ),

                const SizedBox(height: 16),
                buildDiscoverySwitch(
                    label: "Do you want to discover new music?",
                ),

                const SizedBox(height: 24),
                SizedBox(
                    width: double.infinity,
                    height: 56,

                    child: FilledButton(
                        onPressed: (provider.isLoading || !_hasText) ? null : () => _generatePlaylist(provider),
                        style: FilledButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: AppColors.textPrimary,
                            disabledBackgroundColor: AppColors.disabled,
                            disabledForegroundColor: AppColors.textTertiary,
                        ),

                        child: provider.isLoading ? const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                                SizedBox(
                                    width: 24,
                                    height: 24,

                                    child: CircularProgressIndicator(
                                        strokeWidth: 2.5,
                                        valueColor: AlwaysStoppedAnimation<Color>(AppColors.textPrimary),
                                    ),
                                ),

                                SizedBox(width: 16),
                                Text(
                                    'Generating...',
                                 style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                                ),
                            ],
                        )

                        : const Text(
                            'Generate',
                            style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w600
                            ),
                        ),
                    ),
                ),
            ],
        );
    }

    Widget _buildBottomLimitIndicator(PlaylistProvider provider) {
        if (!provider.showPlaylistLimits) return const SizedBox.shrink();

        final rateLimitStatus = provider.rateLimitStatus;

        if (rateLimitStatus == null) return const SizedBox.shrink();

        final requestsMade = rateLimitStatus.requestsMadeToday;
        final maxRequests = rateLimitStatus.maxRequestsPerDay;
        final progress = maxRequests > 0 ? requestsMade / maxRequests : 0.0;

        Color progressColor;

        if (progress <= 0.5) {
            progressColor = AppColors.progressGreen;
        }

        else if (progress <= 0.8) {
            progressColor = AppColors.progressOrange;
        }

        else {
            progressColor = AppColors.progressRed;
        }

        return Positioned(
            left: 16,
            right: 88,
            bottom: 16,

            child: Container(
                height: 56,
                padding: const EdgeInsets.symmetric(
                    horizontal: AppConstants.mediumPadding, 
                    vertical: AppConstants.smallPadding
                ),

                decoration: BoxDecoration(
                    color: const Color(0xFF1A1625),
                    borderRadius: BorderRadius.circular(28),

                    border: Border.all(
                        color: const Color(0xFF2A2635),
                        width: 1,
                    ),
                ),

                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    mainAxisSize: MainAxisSize.min,

                    children: [
                        Text(
                            requestsMade >= maxRequests ? 'Daily limit reached' : 'Daily Playlist limit: $requestsMade/$maxRequests',
                            style: TextStyle(
                                color: progressColor,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                            ),
                        ),

                        const SizedBox(height: 6),
                        Container(
                            height: 4,
                            decoration: BoxDecoration(
                                color: const Color(0xFF2A2635),
                                borderRadius: BorderRadius.circular(2),
                            ),

                            child: ClipRRect(
                                borderRadius: BorderRadius.circular(2),
                                child: LinearProgressIndicator(
                                    value: progress,
                                    backgroundColor: AppColors.transparent,
                                    valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        );
    }

    Widget _buildBottomInfoMessages(PlaylistProvider provider) {
        final infoMessages = provider.infoMessages;
        if (infoMessages.isEmpty) return const SizedBox.shrink();

        double bottomPosition = 100;

        if (provider.showPlaylistLimits && provider.rateLimitStatus != null) bottomPosition = 76;

        return Positioned(
            left: 16,
            right: 88,
            bottom: bottomPosition,

            child: Column(
                mainAxisSize: MainAxisSize.min,
                children: infoMessages.map((message) {
                    return InfoMessageWidget(
                        message: message,
                        onDismiss: () => provider.removeInfoMessage(message.id),
                    );
                }).toList(),
            ),
        );
    }

    Widget _buildQuickPrompts(PlaylistProvider provider) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                    'Quick Suggestions',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 16),
                Wrap(
                    spacing: 12,
                    runSpacing: 12,

                    children: _quickPrompts.map((prompt) {
                        return ActionChip(
                            label: Text(prompt),
                            onPressed: provider.isLoading ? null : () {
                                _promptController.text = prompt;
                                _generatePlaylist(provider);
                            },

                            backgroundColor: const Color(0xFF1A1625),
                            disabledColor: const Color(0xFF1A1625),

                            labelStyle: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                            ),

                            side: const BorderSide(
                                color: Color(0xFF8B5CF6),
                                width: 1,
                            ),

                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(20),
                            ),

                            elevation: 0,
                            shadowColor: AppColors.transparent,
                        );
                    }).toList(),
                ),
            ],
        );
    }

    Widget _buildBottomNavigationBar() {
        return BottomNavigationBar(
            currentIndex: _selectedIndex,
            onTap: (index) {
                setState(() {
                    _selectedIndex = index;
                });

                if (index == 0) _refreshDailyLimit();

                if (index == 2) {
                    setState(() {
                        _libraryKey = UniqueKey();
                    });
                }
            },

            items: const [
                BottomNavigationBarItem(
                    icon: Icon(Icons.home_rounded),
                    label: 'Home',
                ),

                BottomNavigationBarItem(
                    icon: Icon(Icons.psychology_rounded),
                    label: 'Personality',
                ),
            
                BottomNavigationBarItem(
                    icon: Icon(Icons.library_music_rounded),
                    label: 'Library',
                ),
            ],
        );
    }

    void _generatePlaylist(PlaylistProvider provider) async {
        final prompt = _promptController.text.trim();
        final strategy = getGenerationStrategy();

        try {
            await provider.generatePlaylist(prompt, discoveryStrategy: strategy);
            if (!mounted) return;

            if (provider.error != null) {
                _showErrorDialog(provider.error!);
            }

            else {
                Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const PlaylistScreen(),
                    ),
                );
            }
        }

        catch (e) {
            if (!mounted) return;
            _showErrorDialog(e.toString());
        }
    }

    void _showErrorDialog(String error) {
        String displayError = error;
        String title = 'Error';

        if (error.toLowerCase().contains('rate limit') || error.toLowerCase().contains('limit reached') || error.toLowerCase().contains('daily limit')) {
            title = 'Daily Limit Reached';
            displayError = 'You\'ve reached your daily playlist generation limit. Please try again tomorrow or upgrade your plan for more playlists.';
        }

        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: Text(
                    title,
                    style: const TextStyle(color: Colors.white),
                ),

                content: Text(
                    displayError,
                    style: const TextStyle(color: Colors.white70),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'OK',
                            style: TextStyle(color: Color(0xFF8B5CF6)),
                        ),
                    ),
                ],
            ),
        );
    }
}

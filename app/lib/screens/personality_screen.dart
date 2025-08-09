import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../systems/ui_components/advanced_settings_widget.dart';
import '../systems/advanced_settings_system.dart';
import '../systems/universal_screen_focus_api_system.dart';
import '../services/personality_service.dart';
import '../providers/playlist_provider.dart';
import '../services/message_service.dart';
import '../services/config_service.dart';
import '../services/auth_service.dart';
import '../config/app_constants.dart';
import '../models/user_context.dart';
import '../utils/app_logger.dart';

class PersonalityScreen extends StatefulWidget {
    const PersonalityScreen({super.key});

    @override
    State<PersonalityScreen> createState() => _PersonalityScreenState();
}

class _PersonalityScreenState extends State<PersonalityScreen> with TickerProviderStateMixin, WidgetsBindingObserver, AdvancedSettingsMixin, UniversalScreenFocusApiMixin implements PersonalityResetCallback {
    late TabController _tabController;
    
    UserContext? _userContext;
    List<SpotifyArtist> _followedArtists = [];
    bool _isLoading = true;
    String? _error;

    final bool _isSaving = false;

    int _maxFavoriteGenres = 10;
    int _maxPreferredDecades = 5;

    List<String> _selectedGenres = [];
    List<String> _selectedDecades = [];
    Map<String, String> _personalityAnswers = {};

    bool _includeSpotifyArtists = true;

    @override
    void initState() {
        super.initState();
        WidgetsBinding.instance.addObserver(this);
        
        _tabController = TabController(length: 3, vsync: this);

        _tabController.addListener(() {
            if (!mounted) return;

            if (!_tabController.indexIsChanging) {
                AppLogger.personality('Tab changed to index: ${_tabController.index}');
                // Use direct refresh for sub-tab changes
                _silentRefreshPersonalityData();
            }
        });
        
        WidgetsBinding.instance.addPostFrameCallback((_) {
            initializeScreenFocusApiSystem(isActiveTab: true);
        });
        
        // Removed _loadPersonalityData() - now handled by Universal API system
    }

    @override
    void registerScreenFocusApiCalls() {
        // Register user context refresh for personality screen
        screenFocusApiSystem.registerApiCall(ScreenFocusApiCall(
            name: 'personality_user_context_refresh',
            apiCall: (context) async {
                await _loadPersonalityData(); // Use full load for screen enter/app resume
            },
            runOnScreenEnter: true,
            runOnAppResume: true,
            oncePerSession: true, // Once per session for main screen focus
        ));
    }

    Future<void> _silentRefreshPersonalityData() async {
        if (!mounted) return;
        
        try {
            final personalityService = context.read<PersonalityService>();
            final existingContext = await personalityService.loadUserContext();

            if (existingContext != null && mounted) {
                _userContext = existingContext;
                _populateFormFromContext(existingContext);

                await _loadFollowedArtists();

                if (mounted) {
                    setState(() {});
                }
            }
        }

        catch (e) {
            AppLogger.personality('Silent refresh failed: $e', error: e);
        }
    }

    @override
    void dispose() {
        WidgetsBinding.instance.removeObserver(this);
        _tabController.dispose();
        super.dispose();
    }

    Future<void> _loadPersonalityData() async {
        setState(() {
            _isLoading = true;
            _error = null;
        });

        try {
            final personalityService = context.read<PersonalityService>();
            final configService = context.read<ConfigService>();
            final personalityConfig = await configService.getPersonalityConfig();

            _maxFavoriteGenres = personalityConfig.maxFavoriteGenres;
            _maxPreferredDecades = personalityConfig.maxPreferredDecades;

            updateArtistLimits(
                maxFavorite: personalityConfig.maxFavoriteArtists,
                maxDisliked: personalityConfig.maxDislikedArtists,
            );

            final existingContext = await personalityService.loadUserContext();

            if (existingContext != null) {
                _userContext = existingContext;
                _populateFormFromContext(existingContext);
            }

            await _loadFollowedArtists();

        }

        catch (e) {
            if (mounted) {
                setState(() => _error = 'Failed to load personality data: ${e.toString()}');
            }
        }

        finally {
            if (mounted) {
                setState(() => _isLoading = false);
            }
        }
    }

    Future<void> _loadFollowedArtists() async {
        final authService = context.read<AuthService>();
        if (authService.userId == null) return;

        try {
            final personalityService = context.read<PersonalityService>();
            _followedArtists = await personalityService.fetchFollowedArtists(userId: authService.userId);

            if (_userContext == null) {
                final defaultContext = await personalityService.getDefaultPersonalityContext(userId: authService.userId);
                _userContext = defaultContext;
                _populateFormFromContext(defaultContext);
            }

            await personalityService.markArtistsSynced();
        }

        catch (e) {
            if (mounted) {
                MessageService.showError(context, 'Failed to load followed artists');
            }
        }
    }

    void _populateFormFromContext(UserContext context) {
        setState(() {
            _selectedGenres = List.from(context.favoriteGenres ?? []);

            final allFavoriteArtists = context.favoriteArtists ?? [];
            final followedArtistNames = _followedArtists.map((a) => a.name).toSet();

            final customArtists = allFavoriteArtists.where((artist) => !followedArtistNames.contains(artist)).toList();

            updateArtistSettings(
                favoriteArtists: customArtists,
                dislikedArtists: context.dislikedArtists ?? [],
            );

            _selectedDecades = List.from(context.decadePreference ?? []);
            _includeSpotifyArtists = context.includeSpotifyArtists ?? true;

            _personalityAnswers = {
                'music_activity_preference': context.musicActivityPreference ?? '',
                'energy_preference': context.energyPreference ?? '',
                'genre_openness': context.genreOpenness ?? '',
                'vocal_preference': context.vocalPreference ?? '',
                'explicit_content_preference': context.explicitContentPreference ?? '',
                'discovery_openness': context.discoveryOpenness ?? '',
                'instrumental_preference': context.instrumentalPreference ?? '',
                'music_discovery_preference': context.musicDiscoveryPreference ?? '',
            };

            AppLogger.personality('Loaded personality answers: $_personalityAnswers');
            AppLogger.personality('Loaded music_activity_preference: ${context.musicActivityPreference}');
            AppLogger.personality('Loaded genre_openness: ${context.genreOpenness}');
            AppLogger.personality('Loaded vocal_preference: ${context.vocalPreference}');
        });
    }

    Future<void> _autoSavePersonality() async {
        try {
            String? nullIfEmpty(String? value) => value?.isEmpty == true ? null : value;

            AppLogger.personality('Auto-saving personality...');
            AppLogger.personality('Current personality answers: $_personalityAnswers');
            AppLogger.personality('music_activity_preference: ${nullIfEmpty(_personalityAnswers['music_activity_preference'])}');
            AppLogger.personality('energy_preference: ${nullIfEmpty(_personalityAnswers['energy_preference'])}');
            AppLogger.personality('genre_openness: ${nullIfEmpty(_personalityAnswers['genre_openness'])}');
            AppLogger.personality('vocal_preference: ${nullIfEmpty(_personalityAnswers['vocal_preference'])}');
            AppLogger.personality('explicit_content_preference: ${nullIfEmpty(_personalityAnswers['explicit_content_preference'])}');

            final updatedContext = UserContext(
                favoriteGenres: _selectedGenres,
                favoriteArtists: customFavoriteArtists,
                dislikedArtists: customDislikedArtists,
                decadePreference: _selectedDecades,
                includeSpotifyArtists: _includeSpotifyArtists,
                musicActivityPreference: nullIfEmpty(_personalityAnswers['music_activity_preference']),
                energyPreference: nullIfEmpty(_personalityAnswers['energy_preference']),
                genreOpenness: nullIfEmpty(_personalityAnswers['genre_openness']),
                vocalPreference: nullIfEmpty(_personalityAnswers['vocal_preference']),
                explicitContentPreference: nullIfEmpty(_personalityAnswers['explicit_content_preference']),
                discoveryOpenness: nullIfEmpty(_personalityAnswers['discovery_openness']),
                instrumentalPreference: nullIfEmpty(_personalityAnswers['instrumental_preference']),
                musicDiscoveryPreference: nullIfEmpty(_personalityAnswers['music_discovery_preference']),
            );

            AppLogger.personality('Calling PersonalityService.saveUserContext...');
            AppLogger.personality('UserContext about to be saved: ${updatedContext.toJson()}');

            await context.read<PersonalityService>().saveUserContext(updatedContext);
            _userContext = updatedContext;

            if (mounted) {
                context.read<PlaylistProvider>().updateUserContext(updatedContext);
            }

            AppLogger.personality('Auto-save completed successfully');
        }

        catch (e) {
            AppLogger.personality('Auto-save failed: $e', error: e);
        }
    }

    @override
    void onResetPersonalitySettings() {
        setState(() {
            _selectedGenres = [];
            _selectedDecades = [];
            _personalityAnswers = {
                'music_activity_preference': '',
                'energy_preference': '',
                'genre_openness': '',
                'vocal_preference': '',
                'explicit_content_preference': '',
                'discovery_openness': '',
                'instrumental_preference': '',
                'music_discovery_preference': '',
            };

            _includeSpotifyArtists = true;
        });

        updateArtistSettings(
            favoriteArtists: [],
            dislikedArtists: [],
        );

        _autoSavePersonality();
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Music Personality'),
                bottom: TabBar(
                    controller: _tabController,
                    tabs: const [
                        Tab(text: 'Taste', icon: Icon(Icons.favorite_rounded)),
                        Tab(text: 'Quiz', icon: Icon(Icons.quiz_rounded)),
                        Tab(text: 'Advanced', icon: Icon(Icons.tune_rounded)),
                    ],
                ),

                actions: [
                    if (_isSaving)
                        const Padding(
                            padding: EdgeInsets.symmetric(horizontal: AppConstants.mediumPadding),
                            child: Center(
                                child: SizedBox(
                                    width: AppConstants.mediumIconSize,
                                    height: AppConstants.mediumIconSize,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                ),
                            ),
                        )
                ],
            ),

            body: _isLoading ? const Center(child: CircularProgressIndicator()) : TabBarView(
                controller: _tabController,
                children: [
                    _buildPreferencesTab(),
                    _buildQuestionsTab(),
                    _buildAdvancedTab(),
                ],
            ),
        );
    }

    Widget _buildPreferencesTab() {
        if (_error != null) {
            return Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        const Icon(Icons.error, size: 48, color: Colors.red),
                        const SizedBox(height: 16),

                        Text(
                            _error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                        ),

                        const SizedBox(height: 16),
                        FilledButton(
                            onPressed: _loadPersonalityData,
                            child: const Text('Retry'),
                        ),
                    ],
                ),
            );
        }
        
        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    _buildSectionHeader('Favorite Genres (${_selectedGenres.length}/$_maxFavoriteGenres)', 'Select genres you enjoy'),
                    const SizedBox(height: AppConstants.mediumSpacing),

                    _buildGenreSelection(),
                    const SizedBox(height: AppConstants.largeSpacing),
                    
                    _buildSectionHeader('Preferred Decades (${_selectedDecades.length}/$_maxPreferredDecades)', 'Choose your favorite musical eras'),
                    const SizedBox(height: AppConstants.mediumSpacing),
                    _buildDecadeSelection(),
                ],
            ),
        );
    }

    Widget _buildQuestionsTab() {
        if (_error != null) {
            return Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        const Icon(Icons.error, size: 48, color: Colors.red),
                        const SizedBox(height: 16),

                        Text(
                            _error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                        ),

                        const SizedBox(height: 16),
                        FilledButton(
                            onPressed: _loadPersonalityData,
                            child: const Text('Retry'),
                        ),
                    ],
                ),
            );
        }

        final questions = context.read<PersonalityService>().getPersonalityQuestions();

        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    _buildSectionHeader('Personality Questions', 'Help us understand your music taste better'),
                    const SizedBox(height: AppConstants.largeSpacing),

                    ...questions.entries.map((entry) => _buildPersonalityQuestion(
                        key: entry.key,
                        question: entry.value['question'],
                        options: List<String>.from(entry.value['options']),
                    )),
                ],
            ),
        );
    }

    Widget _buildAdvancedTab() {
        if (_error != null) {
            return Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        const Icon(Icons.error, size: 48, color: Colors.red),
                        const SizedBox(height: 16),

                        Text(
                            _error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                        ),

                        const SizedBox(height: 16),
                        FilledButton(
                            onPressed: _loadPersonalityData,
                            child: const Text('Retry'),
                        ),
                    ],
                ),
            );
        }

        return AdvancedSettingsWidget(
            initialFavoriteArtists: customFavoriteArtists,
            initialDislikedArtists: customDislikedArtists,
            onDataChanged: _loadPersonalityData,
            onResetAllSettings: onResetPersonalitySettings,

            onSave: (userContext) {
                if (userContext.favoriteArtists != null) {
                    updateArtistSettings(
                        favoriteArtists: userContext.favoriteArtists,
                    );
                }

                if (userContext.dislikedArtists != null) {
                    updateArtistSettings(
                        dislikedArtists: userContext.dislikedArtists,
                    );
                }

                _autoSavePersonality();
            },
        );
    }

    Widget _buildSectionHeader(String title, String subtitle) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                    ),
                ),

                const SizedBox(height: AppConstants.smallSpacing),
                Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                    ),
                ),
            ],
        );
    }

    Widget _buildGenreSelection() {
        final availableGenres = context.read<PersonalityService>().getAvailableGenres();

        return Wrap(
            spacing: AppConstants.smallSpacing,
            runSpacing: AppConstants.smallSpacing,

            children: availableGenres.map((genre) {
                final isSelected = _selectedGenres.contains(genre);
                return FilterChip(
                    label: Text(genre),
                    selected: isSelected,
                    onSelected: (selected) {
                        setState(() {
                            if (selected && _selectedGenres.length < _maxFavoriteGenres) {
                                _selectedGenres.add(genre);
                            }

                            else if (!selected) {
                                _selectedGenres.remove(genre);
                            }
                        });

                        _autoSavePersonality();
                    },

                    backgroundColor: const Color(0xFF1A1625),
                    selectedColor: const Color(0xFF8B5CF6),
                    checkmarkColor: Colors.white,
                    elevation: isSelected ? 2 : 0,
                    shadowColor: isSelected ? Colors.black26 : null,

                    labelStyle: TextStyle(
                        color: isSelected ? Colors.white : Colors.white70,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                    ),

                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                        side: BorderSide(
                            color: isSelected ? const Color(0xFF8B5CF6) : const Color(0xFF2A2A2A),
                            width: 1,
                        ),
                    ),
                );
            }).toList(),
        );
    }

    Widget _buildDecadeSelection() {
        final availableDecades = context.read<PersonalityService>().getAvailableDecades();

        return Wrap(
            spacing: AppConstants.smallSpacing,
            runSpacing: AppConstants.smallSpacing,

            children: availableDecades.map((decade) {
                final isSelected = _selectedDecades.contains(decade);
                return FilterChip(
                    label: Text(decade),
                    selected: isSelected,

                    onSelected: (selected) {
                        setState(() {
                            if (selected && _selectedDecades.length < _maxPreferredDecades) {
                                _selectedDecades.add(decade);
                            }

                            else if (!selected) {
                                _selectedDecades.remove(decade);
                            }
                        });

                        _autoSavePersonality();
                    },

                    backgroundColor: const Color(0xFF1A1625),
                    selectedColor: const Color(0xFF8B5CF6),
                    checkmarkColor: Colors.white,
                    elevation: isSelected ? 2 : 0,
                    shadowColor: isSelected ? Colors.black26 : null,

                    labelStyle: TextStyle(
                        color: isSelected ? Colors.white : Colors.white70,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                    ),

                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                        side: BorderSide(
                            color: isSelected ? const Color(0xFF8B5CF6) : const Color(0xFF2A2A2A),
                            width: 1,
                        ),
                    ),
                );
            }).toList(),
        );
    }

    Widget _buildPersonalityQuestion({required String key, required String question, required List<String> options}) {
        final currentAnswer = _personalityAnswers[key] ?? '';

        return Card(
            margin: const EdgeInsets.only(bottom: AppConstants.mediumSpacing),
            child: Padding(
                padding: const EdgeInsets.all(AppConstants.mediumPadding),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                            question,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                            ),
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),
                        ...options.map((option) {
                            final isSelected = currentAnswer == option;
                            return Padding(
                                padding: const EdgeInsets.only(bottom: AppConstants.smallSpacing),
                                child: InkWell(
                                    onTap: () {
                                        setState(() {
                                            _personalityAnswers[key] = option;
                                        });

                                        AppLogger.personality('Quiz Answer Updated: $key = $option');
                                        AppLogger.personality('All Answers: $_personalityAnswers');

                                        _autoSavePersonality();
                                    },

                                    borderRadius: BorderRadius.circular(AppConstants.mediumRadius),
                                    child: Container(
                                        width: double.infinity,
                                        padding: const EdgeInsets.all(AppConstants.mediumPadding),

                                        decoration: BoxDecoration(
                                            color: isSelected ? const Color(0xFF8B5CF6).withValues(alpha: 0.2) : Colors.transparent,
                                            borderRadius: BorderRadius.circular(AppConstants.mediumRadius),
                                            border: Border.all(
                                                color: isSelected ? const Color(0xFF8B5CF6) : const Color(0xFF2A2A2A),
                                                width: 1,
                                            ),
                                        ),

                                        child: Row(
                                            children: [
                                                Icon(
                                                    isSelected ? Icons.radio_button_checked_rounded : Icons.radio_button_unchecked_rounded,
                                                    color: isSelected ? const Color(0xFF8B5CF6) : Colors.white54,
                                                    size: AppConstants.mediumIconSize,
                                                ),

                                                const SizedBox(width: AppConstants.mediumSpacing),
                                                Expanded(
                                                    child: Text(
                                                        option,
                                                        style: TextStyle(
                                                            color: isSelected ? Colors.white : Colors.white70,
                                                            fontWeight: isSelected ? FontWeight.w500 : FontWeight.normal,
                                                        ),
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ),
                                ),
                            );
                        }),
                    ],
                ),
            ),
        );
    }
}

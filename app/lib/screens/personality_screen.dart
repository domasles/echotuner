import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/personality_service.dart';
import '../providers/playlist_provider.dart';
import '../services/message_service.dart';
import '../services/config_service.dart';
import '../services/auth_service.dart';
import '../config/app_constants.dart';
import '../models/user_context.dart';

class PersonalityScreen extends StatefulWidget {
    const PersonalityScreen({super.key});

    @override
    State<PersonalityScreen> createState() => _PersonalityScreenState();
}

class _PersonalityScreenState extends State<PersonalityScreen> with TickerProviderStateMixin {
    late TabController _tabController;
    
    UserContext? _userContext;
    List<SpotifyArtist> _followedArtists = [];
    bool _isLoading = true;

    final bool _isSaving = false;

    int _maxFavoriteArtists = 12;
    int _maxDislikedArtists = 20;
    int _maxFavoriteGenres = 10;

    List<String> _selectedGenres = [];
    List<String> _likedArtists = [];
    List<String> _dislikedArtists = [];
    List<String> _selectedDecades = [];
    Map<String, String> _personalityAnswers = {};

    bool _includeSpotifyArtists = true;

    @override
    void initState() {
        super.initState();
        _tabController = TabController(length: 4, vsync: this);

        _tabController.addListener(() {
            if (!_tabController.indexIsChanging) {
                _refreshCurrentTab();
            }
        });
        
        _loadPersonalityData();
    }

    @override
    void dispose() {
        _tabController.dispose();
        super.dispose();
    }

    void _refreshCurrentTab() {
        if (!mounted) return;
        
        switch (_tabController.index) {
            case 0: // Basic info - no refresh needed
                break;
            case 1: // Music preferences - refresh spotify artists if needed
                if (_includeSpotifyArtists && _followedArtists.isEmpty) {
                    _loadFollowedArtists();
                }
                break;
            case 2: // Personality - no refresh needed
                break;
            case 3: // Advanced - no refresh needed
                break;
        }
    }

    Future<void> _loadPersonalityData() async {
        setState(() => _isLoading = true);

        try {
            final personalityService = context.read<PersonalityService>();
            final configService = context.read<ConfigService>();
            final personalityConfig = await configService.getPersonalityConfig();

            _maxFavoriteArtists = personalityConfig.maxFavoriteArtists;
            _maxDislikedArtists = personalityConfig.maxDislikedArtists;
            _maxFavoriteGenres = personalityConfig.maxFavoriteGenres;

            final existingContext = await personalityService.loadUserContext();

            if (existingContext != null) {
                _userContext = existingContext;
                _populateFormFromContext(existingContext);
            }

            await _loadFollowedArtists();

        }

        catch (e) {
            if (mounted) {
                MessageService.showError(context, 'Failed to load personality data');
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
        if (authService.sessionId == null) return;

        try {
            final personalityService = context.read<PersonalityService>();
            _followedArtists = await personalityService.fetchFollowedArtists(sessionId: authService.sessionId);

            if (_userContext == null) {
                final defaultContext = await personalityService.getDefaultPersonalityContext(sessionId: authService.sessionId);
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

            _likedArtists = allFavoriteArtists.where((artist) => !followedArtistNames.contains(artist)).toList();
            _dislikedArtists = List.from(context.dislikedArtists ?? []);

            _selectedDecades = [];
            _includeSpotifyArtists = context.includeSpotifyArtists ?? true;

            _personalityAnswers = {
                'happy_music_preference': context.happyMusicPreference ?? '',
                'sad_music_preference': context.sadMusicPreference ?? '',
                'workout_music_preference': context.workoutMusicPreference ?? '',
                'focus_music_preference': context.focusMusicPreference ?? '',
                'relaxation_music_preference': context.relaxationMusicPreference ?? '',
                'party_music_preference': context.partyMusicPreference ?? '',
                'discovery_openness': context.discoveryOpenness ?? '',
                'explicit_content_preference': context.explicitContentPreference ?? '',
                'instrumental_preference': context.instrumentalPreference ?? '',
            };
        });
    }

    Future<void> _autoSavePersonality() async {
        try {
            final updatedContext = (_userContext ?? UserContext()).copyWith(
                favoriteGenres: _selectedGenres,
                favoriteArtists: _likedArtists,
                dislikedArtists: _dislikedArtists,
                decadePreference: _selectedDecades,
                includeSpotifyArtists: _includeSpotifyArtists,
                happyMusicPreference: _personalityAnswers['happy_music_preference'],
                sadMusicPreference: _personalityAnswers['sad_music_preference'],
                workoutMusicPreference: _personalityAnswers['workout_music_preference'],
                focusMusicPreference: _personalityAnswers['focus_music_preference'],
                relaxationMusicPreference: _personalityAnswers['relaxation_music_preference'],
                partyMusicPreference: _personalityAnswers['party_music_preference'],
                discoveryOpenness: _personalityAnswers['discovery_openness'],
                explicitContentPreference: _personalityAnswers['explicit_content_preference'],
                instrumentalPreference: _personalityAnswers['instrumental_preference'],
            );

            await context.read<PersonalityService>().saveUserContext(updatedContext);

            if (mounted) {
                context.read<PlaylistProvider>().updateUserContext(updatedContext);
            }
        }
        
        catch (e) {
            // Silent - don't show error messages
        }
    }

    Future<void> _syncSpotifyArtists() async {
        final authService = context.read<AuthService>();
        if (authService.sessionId == null) {
            if (mounted) {
                MessageService.showError(context, 'Please login to Spotify first');
            }
            return;
        }

        try {
            final personalityService = context.read<PersonalityService>();
            _followedArtists = await personalityService.fetchFollowedArtists(
                sessionId: authService.sessionId
            );

            await personalityService.markArtistsSynced();
            if (mounted) {
                MessageService.showSuccess(context, 'Synced ${_followedArtists.length} followed artists from Spotify');
            }
        }
        
        catch (e) {
            if (mounted) {
                MessageService.showError(context, 'Failed to sync followed artists');
            }
        }
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
                        Tab(text: 'Artists', icon: Icon(Icons.person_rounded)),
                        Tab(text: 'Quiz', icon: Icon(Icons.quiz_rounded)),
                        Tab(text: 'Settings', icon: Icon(Icons.tune_rounded)),
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
                    _buildArtistsTab(),
                    _buildQuestionsTab(),
                    _buildSettingsTab(),
                ],
            ),
        );
    }

    Widget _buildPreferencesTab() {
        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    _buildSectionHeader('Favorite Genres', 'Select genres you enjoy'),
                    const SizedBox(height: AppConstants.mediumSpacing),
                    _buildGenreSelection(),
                    const SizedBox(height: AppConstants.extraLargeSpacing),
                    
                    _buildSectionHeader('Preferred Decades', 'Choose your favorite musical eras'),
                    const SizedBox(height: AppConstants.mediumSpacing),
                    _buildDecadeSelection(),
                ],
            ),
        );
    }

    Widget _buildArtistsTab() {
        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(AppConstants.mediumPadding),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Row(
                                        children: [
                                            Expanded(
                                                child: Column(
                                                    crossAxisAlignment: CrossAxisAlignment.start,
                                                    children: [
                                                        Text(
                                                            'Spotify Followed Artists',
                                                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                                                fontWeight: FontWeight.bold,
                                                            ),
                                                        ),

                                                        Text(
                                                            'Artists you follow on Spotify',
                                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                                                color: Colors.white70,
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                            ),

                                            Switch(
                                                value: _includeSpotifyArtists,
                                                onChanged: (value) {
                                                    setState(() {
                                                        _includeSpotifyArtists = value;
                                                    });

                                                    _autoSavePersonality();
                                                },
                                            ),
                                        ],
                                    ),

                                    if (_includeSpotifyArtists) ...[
                                        const SizedBox(height: AppConstants.mediumSpacing),
                                        Row(
                                            children: [
                                                Expanded(
                                                    child: Text(
                                                        '${_followedArtists.length} followed artists',
                                                        style: Theme.of(context).textTheme.bodySmall,
                                                    ),
                                                ),

                                                TextButton.icon(
                                                    onPressed: _syncSpotifyArtists,
                                                    icon: const Icon(Icons.sync_rounded, size: AppConstants.smallIconSize),
                                                    label: const Text('Sync'),
                                                    style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: AppConstants.mediumPadding, vertical: AppConstants.tinyPadding)),
                                                ),
                                            ],
                                        ),

                                        if (_followedArtists.isNotEmpty) ...[
                                            const SizedBox(height: AppConstants.smallSpacing),
                                            Wrap(
                                                spacing: AppConstants.smallSpacing,
                                                runSpacing: AppConstants.smallSpacing,
                                                children: _followedArtists.take(10).map(
                                                    (artist) => Chip(
                                                        label: Text(artist.name),
                                                        avatar: CircleAvatar(
                                                            backgroundImage: artist.imageUrl != null ? NetworkImage(artist.imageUrl!) : null,
                                                            child: artist.imageUrl == null ? const Icon(Icons.person, size: 16) : null,
                                                        ),
                                                    )
                                                ).toList(),
                                            ),
                                        ]

                                        else ...[
                                            const SizedBox(height: AppConstants.smallSpacing),
                                            Text(
                                                'No followed artists found. Make sure you follow artists on Spotify.',
                                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                                    color: Colors.white54,
                                                ),
                                            ),
                                        ],
                                    ],
                                ],
                            ),
                        ),
                    ),

                    const SizedBox(height: AppConstants.largeSpacing),

                    _buildSectionHeader('Custom Favorite Artists', 'Artists you love (${_likedArtists.length}/$_maxFavoriteArtists)'),
                    const SizedBox(height: AppConstants.smallSpacing),

                    _buildLikedArtistSelection(),
                    const SizedBox(height: AppConstants.extraLargeSpacing),

                    _buildSectionHeader('Disliked Artists', 'Artists to exclude from playlists(${_dislikedArtists.length}/$_maxDislikedArtists)'),
                    const SizedBox(height: AppConstants.smallSpacing),

                    _buildDislikedArtistSelection(),
                ],
            ),
        );
    }

    Widget _buildQuestionsTab() {
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

    Widget _buildSettingsTab() {
        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    _buildSectionHeader('Advanced Settings', 'Settings for power users'),
                    const SizedBox(height: AppConstants.largeSpacing),

                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(AppConstants.mediumPadding),
                            child: Column(
                                children: [
                                    ListTile(
                                        leading: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                                        title: const Text('Reset Personality', style: TextStyle(color: Colors.red)),
                                        subtitle: const Text('Clear all saved preferences'),
                                        trailing: const Icon(Icons.arrow_forward_ios_rounded, color: Colors.red),
                                        onTap: _showResetDialog,
                                    ),
                                ],
                            ),
                        ),
                    ),
                ],
            ),
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
                            if (selected) {
                                _selectedDecades.add(decade);
                            }

                            else {
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

    Widget _buildLikedArtistSelection() {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                const SizedBox(height: AppConstants.smallSpacing),

                if (_likedArtists.isNotEmpty) ...[
                    Wrap(
                        spacing: AppConstants.smallSpacing,
                        runSpacing: AppConstants.smallSpacing,
                        children: _likedArtists.map((artist) {
                            return Chip(
                                label: Text(artist),
                                onDeleted: () {
                                    setState(() {
                                        _likedArtists.remove(artist);
                                    });

                                    _autoSavePersonality();
                                },

                                deleteIcon: const Icon(Icons.close_rounded, size: AppConstants.smallIconSize),
                                backgroundColor: const Color(0xFF8B5CF6),

                                labelStyle: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w500,
                                ),

                                deleteIconColor: Colors.white,
                                elevation: 2,
                                shadowColor: Colors.black26,

                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(20),
                                    side: BorderSide.none,
                                ),

                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            );
                        }).toList(),
                    ),
                    const SizedBox(height: AppConstants.smallSpacing),
                ],

                OutlinedButton.icon(
                    onPressed: _showAddArtistDialog,
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Add Custom Artist'),
                    style: OutlinedButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppConstants.buttonRadius))),
                ),
            ],
        );
    }

    Widget _buildDislikedArtistSelection() {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                const SizedBox(height: AppConstants.smallSpacing),

                if (_dislikedArtists.isNotEmpty) ...[
                    Wrap(
                        spacing: AppConstants.smallSpacing,
                        runSpacing: AppConstants.smallSpacing,
                        children: _dislikedArtists.map((artist) {
                            return Chip(
                                label: Text(artist),
                                onDeleted: () {
                                    setState(() {
                                        _dislikedArtists.remove(artist);
                                    });

                                    _autoSavePersonality();
                                },

                                deleteIcon: const Icon(Icons.close_rounded, size: AppConstants.smallIconSize),
                                backgroundColor: Colors.red.withValues(alpha: 0.1),

                                labelStyle: const TextStyle(
                                    color: Colors.red,
                                    fontWeight: FontWeight.w500,
                                ),

                                deleteIconColor: Colors.red,
                                elevation: 1,
                                shadowColor: Colors.red.withValues(alpha: 0.2),

                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(20),
                                    side: BorderSide(color: Colors.red.withValues(alpha: 0.3), width: 1),
                                ),

                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            );
                        }).toList(),
                    ),

                    const SizedBox(height: AppConstants.smallSpacing),
                ],

                OutlinedButton.icon(
                    onPressed: _showAddDislikedArtistDialog,
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Add Disliked Artist'),

                    style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.red,
                        side: const BorderSide(color: Colors.red),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppConstants.buttonRadius),
                        ),
                    ),
                ),
            ],
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

    void _showAddArtistDialog() {
        showDialog(
            context: context,
            builder: (context) => _ArtistSearchDialog(
                personalityService: context.read<PersonalityService>(),
                onArtistSelected: (artist) {
                    if (!_likedArtists.contains(artist.name) && _likedArtists.length < _maxFavoriteArtists) {
                        setState(() {
                            _likedArtists.add(artist.name);
                        });

                        _autoSavePersonality();
                    }
                },
            ),
        );
    }

    void _showAddDislikedArtistDialog() {
        showDialog(
            context: context,
            builder: (context) => _ArtistSearchDialog(
                personalityService: context.read<PersonalityService>(),
                onArtistSelected: (artist) {
                    if (!_dislikedArtists.contains(artist.name) &&
                        _dislikedArtists.length < _maxDislikedArtists) {

                        setState(() {
                            _dislikedArtists.add(artist.name);
                        });

                        _autoSavePersonality();
                    }
                },
            ),
        );
    }

    void _showResetDialog() {
        showDialog(
            context: context,
            builder: (dialogContext) => AlertDialog(
                title: const Text('Reset Personality'),
                content: const Text(
                    'This will clear all your saved preferences, including favorite artists, genres, and personality answers. This action cannot be undone.',
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(dialogContext).pop(),
                        child: const Text('Cancel'),
                    ),

                    FilledButton(
                        onPressed: () async {
                            final navigator = Navigator.of(dialogContext);
                            final personalityService = context.read<PersonalityService>();
                            final playlistProvider = context.read<PlaylistProvider>();
                            
                            navigator.pop();

                            try {
                                await personalityService.clearUserContext();

                                if (mounted) {
                                    playlistProvider.updateUserContext(null);

                                    setState(() {
                                        _selectedGenres.clear();
                                        _likedArtists.clear();
                                        _dislikedArtists.clear();
                                        _selectedDecades.clear();
                                        _personalityAnswers.clear();
                                        _includeSpotifyArtists = true;
                                    });

                                    MessageService.showSuccess(context, 'Personality settings reset successfully');
                                }
                            }

                            catch (e) {
                                if (mounted) {
                                    MessageService.showError(context, 'Failed to reset personality settings');
                                }
                            }
                        },

                        style: FilledButton.styleFrom(backgroundColor: Colors.red),
                        child: const Text('Reset'),
                    ),
                ],
            ),
        );
    }
}

class _ArtistSearchDialog extends StatefulWidget {
    final PersonalityService personalityService;
    final Function(SpotifyArtist) onArtistSelected;

    const _ArtistSearchDialog({
        required this.personalityService,
        required this.onArtistSelected,
    });

    @override
    State<_ArtistSearchDialog> createState() => _ArtistSearchDialogState();
}

class _ArtistSearchDialogState extends State<_ArtistSearchDialog> {
    final TextEditingController _searchController = TextEditingController();

    List<SpotifyArtist> _searchResults = [];
    bool _isSearching = false;
    String _lastQuery = '';

    @override
    void dispose() {
        _searchController.dispose();
        super.dispose();
    }

    Future<void> _searchArtists(String query) async {
        if (query.isEmpty || query == _lastQuery) return;

        setState(() {
            _isSearching = true;
            _lastQuery = query;
        });

        try {
            final results = await widget.personalityService.searchArtists(query);

            if (mounted && query == _lastQuery) {
                setState(() {
                    _searchResults = results;
                    _isSearching = false;
                });
            }
        }

        catch (e) {
            if (mounted) {
                setState(() {
                    _searchResults = [];
                    _isSearching = false;
                });

                ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to search artists: $e')),
                );
            }
        }
    }

    @override
    Widget build(BuildContext context) {
        return Dialog(
            child: Container(
                width: AppConstants.dialogWidth,
                height: MediaQuery.of(context).size.height * 0.7,
                padding: const EdgeInsets.all(AppConstants.mediumPadding),

                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                            'Search Artists',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                            ),
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),
                        
                        TextField(
                            controller: _searchController,
                            decoration: InputDecoration(
                                hintText: 'Type artist name...',
                                prefixIcon: const Icon(Icons.search_rounded),

                                suffixIcon: _isSearching ? Container(
                                    width: AppConstants.mediumIconSize,
                                    height: AppConstants.mediumIconSize,
                                    padding: const EdgeInsets.all(AppConstants.smallMediumPadding),
                                    child: const CircularProgressIndicator(strokeWidth: 3),
                                )

                                : null,
                            ),

                            onChanged: (value) {
                                Future.delayed(const Duration(milliseconds: 500), () {
                                    if (_searchController.text == value) {
                                        _searchArtists(value);
                                    }
                                });
                            },

                            autofocus: true,
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),

                        Expanded(
                            child: _searchResults.isEmpty && !_isSearching ? const Center(
                                child: Text(
                                    'Start typing to search for artists',
                                    style: TextStyle(color: Colors.white54),
                                ),
                            )

                            : ListView.builder(
                                itemCount: _searchResults.length,
                                itemBuilder: (context, index) {
                                    final artist = _searchResults[index];
                                    return ListTile(
                                        leading: artist.imageUrl != null ? CircleAvatar(
                                            backgroundImage: NetworkImage(artist.imageUrl!),
                                            onBackgroundImageError: (_, __) {},
                                            child: artist.imageUrl == null ? const Icon(Icons.person_rounded) : null,
                                        )

                                        : const CircleAvatar(
                                            child: Icon(Icons.person_rounded),
                                        ),

                                        title: Text(artist.name),
                                        subtitle: artist.genres?.isNotEmpty == true ? Text(
                                            artist.genres!.take(2).join(', '),
                                            style: const TextStyle(color: Colors.white54),
                                        )

                                        : null,
                                        trailing: Text(
                                            '${artist.popularity}%',
                                            style: const TextStyle(color: Colors.white54),
                                        ),

                                        onTap: () {
                                            widget.onArtistSelected(artist);
                                            Navigator.of(context).pop();
                                        },
                                    );
                                },
                            ),
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),

                        Row(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                                TextButton(
                                    onPressed: () => Navigator.of(context).pop(),
                                    child: const Text('Cancel'),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        );
    }
}

import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/personality_service.dart';
import '../config/app_constants.dart';
import '../models/user_context.dart';

abstract class PersonalityResetCallback {
    void onResetPersonalitySettings();
}

class AdvancedSettingsSystem {
    List<String> _customFavoriteArtists = [];
    List<String> _customDislikedArtists = [];

    int _maxFavoriteArtists = 12;
    int _maxDislikedArtists = 20;

    List<String> get customFavoriteArtists => _customFavoriteArtists;
    List<String> get customDislikedArtists => _customDislikedArtists;

    int get maxFavoriteArtists => _maxFavoriteArtists;
    int get maxDislikedArtists => _maxDislikedArtists;

    void updateArtists({List<String>? favoriteArtists, List<String>? dislikedArtists}) {
        if (favoriteArtists != null) _customFavoriteArtists = favoriteArtists;
        if (dislikedArtists != null) _customDislikedArtists = dislikedArtists;
    }

    void updateLimits({int? maxFavorite, int? maxDisliked}) {
        if (maxFavorite != null) _maxFavoriteArtists = maxFavorite;
        if (maxDisliked != null) _maxDislikedArtists = maxDisliked;
    }

    void addFavoriteArtist(String artist) {
        if (!_customFavoriteArtists.contains(artist) && 
            _customFavoriteArtists.length < _maxFavoriteArtists) {
            _customFavoriteArtists.add(artist);
        }
    }

    void removeFavoriteArtist(String artist) {
        _customFavoriteArtists.remove(artist);
    }

    void addDislikedArtist(String artist) {
        if (!_customDislikedArtists.contains(artist) && 
            _customDislikedArtists.length < _maxDislikedArtists) {
            _customDislikedArtists.add(artist);
        }
    }

    void removeDislikedArtist(String artist) {
        _customDislikedArtists.remove(artist);
    }
}

mixin AdvancedSettingsMixin<T extends StatefulWidget> on State<T> {
    final AdvancedSettingsSystem _advancedSettings = AdvancedSettingsSystem();
    
    List<String> get customFavoriteArtists => _advancedSettings.customFavoriteArtists;
    List<String> get customDislikedArtists => _advancedSettings.customDislikedArtists;

    int get maxFavoriteArtists => _advancedSettings.maxFavoriteArtists;
    int get maxDislikedArtists => _advancedSettings.maxDislikedArtists;

    void updateArtistSettings({List<String>? favoriteArtists, List<String>? dislikedArtists}) {
        _advancedSettings.updateArtists(
            favoriteArtists: favoriteArtists,
            dislikedArtists: dislikedArtists,
        );

        if (mounted) {
            setState(() {});
        }
    }

    void updateArtistLimits({int? maxFavorite, int? maxDisliked}) {
        _advancedSettings.updateLimits(
            maxFavorite: maxFavorite,
            maxDisliked: maxDisliked,
        );

        if (mounted) {
            setState(() {});
        }
    }

    void addFavoriteArtist(String artist) {
        _advancedSettings.addFavoriteArtist(artist);

        if (mounted) {
            setState(() {});
        }
    }

    void removeFavoriteArtist(String artist) {
        _advancedSettings.removeFavoriteArtist(artist);

        if (mounted) {
            setState(() {});
        }
    }

    void addDislikedArtist(String artist) {
        _advancedSettings.addDislikedArtist(artist);

        if (mounted) {
            setState(() {});
        }
    }

    void removeDislikedArtist(String artist) {
        _advancedSettings.removeDislikedArtist(artist);

        if (mounted) {
            setState(() {});
        }
    }

    Future<void> showAddArtistDialog({required bool isDisliked, required Function(SpotifyArtist) onArtistSelected}) async {
        await showDialog(
            context: context,
            builder: (context) => _ArtistSearchDialog(
                personalityService: context.read<PersonalityService>(),
                onArtistSelected: onArtistSelected,
                isDisliked: isDisliked,
            ),
        );
    }
}

class _ArtistSearchDialog extends StatefulWidget {
    final PersonalityService personalityService;
    final Function(SpotifyArtist) onArtistSelected;
    final bool isDisliked;

    const _ArtistSearchDialog({
        required this.personalityService,
        required this.onArtistSelected,

        this.isDisliked = false,
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
                            widget.isDisliked ? 'Search Disliked Artists' : 'Search Artists',
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

                                        : const CircleAvatar(child: Icon(Icons.person_rounded)),
                                        title: Text(artist.name),

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

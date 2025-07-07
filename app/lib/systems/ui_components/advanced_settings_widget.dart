import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../services/personality_service.dart';
import '../../services/message_service.dart';
import '../advanced_settings_system.dart';
import '../../config/app_constants.dart';
import '../../models/user_context.dart';

import 'artist_selector.dart';

class AdvancedSettingsWidget extends StatefulWidget {
    final Function(UserContext) onSave;

    final List<String>? initialFavoriteArtists;
    final List<String>? initialDislikedArtists;

    final VoidCallback? onDataChanged;
    final VoidCallback? onResetAllSettings;

    const AdvancedSettingsWidget({
        super.key,
        required this.onSave,
        this.initialFavoriteArtists,
        this.initialDislikedArtists,
        this.onDataChanged,
        this.onResetAllSettings,
    });

    @override
    State<AdvancedSettingsWidget> createState() => _AdvancedSettingsWidgetState();
}

class _AdvancedSettingsWidgetState extends State<AdvancedSettingsWidget> with AdvancedSettingsMixin {

    @override
    void initState() {
        super.initState();

        if (widget.initialFavoriteArtists != null || widget.initialDislikedArtists != null) {
            updateArtistSettings(
                favoriteArtists: widget.initialFavoriteArtists ?? [],
                dislikedArtists: widget.initialDislikedArtists ?? [],
            );
        }
    }

    @override
    Widget build(BuildContext context) {
        return SingleChildScrollView(
            padding: const EdgeInsets.all(AppConstants.largePadding),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                    _buildSectionHeader('Custom Artist Management', 'Manage your preferred and disliked artists'),
                    const SizedBox(height: AppConstants.largeSpacing),

                    _buildCustomFavoriteArtists(),
                    const SizedBox(height: AppConstants.largeSpacing),

                    _buildCustomDislikedArtists(),
                    const SizedBox(height: AppConstants.largeSpacing),

                    _buildSectionHeader('Advanced Settings', 'Settings for power users'),
                    const SizedBox(height: AppConstants.largeSpacing),

                    _buildAdvancedControls(),
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

    Widget _buildCustomFavoriteArtists() {
        return Card(
            child: Padding(
                padding: const EdgeInsets.all(AppConstants.mediumPadding),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                            'Custom Favorite Artists (${customFavoriteArtists.length}/$maxFavoriteArtists)',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                            ),
                        ),

                        const SizedBox(height: AppConstants.smallSpacing),
                        Text(
                            'Add artists you love that might not be in your Spotify followed list',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.white70,
                            ),
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),
                        ArtistSelector(
                            selectedArtists: customFavoriteArtists,
                            maxArtists: maxFavoriteArtists,
                            label: 'Custom Favorite Artists',

                            onRemove: (artist) {
                                removeFavoriteArtist(artist);
                                _saveSettings();
                            },
                            onAdd: () => _showAddFavoriteArtistDialog(),
                        ),
                    ],
                ),
            ),
        );
    }

    Widget _buildCustomDislikedArtists() {
        return Card(
            child: Padding(
                padding: const EdgeInsets.all(AppConstants.mediumPadding),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                            'Disliked Artists (${customDislikedArtists.length}/$maxDislikedArtists)',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                            ),
                        ),

                        const SizedBox(height: AppConstants.smallSpacing),
                        Text(
                            'Artists to exclude from generated playlists',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.white70,
                            ),
                        ),

                        const SizedBox(height: AppConstants.mediumSpacing),
                        ArtistSelector(
                            selectedArtists: customDislikedArtists,
                            maxArtists: maxDislikedArtists,
                            label: 'Disliked Artists',
                            isDisliked: true,

                            onRemove: (artist) {
                                removeDislikedArtist(artist);
                                _saveSettings();
                            },
                            onAdd: () => _showAddDislikedArtistDialog(),
                        ),
                    ],
                ),
            ),
        );
    }

    Widget _buildAdvancedControls() {
        return Card(
            child: Padding(
                padding: const EdgeInsets.all(AppConstants.mediumPadding),
                child: Column(
                    children: [
                        ListTile(
                            leading: const Icon(Icons.delete_outline_rounded, color: Colors.red),
                            title: const Text('Reset All Settings', style: TextStyle(color: Colors.red)),
                            subtitle: const Text('Clear all saved preferences and start fresh'),
                            trailing: const Icon(Icons.arrow_forward_ios_rounded, color: Colors.red),
                            onTap: _showResetDialog,
                        ),
                    ],
                ),
            ),
        );
    }

    void _showAddFavoriteArtistDialog() {
        showAddArtistDialog(
            isDisliked: false,
            onArtistSelected: (artist) {
                addFavoriteArtist(artist.name);
                _saveSettings();
            },
        );
    }

    void _showAddDislikedArtistDialog() {
        showAddArtistDialog(
            isDisliked: true,
            onArtistSelected: (artist) {
                addDislikedArtist(artist.name);
                _saveSettings();
            },
        );
    }

    void _saveSettings() {
        try {
            final context = UserContext(
                favoriteArtists: customFavoriteArtists,
                dislikedArtists: customDislikedArtists,
            );
            widget.onSave(context);
        }

        catch (e) {
            if (mounted) {
                MessageService.showError(context, 'Failed to save settings');
            }
        }
    }

    void _showResetDialog() {
        showDialog(
            context: context,
            builder: (dialogContext) => AlertDialog(
                title: const Text('Reset All Settings'),
                content: const Text('This will clear all your saved preferences, including favorite artists, genres, and personality answers. This action cannot be undone.'),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(dialogContext).pop(),
                        child: const Text('Cancel'),
                    ),

                    FilledButton(
                        onPressed: () async {
                            Navigator.of(dialogContext).pop();
                            await _resetAllSettings();
                        },

                        style: FilledButton.styleFrom(backgroundColor: Colors.red),
                        child: const Text('Reset'),
                    ),
                ],
            ),
        );
    }

    Future<void> _resetAllSettings() async {
        try {
            final personalityService = context.read<PersonalityService>();
            await personalityService.clearUserContext();

            updateArtistSettings(
                favoriteArtists: [],
                dislikedArtists: [],
            );

            if (widget.onResetAllSettings != null) {
                widget.onResetAllSettings!();
            }

            else if (widget.onDataChanged != null) {
                widget.onDataChanged!();
            }

            if (mounted) MessageService.showSuccess(context, 'All settings reset successfully');
        }

        catch (e) {
            if (mounted) MessageService.showError(context, 'Failed to reset settings');
        }
    }
}

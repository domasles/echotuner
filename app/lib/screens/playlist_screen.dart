import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../providers/playlist_provider.dart';
import '../services/message_service.dart';
import '../services/auth_service.dart';
import '../config/app_constants.dart';
import '../config/app_colors.dart';
import '../utils/app_logger.dart';

class PlaylistScreen extends StatefulWidget {
    const PlaylistScreen({super.key});

    @override
    State<PlaylistScreen> createState() => _PlaylistScreenState();
}

class _PlaylistScreenState extends State<PlaylistScreen> {

    Future<void> _openSpotifyTrack(String spotifyId) async {
        final spotifyUrl = 'https://open.spotify.com/track/$spotifyId';

        try {
            if (await canLaunchUrl(Uri.parse(spotifyUrl))) {
                await launchUrl(
                    Uri.parse(spotifyUrl),
                    mode: LaunchMode.externalApplication,
                );
            }
        }

        catch (e, stackTrace) {
            AppLogger.error('Failed to launch Spotify URL', error: e, stackTrace: stackTrace);
        }
    }

    Future<void> _showRefineDialog(BuildContext context, PlaylistProvider provider) async {
        String refinementText = '';

        return showDialog<void>(
            context: context,
            builder: (BuildContext dialogContext) {
                return AlertDialog(
                    backgroundColor: AppColors.surface,
                    title: const Text(
                        'Refine Your Playlist',
                        style: TextStyle(color: AppColors.textPrimary),
                    ),

                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                            _buildRefinementIndicatorForDialog(provider),
                            const SizedBox(height: AppConstants.mediumSpacing),

                            TextField(
                                autofocus: true,
                                maxLines: 3,

                                decoration: const InputDecoration(
                                    hintText: 'Tell us how you\'d like to adjust your playlist',
                                    border: OutlineInputBorder(),
                                ),

                                onChanged: (value) => refinementText = value,
                            ),
                        ],
                    ),

                    actions: [
                        TextButton(
                            onPressed: () => Navigator.of(dialogContext).pop(),
                            child: const Text('Cancel'),
                        ),

                        FilledButton(
                            onPressed: () {
                                if (refinementText.trim().isNotEmpty) {
                                    Navigator.of(dialogContext).pop();
                                    provider.refinePlaylist(refinementText.trim());
                                }
                            },

                            child: const Text('Refine'),
                        ),
                    ],
                );
            },
        );
    }

    Future<void> _showAddToSpotifyDialog(BuildContext context, PlaylistProvider provider) async {
        if (provider.isPlaylistAddedToSpotify && provider.spotifyPlaylistInfo != null) {
            await _updateSpotifyPlaylist(context, provider);
            return;
        }

        String playlistName = '';
        String description = '';

        return showDialog<void>(
            context: context,
            builder: (BuildContext dialogContext) {
                return AlertDialog(
                    backgroundColor: AppColors.surface,
                    title: const Text(
                        'Add to Spotify',
                        style: TextStyle(color: AppColors.textPrimary),
                    ),

                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                            TextField(
                                autofocus: true,
                                decoration: const InputDecoration(
                                    hintText: 'Playlist name',
                                    border: OutlineInputBorder(),
                                ),

                                onChanged: (value) => playlistName = value,
                            ),

                            const SizedBox(height: AppConstants.mediumSpacing),
                            TextField(
                                maxLines: 2,
                                textAlignVertical: TextAlignVertical.top,

                                decoration: const InputDecoration(
                                    hintText: 'Description (optional)',
                                    border: OutlineInputBorder(),
                                    alignLabelWithHint: true,
                                ),

                                onChanged: (value) => description = value,
                            ),
                        ],
                    ),

                    actions: [
                        TextButton(
                            onPressed: () => Navigator.of(dialogContext).pop(),
                            child: const Text('Cancel'),
                        ),

                        FilledButton(
                            onPressed: () async {
                                if (playlistName.trim().isNotEmpty) {
                                    Navigator.of(dialogContext).pop();

                                    try {
                                        final isUpdate = provider.isPlaylistAddedToSpotify;

                                        await provider.addToSpotify(
                                            playlistName: playlistName.trim(),
                                            description: description.trim().isEmpty ? null : description.trim(),
                                        );

                                        if (context.mounted) {
                                            Navigator.of(context).pop();
                                            MessageService.showSuccess(context, isUpdate ? 'Playlist updated on Spotify successfully!' : 'Playlist added to Spotify successfully!');
                                        }
                                    }

                                    catch (e) {
                                        if (context.mounted) {
                                            Navigator.of(context).pop();
                                            MessageService.showError(context, provider.isPlaylistAddedToSpotify ? 'Failed to update playlist: $e' : 'Failed to add playlist: $e');
                                        }
                                    }
                                }
                            },

                            child: Text('Add to Spotify'),
                        ),
                    ],
                );
            },
        );
    }

    Future<void> _updateSpotifyPlaylist(BuildContext context, PlaylistProvider provider) async {
        try {
            final spotifyInfo = provider.spotifyPlaylistInfo!;

            await provider.addToSpotify(
                playlistName: spotifyInfo.name, 
                description: spotifyInfo.description,
            );

            if (context.mounted) {
                Navigator.of(context).pop();
                MessageService.showSuccess(context, 'Playlist updated on Spotify successfully!');
            }
        }

        catch (e) {
            if (context.mounted) {
                Navigator.of(context).pop();
                MessageService.showError(context, 'Failed to update playlist: $e');
            }
        }
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Your Playlist'),
                centerTitle: true,
            ),

            body: Consumer<PlaylistProvider>(
                builder: (context, provider, child) {
                    if (provider.isLoading) {
                        return const Center(
                            child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                    CircularProgressIndicator(),
                                    SizedBox(height: AppConstants.mediumSpacing),
                                    Text('Generating your playlist...'),
                                ],
                            ),
                        );
                    }

                    if (provider.error != null) {
                        return Center(
                            child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                    const Icon(Icons.error, size: AppConstants.largeIconSize, color: AppColors.errorIcon),
                                    const SizedBox(height: AppConstants.mediumSpacing),

                                    Text(
                                        'Error: ${provider.error}',
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(color: AppColors.errorIcon),
                                    ),

                                    const SizedBox(height: AppConstants.mediumSpacing),
                                    FilledButton(
                                        onPressed: () => Navigator.pop(context),
                                        child: const Text('Go Back'),
                                    ),
                                ],
                            ),
                        );
                    }

                    if (provider.currentPlaylist.isEmpty) {
                        return const Center(
                            child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                    Icon(Icons.music_note, size: AppConstants.largeIconSize, color: AppColors.grey),
                                    SizedBox(height: AppConstants.mediumSpacing),

                                    Text(
                                        'No playlist generated yet',
                                        style: TextStyle(color: AppColors.grey),
                                    ),
                                ],
                            ),
                        );
                    }

                    return _buildPlaylistContent(context, provider);
                },
            ),

            bottomNavigationBar: Consumer<PlaylistProvider>(
                builder: (context, provider, child) {
                    return _buildBottomRefineButton(context, provider);
                },
            ),
        );
    }

    Widget _buildPlaylistContent(BuildContext context, PlaylistProvider provider) {
        return Column(
            children: [
                if (provider.currentPrompt.isNotEmpty) Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppConstants.mediumSpacing),
                    margin: const EdgeInsets.all(AppConstants.mediumSpacing),

                    decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(AppConstants.mediumRadius),

                        border: Border.all(
                            color: AppColors.surfaceVariant,  
                            width: 1,
                        ),
                    ),

                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                            const Text(
                                'Generated for:',
                                style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: AppConstants.smallFontSize,
                                ),
                            ),

                            const SizedBox(height: AppConstants.tinySpacing),
                            Text(
                                provider.currentPrompt,
                                style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontWeight: FontWeight.bold,
                                ),
                            ),
                        ],
                    ),
                ),

                Expanded(
                    child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: provider.currentPlaylist.length,

                        itemBuilder: (context, index) {
                            final song = provider.currentPlaylist[index];

                            return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                child: ListTile(
                                    leading: const Icon(Icons.music_note),
                                    title: Text(
                                        song.title,
                                        style: const TextStyle(
                                            color: AppColors.textPrimary,
                                            fontWeight: FontWeight.bold,
                                        ),
                                    ),

                                    subtitle: Text(
                                        song.artist,
                                        style: const TextStyle(color: AppColors.textSecondary),
                                    ),

                                    trailing: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                            IconButton(
                                                icon: const Icon(Icons.delete, color: Colors.red),
                                                onPressed: () => _removeSong(context, index),
                                                tooltip: 'Remove song',
                                            ),

                                            if (song.spotifyId != null)
                                                IconButton(
                                                    icon: const Icon(Icons.open_in_new),
                                                    onPressed: () => _openSpotifyTrack(song.spotifyId!),
                                                    tooltip: 'Open in Spotify',
                                                ),
                                        ],
                                    ),
                                ),
                            );
                        },
                    ),
                ),
            ],
        );
    }

    Widget _buildBottomRefineButton(BuildContext context, PlaylistProvider provider) {
        if (provider.currentPlaylist.isEmpty) {
            return const SizedBox.shrink();
        }

        return BottomAppBar(
            height: 88,
            color: AppColors.background,

            child: Padding(
                padding: const EdgeInsets.all(4),
                child: Row(
                    children: [
                        Expanded(
                            child: FilledButton(
                                onPressed: provider.isAddingToSpotify ? null : () => _showAddToSpotifyDialog(context, provider),
                                style: const ButtonStyle(
                                    side: WidgetStatePropertyAll(BorderSide(color: AppColors.surfaceVariant, width: 0.5)),
                                    elevation: WidgetStatePropertyAll(0),
                                    shadowColor: WidgetStatePropertyAll(AppColors.transparent),
                                    minimumSize: WidgetStatePropertyAll(Size.fromHeight(48)),
                                ),

                                child: provider.isAddingToSpotify ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                )

                                : Text('Add to Spotify'),
                            ),
                        ),

                        const SizedBox(width: AppConstants.smallSpacing),

                        if (provider.canRefine) Expanded(
                            child: FilledButton(
                                onPressed: () => _showRefineDialog(context, provider),
                                style: const ButtonStyle(
                                    side: WidgetStatePropertyAll(BorderSide(color: AppColors.surfaceVariant, width: 0.5)),
                                    elevation: WidgetStatePropertyAll(0),
                                    shadowColor: WidgetStatePropertyAll(AppColors.transparent),
                                    minimumSize: WidgetStatePropertyAll(Size.fromHeight(48)),
                                ),

                                child: Text(
                                    provider.showRefinementLimits ? 'Refine (${(provider.rateLimitStatus?.maxRefinements ?? 3) - provider.refinementsUsed} left)' : 'Refine',
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        );
    }

    Widget _buildRefinementIndicatorForDialog(PlaylistProvider provider) {
        if (!provider.showRefinementLimits) return const SizedBox.shrink();
        final rateLimitStatus = provider.rateLimitStatus;
        if (rateLimitStatus == null) return const SizedBox.shrink();

        final refinementsUsed = provider.refinementsUsed;
        final maxRefinements = rateLimitStatus.maxRefinements;
        final progress = maxRefinements > 0 ? refinementsUsed / maxRefinements : 0.0;

        Color progressColor;

        if (progress <= 0.5) {
            progressColor = AppColors.progressBlue;
        }

        else if (progress <= 0.8) {
            progressColor = AppColors.progressOrange;
        }

        else {
            progressColor = AppColors.progressRed;
        }

        return Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(AppConstants.mediumRadius),

                border: Border.all(
                    color: AppColors.surfaceVariant, 
                    width: 1,
                ),
            ),

            child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                    Text(
                        refinementsUsed >= maxRefinements ? 'Refinement limit reached' : 'Refinements Used: $refinementsUsed/$maxRefinements',
                        style: TextStyle(
                            color: progressColor,
                            fontSize: AppConstants.smallFontSize,
                            fontWeight: FontWeight.bold,
                        ),
                    ),

                    const SizedBox(height: AppConstants.tinySpacing),
                    Container(
                        height: 4,
                        decoration: BoxDecoration(
                            color: const Color(0xFF2A2A2A),
                            borderRadius: BorderRadius.circular(AppConstants.tinyRadius),
                        ),

                        child: ClipRRect(
                            borderRadius: BorderRadius.circular(AppConstants.tinyRadius),
                            child: LinearProgressIndicator(
                                value: progress,
                                backgroundColor: Colors.transparent,
                                valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                            ),
                        ),
                    ),
                ],
            ),
        );
    }

    Future<void> _removeSong(BuildContext context, int index) async {
        final provider = Provider.of<PlaylistProvider>(context, listen: false);
        final authService = Provider.of<AuthService>(context, listen: false);
        final currentPlaylist = provider.currentPlaylist;

        if (currentPlaylist.isEmpty || index >= currentPlaylist.length) return;
        final song = currentPlaylist[index];

        final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: AppColors.surface,
                title: const Text(
                    'Remove Song',
                    style: TextStyle(color: AppColors.textPrimary),
                ),

                content: Text(
                    'Remove "${song.title}" from the playlist?',
                    style: const TextStyle(color: AppColors.textSecondary),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('Cancel'),
                    ),

                    TextButton(
                        onPressed: () => Navigator.of(context).pop(true),
                        child: const Text(
                            'Remove',
                            style: TextStyle(color: Colors.red),
                        ),
                    ),
                ],
            ),
        );

        if (confirmed == true && context.mounted) {
            provider.removeSong(song);

            if (provider.isPlaylistAddedToSpotify && provider.currentPlaylistId != null && authService.sessionId != null && authService.deviceId != null && song.uri.isNotEmpty) {
                try {
                    final success = await provider.removeSongFromSpotifyPlaylist(
                        provider.currentPlaylistId!,
                        song.uri,
                        authService.sessionId!,
                        authService.deviceId!,
                    );

                    if (success && context.mounted) {
                        MessageService.showSuccess(context, 'Song removed from playlist and Spotify');
                    }

                    else if (context.mounted) {
                        MessageService.showWarning(context, 'Song removed locally but failed to remove from Spotify');
                    }
                }

                catch (e) {
                    if (context.mounted) {
                        MessageService.showWarning(context, 'Song removed locally but failed to remove from Spotify');
                    }
                }
            }

            else if (context.mounted) {
                MessageService.showSuccess(context, 'Song removed from playlist');
            }
        }
    }
}

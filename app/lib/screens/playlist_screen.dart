import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../providers/playlist_provider.dart';

class PlaylistScreen extends StatelessWidget {
    const PlaylistScreen({super.key});

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
            debugPrint('Failed to launch Spotify URL: $e');
            debugPrint('Stack trace: $stackTrace');
        }
    }

    Future<void> _showRefineDialog(BuildContext context, PlaylistProvider provider) async {
        String refinementText = '';
        
        return showDialog<void>(
            context: context,
            builder: (BuildContext context) {
                return AlertDialog(
                    backgroundColor: const Color(0xFF1A1625),
                    title: const Text(
                        'Refine Your Playlist',
                        style: TextStyle(color: Colors.white),
                    ),

                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                            const SizedBox(height: 16),
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
                            onPressed: () => Navigator.of(context).pop(),
                            child: const Text('Cancel'),
                        ),

                        ElevatedButton(
                            onPressed: () {
                                if (refinementText.trim().isNotEmpty) {
                                    Navigator.of(context).pop();
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
                                    SizedBox(height: 16),
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
                                    const Icon(Icons.error, size: 64, color: Colors.red),
                                    const SizedBox(height: 16),

                                    Text(
                                        'Error: ${provider.error}',
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(color: Colors.red),
                                    ),

                                    const SizedBox(height: 16),
                                    ElevatedButton(
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
                                    Icon(Icons.music_note, size: 64, color: Colors.grey),
                                    SizedBox(height: 16),

                                    Text(
                                        'No playlist generated yet',
                                        style: TextStyle(color: Colors.grey),
                                    ),
                                ],
                            ),
                        );
                    }

                    return Stack(
                        children: [
                            Column(
                                children: [
                                    Expanded(
                                        child: _buildPlaylistContent(context, provider),
                                    ),
                                ],
                            ),

                            _buildBottomRefinementIndicator(provider),
                        ],
                    );
                },
            ),
        );
    }

    Widget _buildPlaylistContent(BuildContext context, PlaylistProvider provider) {
        return Column(
            children: [
                if (provider.currentPrompt.isNotEmpty) Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    margin: const EdgeInsets.all(16),

                    decoration: BoxDecoration(
                        color: const Color(0xFF1E1E1E),
                        borderRadius: BorderRadius.circular(12),
                    ),
                    
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                            const Text(
                                'Generated for:',
                                style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                ),
                            ),

                            const SizedBox(height: 4),
                            Text(
                                provider.currentPrompt,
                                style: const TextStyle(
                                    color: Colors.white,
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
                                            color: Colors.white,
                                            fontWeight: FontWeight.bold,
                                        ),
                                    ),

                                    subtitle: Text(
                                        song.artist,
                                        style: const TextStyle(color: Colors.white70),
                                    ),

                                    trailing: song.spotifyId != null ? IconButton(
                                        icon: const Icon(Icons.open_in_new),
                                        onPressed: () => _openSpotifyTrack(song.spotifyId!),
                                    )

                                    : null,
                                ),
                            );
                        },
                    ),
                ),

                if (provider.canRefine) Padding(
                    padding: const EdgeInsets.all(16),
                    child: ElevatedButton(
                        onPressed: () => _showRefineDialog(context, provider),
                        child: Text(
                            provider.showRefinementLimits ? 'Refine Playlist (${(provider.rateLimitStatus?.maxRefinements ?? 3) - provider.refinementsUsed} left)' : 'Refine Playlist',
                        ),
                    ),
                ),
            ],
        );
    }

    Widget _buildBottomRefinementIndicator(PlaylistProvider provider) {
        if (!provider.showRefinementLimits) {
            return const SizedBox.shrink();
        }
        
        final rateLimitStatus = provider.rateLimitStatus;

        if (rateLimitStatus == null) {
            return const SizedBox.shrink();
        }
        
        final refinementsUsed = provider.refinementsUsed;
        final maxRefinements = rateLimitStatus.maxRefinements;
        final progress = maxRefinements > 0 ? refinementsUsed / maxRefinements : 0.0;
        
        Color progressColor;

        if (progress <= 0.5) {
            progressColor = Colors.blue;
        }
		
		else if (progress <= 0.8) {
            progressColor = Colors.orange;
        }
		
		else {
            progressColor = Colors.red;
        }
        
        return Positioned(
            left: 16,
            right: 16,
            bottom: 16,

            child: Container(
                height: 56, // Same consistent height
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),

                decoration: BoxDecoration(
                    color: const Color(0xFF1A1625),
                    borderRadius: BorderRadius.circular(28), // Half of height for pill shape
                    border: Border.all(
                        color: const Color(0xFF2A2635),
                        width: 1,
                    ),

                    boxShadow: [
                        BoxShadow(
                            color: Colors.black.withValues(alpha: 255 * 0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 4),
                        ),
                    ],
                ),

                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                        Text(
                            refinementsUsed >= maxRefinements ? 'Refinement limit reached' : 'Refinements Used: $refinementsUsed/$maxRefinements',
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
                                    backgroundColor: Colors.transparent,
                                    valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        );
    }
}

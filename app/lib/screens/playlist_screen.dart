import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

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
                            const Text(
                                'Tell us how you\'d like to adjust your playlist:',
                                style: TextStyle(color: Colors.white70),
                            ),

                            const SizedBox(height: 16),
                            TextField(
                                autofocus: true,
                                maxLines: 3,

                                decoration: const InputDecoration(
                                    hintText: 'e.g., "Add more upbeat songs", "Include more 80s music", "Remove slow songs"',
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
                                        'Refine Playlist (${3 - provider.refinementsUsed} left)',
                                    ),
                                ),
                            ),
                        ],
                    );
                },
            ),
        );
    }
}

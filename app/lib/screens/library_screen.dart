import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/playlist_provider.dart';
import '../models/playlist_draft_models.dart';
import 'playlist_screen.dart';

class LibraryScreen extends StatefulWidget {
    const LibraryScreen({super.key});

    @override
    State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> with TickerProviderStateMixin {
    List<PlaylistDraft> _drafts = [];
    List<SpotifyPlaylistInfo> _spotifyPlaylists = [];

    bool _isLoading = true;
    String? _error;

    late TabController _tabController;

    @override
    void initState() {
        super.initState();
        _tabController = TabController(length: 2, vsync: this);
        _loadLibrary();
    }

    @override
    void dispose() {
        _tabController.dispose();
        super.dispose();
    }

    Future<void> _loadLibrary() async {
        setState(() {
            _isLoading = true;
            _error = null;
        });

        try {
            final provider = Provider.of<PlaylistProvider>(context, listen: false);
            final response = await provider.getLibraryPlaylists();
            
            setState(() {
                _drafts = response.drafts;
                _spotifyPlaylists = response.spotifyPlaylists;
                _isLoading = false;
            });
        }
		
		catch (e) {
            setState(() {
                _error = e.toString();
                _isLoading = false;
            });
        }
    }

    Future<void> _openDraft(PlaylistDraft draft) async {
        final provider = Provider.of<PlaylistProvider>(context, listen: false);
        
        try {
            await provider.loadDraft(draft);
            if (mounted) {
                await Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const PlaylistScreen()),
                );

                _loadLibrary();
            }
        }
		
		catch (e) {
            if (mounted) {
                _showCustomSnackbar(
                    context,
                    'Failed to load draft: $e',
                    isError: true,
                );
            }
        }
    }

    Future<void> _deleteDraft(PlaylistDraft draft) async {
        final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text('Delete Draft', style: TextStyle(color: Colors.white)),

                content: const Text(
                    'Are you sure you want to delete this draft? This action cannot be undone.',
                    style: TextStyle(color: Colors.white70),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('Cancel'),
                    ),

                    TextButton(
                        onPressed: () => Navigator.of(context).pop(true),
                        child: const Text('Delete', style: TextStyle(color: Colors.red)),
                    ),
                ],
            ),
        );

        if (confirmed == true) {
            try {
                final provider = Provider.of<PlaylistProvider>(context, listen: false);
                await provider.deleteDraft(draft.id);

                _loadLibrary();
                
                if (mounted) {
                    _showCustomSnackbar(context, 'Draft deleted successfully');
                }
            }
			
			catch (e) {
                if (mounted) {
                    _showCustomSnackbar(context, 'Failed to delete draft: $e', isError: true);
                }
            }
        }
    }



    Future<void> _deleteSpotifyPlaylist(SpotifyPlaylistInfo playlist) async {
        final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
                title: const Text('Delete Playlist'),
                content: Text('Are you sure you want to delete "${playlist.name}" from Spotify? This action cannot be undone.'),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        child: const Text('Cancel'),
                    ),

                    TextButton(
                        onPressed: () => Navigator.of(context).pop(true),
                        child: const Text('Delete', style: TextStyle(color: Colors.red)),
                    ),
                ],
            ),
        );

        if (confirmed == true) {
            try {
                final provider = Provider.of<PlaylistProvider>(context, listen: false);
                await provider.deleteSpotifyPlaylist(playlist.id);

                _loadLibrary();
                
                if (mounted) {
                    _showCustomSnackbar(context, 'Playlist deleted successfully');
                }
            }
			
			catch (e) {
                if (mounted) {
                    _showCustomSnackbar(context, 'Failed to delete playlist: $e', isError: true);
                }
            }
        }
    }



    void _showCustomSnackbar(BuildContext context, String message, {bool isError = false, bool isSuccess = false}) {
        Color borderColor;
        if (isSuccess) {
            borderColor = Color(0xFF4CAF50);
        }
		
		else if (isError) {
            borderColor = Color(0xFFD32F2F);
        }
		
		else {
            borderColor = Color(0xFF666666);
        }

        final overlay = Overlay.of(context);
        late OverlayEntry overlayEntry;
        
        overlayEntry = OverlayEntry(
            builder: (context) => Positioned(
                bottom: 16,
                left: 16,
                right: 16,

                child: Material(
                    elevation: 0,
                    color: Colors.transparent,

                    child: Container(
                        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                            color: Color(0xFF1A1625),
                            borderRadius: BorderRadius.circular(28),
                            border: Border.all(color: borderColor, width: 1),
                        ),

                        child: Text(
                            message,
                            style: TextStyle(color: Colors.white),
                        ),
                    ),
                ),
            ),
        );
        
        overlay.insert(overlayEntry);

        Future.delayed(Duration(seconds: 2), () {
            overlayEntry.remove();
        });
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Your Library'),
                centerTitle: true,

                actions: [
                    IconButton(
                        icon: const Icon(Icons.refresh),
                        onPressed: _loadLibrary,
                    ),
                ],
            ),

            body: _isLoading ? const Center(child: CircularProgressIndicator()) : _error != null ? Center(
				child: Column(
					mainAxisAlignment: MainAxisAlignment.center,
					children: [
						const Icon(Icons.error, size: 64, color: Colors.red),
						const SizedBox(height: 16),

						Text(
							'Error: $_error',
							textAlign: TextAlign.center,
							style: const TextStyle(color: Colors.red),
						),

						const SizedBox(height: 16),
						FilledButton(
							onPressed: _loadLibrary,
							child: const Text('Retry'),
						),
					],
				),
			)

			: _buildLibraryContent(),
        );
    }

    Widget _buildLibraryContent() {
        return Column(
            children: [
                TabBar(
                    controller: _tabController,
                    tabs: const [
                        Tab(text: 'Drafts'),
                        Tab(text: 'Spotify'),
                    ],
                ),

                Expanded(
                    child: TabBarView(
                        controller: _tabController,
                        children: [
                            _buildDraftsTab(),
                            _buildSpotifyTab(),
                        ],
                    ),
                ),
            ],
        );
    }

    Widget _buildDraftsTab() {
        if (_drafts.isEmpty) {
            return const Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        Icon(Icons.music_note, size: 64, color: Colors.grey),
                        SizedBox(height: 16),

                        Text(
                            'No draft playlists yet',
                            style: TextStyle(color: Colors.grey),
                        ),

                        SizedBox(height: 8),
                        Text(
                            'Create a playlist from the home screen to see it here',
                            style: TextStyle(color: Colors.grey, fontSize: 12),
                            textAlign: TextAlign.center,
                        ),
                    ],
                ),
            );
        }

        return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _drafts.length,

            itemBuilder: (context, index) {
                final draft = _drafts[index];
                return _buildDraftCard(draft);
            },
        );
    }

    Widget _buildDraftCard(PlaylistDraft draft) {
        return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
                leading: CircleAvatar(
                    backgroundColor: draft.isDraft ? Colors.orange : Colors.green,
                    child: Icon(
                        draft.isDraft ? Icons.edit : Icons.check,
                        color: Colors.white,
                    ),
                ),

                title: Text(
                    draft.prompt,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                    ),

                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                ),

                subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                            '${draft.songs.length} songs • ${draft.refinementsUsed} refinements',
                            style: const TextStyle(color: Colors.white70),
                        ),

                        Text(
                            draft.isDraft ? 'Draft' : 'Added to Spotify',
                            style: TextStyle(
                                color: draft.isDraft ? Colors.orange : Colors.green,
                                fontSize: 12,
                            ),
                        ),
                    ],
                ),
				
                trailing: draft.isDraft 
                    ? PopupMenuButton<String>(
                        onSelected: (value) {
                            switch (value) {
                                case 'open':
                                    _openDraft(draft);
                                    break;

                                case 'delete':
                                    _deleteDraft(draft);
                                    break;
                            }
                        },

                        itemBuilder: (context) => [
                            const PopupMenuItem(
                                value: 'open',
                                child: Text('Open'),
                            ),

                            const PopupMenuItem(
                                value: 'delete',
                                child: Text('Delete'),
                            ),
                        ],
                    )

                    : IconButton(
                        icon: const Icon(Icons.open_in_new),
                        onPressed: () {
                            // Open Spotify playlist if URL is available
                        },
                    ),

                onTap: () => _openDraft(draft),
            ),
        );
    }

    Widget _buildSpotifyTab() {
        if (_spotifyPlaylists.isEmpty) {
            return const Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        Icon(Icons.library_music, size: 64, color: Colors.grey),
                        SizedBox(height: 16),

                        Text(
                            'No Spotify playlists found',
                            style: TextStyle(color: Colors.grey),
                        ),

                        SizedBox(height: 8),
                        Text(
                            'Your Spotify playlists will appear here',
                            style: TextStyle(color: Colors.grey, fontSize: 12),
                            textAlign: TextAlign.center,
                        ),
                    ],
                ),
            );
        }

        return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _spotifyPlaylists.length,

            itemBuilder: (context, index) {
                final playlist = _spotifyPlaylists[index];
                return _buildSpotifyCard(playlist);
            },
        );
    }

    Widget _buildSpotifyCard(SpotifyPlaylistInfo playlist) {
        return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
                leading: const CircleAvatar(
                    backgroundColor: Colors.green,
                    child: Icon(Icons.library_music, color: Colors.white),
                ),

                title: Text(
                    playlist.name,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                    ),
                ),

                subtitle: Text(
                    '${playlist.tracksCount} tracks',
                    style: const TextStyle(color: Colors.white70),
                ),

                trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                        IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deleteSpotifyPlaylist(playlist),
                        ),

                        IconButton(
                            icon: const Icon(Icons.open_in_new),
                            onPressed: () async {
                                final url = playlist.spotifyUrl;
								
                                if (url != null && await canLaunchUrl(Uri.parse(url))) {
                                    await launchUrl(
                                        Uri.parse(url),
                                        mode: LaunchMode.externalApplication,
                                    );
                                }
                            },
                        ),
                    ],
                ),

                onTap: null, // No tap action for Spotify playlists
            ),
        );
    }
}

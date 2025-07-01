import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../systems/library_management_system.dart';
import '../systems/tab_management_system.dart';
import '../models/playlist_draft_models.dart';
import '../providers/playlist_provider.dart';
import '../services/message_service.dart';
import '../config/app_constants.dart';
import '../config/app_colors.dart';

import 'playlist_screen.dart';

class LibraryScreen extends StatefulWidget {
    const LibraryScreen({super.key});

    @override
    State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> with TickerProviderStateMixin, WidgetsBindingObserver {
    final TabManagementSystem _tabSystem = TabManagementSystem();
    final LibraryManagementSystem _librarySystem = LibraryManagementSystem();
    
    TabController? get tabController => _tabSystem.tabController;
    
    List<PlaylistDraft> get drafts => _librarySystem.drafts;
    List<SpotifyPlaylistInfo> get spotifyPlaylists => _librarySystem.spotifyPlaylists;
    bool get isLibraryLoading => _librarySystem.isLoading;
    String? get libraryError => _librarySystem.error;

    @override
    void initState() {
        super.initState();
        
        _tabSystem.initialize(
            tabCount: 2,
            vsync: this,
            onTabChanged: _silentRefreshCurrentTab,
            showTabsDuringLoading: true,
        );
        
        loadLibraryData();
    }

    @override
    void didChangeDependencies() {
        super.didChangeDependencies();
    }

    @override
    void dispose() {
        _tabSystem.dispose();
        super.dispose();
    }

    Future<void> loadLibraryData() async {
        await _librarySystem.loadLibraryData(context);
        if (mounted) {
            setState(() {});
        }
    }

    Future<void> silentRefreshLibrary() async {
        await _librarySystem.silentRefresh(context);
        if (mounted) {
            setState(() {});
        }
    }

    Future<void> _silentRefreshCurrentTab() async {
        if (!mounted) return;
        await silentRefreshLibrary();
    }

    void refreshCurrentTab() {
        _silentRefreshCurrentTab();
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

                _silentRefreshCurrentTab();
            }
        }

        catch (e) {
            if (mounted) {
                MessageService.showError(
                    context,
                    'Failed to load draft: $e',
                );
            }
        }
    }

    Future<void> _deleteDraft(PlaylistDraft draft) async {
        final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text('Delete Draft', style: TextStyle(color: AppColors.textPrimary)),

                content: const Text(
                    'Are you sure you want to delete this draft? This action cannot be undone.',
                    style: TextStyle(color: AppColors.textSecondary),
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
            if (!mounted) return;
            final provider = Provider.of<PlaylistProvider>(context, listen: false);

            try {
                await provider.deleteDraft(draft.id);
                _silentRefreshCurrentTab();

                if (mounted) {
                    MessageService.showInfo(context, 'Draft deleted successfully');
                }
            }

            catch (e) {
                if (mounted) {
                    MessageService.showError(context, 'Failed to delete draft: $e');
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
            if (!mounted) return;
            final provider = Provider.of<PlaylistProvider>(context, listen: false);

            try {
                await provider.deleteSpotifyPlaylist(playlist.id);
                _silentRefreshCurrentTab();

                if (mounted) {
                    MessageService.showInfo(context, 'Playlist deleted successfully');
                }
            }

            catch (e) {
                if (mounted) {
                    MessageService.showError(context, 'Failed to delete playlist: $e');
                }
            }
        }
    }

    @override
    Widget build(BuildContext context) {
        return PopScope(
            onPopInvokedWithResult: (didPop, result) {
                if (!didPop) _silentRefreshCurrentTab();
            },

            child: Scaffold(
                appBar: AppBar(
                    title: const Text('Your Library'),
                    centerTitle: true,
                ),

                body: _buildLibraryContent(),
            ),
        );
    }

    Widget _buildLibraryContent() {
        return Column(
            children: [
                TabBar(
                    controller: tabController,
                    tabs: [
                        const Tab(
                            icon: Icon(Icons.edit_note),
                            text: 'Drafts',
                        ),

                        Tab(
                            icon: Image.asset(
                                'assets/logos/SpotifyLogo.png',
                                width: 24,
                                height: 24,
                                errorBuilder: (context, error, stackTrace) {
                                    return const Icon(Icons.music_note);
                                },
                            ),

                            text: 'Spotify',
                        ),
                    ],
                ),

                Expanded(
                    child: TabBarView(
                        controller: tabController,
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
        if (libraryError != null) {
            return Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        const Icon(Icons.error, size: 48, color: Colors.red),
                        const SizedBox(height: 16),

                        Text(
                            'Error: $libraryError',
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                        ),

                        const SizedBox(height: 16),
                        FilledButton(
                            onPressed: () => _silentRefreshCurrentTab(),
                            child: const Text('Retry'),
                        ),
                    ],
                ),
            );
        }
        
        if (isLibraryLoading) {
            return const Center(child: CircularProgressIndicator());
        }
        
        if (drafts.isEmpty) {
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
            padding: const EdgeInsets.all(AppConstants.largePadding),
            itemCount: drafts.length,

            itemBuilder: (context, index) {
                final draft = drafts[index];
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
                            _openDraft(draft);
                        },
                    ),

                onTap: () => _openDraft(draft),
            ),
        );
    }

    Widget _buildSpotifyTab() {
        if (libraryError != null) {
            return Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                        const Icon(Icons.error, size: 48, color: Colors.red),
                        const SizedBox(height: 16),

                        Text(
                            'Error: $libraryError',
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                        ),

                        const SizedBox(height: 16),
                        FilledButton(
                            onPressed: () => _silentRefreshCurrentTab(),
                            child: const Text('Retry'),
                        ),
                    ],
                ),
            );
        }

        if (isLibraryLoading) {
            return const Center(child: CircularProgressIndicator());
        }

        if (spotifyPlaylists.isEmpty) {
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
            padding: const EdgeInsets.all(AppConstants.largePadding),
            itemCount: spotifyPlaylists.length,

            itemBuilder: (context, index) {
                final playlist = spotifyPlaylists[index];
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

                onTap: null,
            ),
        );
    }
}

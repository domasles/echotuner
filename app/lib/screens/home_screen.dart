import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/playlist_provider.dart';
import 'playlist_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
    const HomeScreen({super.key});

    @override
    State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
    final TextEditingController _promptController = TextEditingController();

    final List<String> _quickPrompts = [
        "I'm feeling happy and energetic",
        "Something chill and relaxing",
        "Pump me up for a workout",
        "I'm feeling nostalgic",
        "Perfect for a road trip",
        "Help me focus while studying",
        "Romantic dinner vibes",
        "I'm feeling sad and want to embrace it",
    ];

    @override
    void dispose() {
        _promptController.dispose();
        super.dispose();
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            body: SafeArea(
                child: Consumer<PlaylistProvider>(
                    builder: (context, playlistProvider, child) {
                        return SingleChildScrollView(
                            padding: const EdgeInsets.all(20),

                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    _buildHeader(),

                                    const SizedBox(height: 30),
                                    _buildPromptInput(playlistProvider),
                                    
                                    const SizedBox(height: 20),
                                    _buildQuickPrompts(playlistProvider),

                                    const SizedBox(height: 30),
                                    _buildRateLimitStatus(playlistProvider),
                                ],
                            ),
                        );
                    },
                ),
            ),

            floatingActionButton: FloatingActionButton(
                onPressed: () {
                    Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const SettingsScreen()),
                    );
                },
                
                backgroundColor: const Color(0xFF1DB954),
                child: const Icon(Icons.settings),
            ),
        );
    }

    Widget _buildHeader() {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Row(
                    children: [
                        Container(
                            width: 50,
                            height: 50,

                            decoration: BoxDecoration(
                                gradient: const LinearGradient(colors: [Color(0xFF1DB954), Color(0xFF1ED760)]),
                                borderRadius: BorderRadius.circular(12),
                            ),

                            child: const Icon(
                                Icons.music_note,
                                color: Colors.white,
                                size: 30,
                            ),
                        ),

                        const SizedBox(width: 15),
                        const Expanded(
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Text(
                                        'EchoTuner',
                                        style: TextStyle(
                                            fontSize: 28,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                        ),
                                    ),

                                    Text(
                                        'Your personal AI Music DJ',
                                        style: TextStyle(
                                            fontSize: 16,
                                            color: Colors.white70,
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        );
    }

    Widget _buildPromptInput(PlaylistProvider provider) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                const Text(
                    'What\'s your mood?',
                    style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 12),
                TextField(
                    controller: _promptController,
                    maxLines: 3,

                    decoration: const InputDecoration(
                        hintText: 'e.g., "I\'m feeling energetic and want to dance" or "Something calm for studying"',
                        border: OutlineInputBorder(),
                    ),

                    style: const TextStyle(color: Colors.white),
                ),

                const SizedBox(height: 16),
                SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                        onPressed: provider.isLoading ? null : () => _generatePlaylist(provider),
                        child: provider.isLoading ? const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                                SizedBox(
                                    width: 20,
                                    height: 20,

                                    child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                    ),
                                ),

                                SizedBox(width: 12),
                                Text('Generating playlist...'),
                            ],
                        )
                        
                        : const Text(
                            'Generate Playlist',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                        ),
                    ),
                ),
            ],
        );
    }

    Widget _buildQuickPrompts(PlaylistProvider provider) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                const Text(
                    'Quick suggestions',
                    style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 12),
                Wrap(
                    spacing: 8,
                    runSpacing: 8,

                    children: _quickPrompts.map((prompt) {
                        return ActionChip(
                            label: Text(prompt),
                            onPressed: provider.isLoading ? null : () {
                                _promptController.text = prompt;
                                _generatePlaylist(provider);
                            },
                            
                            backgroundColor: const Color(0xFF2A2A2A),
                            labelStyle: const TextStyle(color: Colors.white70),
                            side: const BorderSide(color: Color(0xFF404040)),
                        );
                    }).toList(),
                ),
            ],
        );
    }

    Widget _buildRateLimitStatus(PlaylistProvider provider) {
        return FutureBuilder<Map<String, dynamic>>(
            future: provider.getRateLimitStatus(),
            builder: (context, snapshot) {
                if (!snapshot.hasData) return const SizedBox.shrink();
                
                final status = snapshot.data!;

                final requestsMade = status['requests_made_today'] ?? 0;
                final maxRequests = status['max_requests_per_day'] ?? 2;
                
                return Card(
                    child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                                const Text(
                                    'Daily Usage',
                                    style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                        color: Colors.white,
                                    ),
                                ),

                                const SizedBox(height: 8),
                                LinearProgressIndicator(
                                    value: requestsMade / maxRequests,
                                    backgroundColor: const Color(0xFF404040),
                                    valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF1DB954)),
                                ),
                                
                                const SizedBox(height: 8),
                                Text(
                                    '$requestsMade / $maxRequests playlists generated today',
                                    style: const TextStyle(color: Colors.white70),
                                ),
                            ],
                        ),
                    ),
                );
            },
        );
    }

    void _generatePlaylist(PlaylistProvider provider) async {
        final prompt = _promptController.text.trim();
        if (prompt.isEmpty) return;

        try {
            await provider.generatePlaylist(prompt);
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
        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                title: const Text('Error'),
                content: Text(error),
                
                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('OK'),
                    ),
                ],
            ),
        );
    }
}

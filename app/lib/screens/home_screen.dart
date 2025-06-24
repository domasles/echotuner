import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/playlist_provider.dart';
import 'playlist_screen.dart';

class HomeScreen extends StatefulWidget {
    const HomeScreen({super.key});

    @override
    State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {    final TextEditingController _promptController = TextEditingController();
    int _selectedIndex = 0;

    final List<String> _quickPrompts = [
        "I'm feeling happy and energetic",
        "Something chill and relaxing",
        "Pump me up for a workout",
        "I'm feeling nostalgic",
        "Perfect for a road trip",
        "Help me focus while studying",
        "Romantic dinner vibes",
        "I'm feeling sad and want to embrace it",
        "Upbeat electronic dance music",
        "Cozy acoustic coffee shop vibes",
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
                            child: Padding(
                                padding: const EdgeInsets.all(24.0),
                                child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                        _buildHeader(),
                                        const SizedBox(height: 40),

										_buildPromptInput(playlistProvider),
                                        const SizedBox(height: 32),

                                        _buildQuickPrompts(playlistProvider),
                                        const SizedBox(height: 100),
                                    ],
                                ),
                            ),
                        );
                    },
                ),
            ),
            bottomNavigationBar: _buildBottomNavigationBar(),
        );
    }

    Widget _buildHeader() {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                    'EchoTuner',
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 8),
                Text(
                    'Create a custom music playlist with the help of AI and natural language processing',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontSize: 16,
                        color: Colors.white70,
                        height: 1.4,
                    ),
                ),
            ],
        );
    }

    Widget _buildPromptInput(PlaylistProvider provider) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
                TextField(
                    controller: _promptController,
                    maxLines: null,
                    minLines: 3,
                    style: const TextStyle(color: Colors.white, fontSize: 16),
					
                    decoration: InputDecoration(
                        hintText: 'Describe your ideal playlist...\n\nFor example: "energetic indie rock from the 2000s" or "chill lofi beats for studying"',
                        hintStyle: TextStyle(
                            color: Colors.white.withValues(alpha: 255 * 0.6),
                            fontSize: 16,
                            height: 1.4,
                        ),
                    ),
                ),

                const SizedBox(height: 24),
                SizedBox(
                    width: double.infinity,
                    height: 56,

                    child: ElevatedButton(
                        onPressed: provider.isLoading ? null : () => _generatePlaylist(provider),
						style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF8B5CF6),
                            foregroundColor: Colors.white,
                            elevation: 4,
                            shadowColor: const Color(0xFF8B5CF6).withValues(alpha: 255 * 0.3)
						),

                        child: provider.isLoading ? const Row(
							mainAxisAlignment: MainAxisAlignment.center,
							children: [
								SizedBox(
									width: 24,
									height: 24,

									child: CircularProgressIndicator(
										strokeWidth: 2.5,
										valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
									),
								),

								SizedBox(width: 16),
								Text(
									'Generating...',
									style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
								),
							],
						)

						: const Text(
							'Generate',
							style: TextStyle(
								fontSize: 18,
								fontWeight: FontWeight.w600
							),
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
                Text(
                    'Quick Suggestions',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 16),
                Wrap(
                    spacing: 12,
                    runSpacing: 12,

                    children: _quickPrompts.map((prompt) {
                        return ActionChip(
                            label: Text(prompt),
                            onPressed: provider.isLoading ? null : () {
                                _promptController.text = prompt;
                                _generatePlaylist(provider);
                            },

                            backgroundColor: const Color(0xFF1A1625),
                            labelStyle: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                            ),

                            side: BorderSide(
                                color: const Color(0xFF8B5CF6).withOpacity(0.3),
                                width: 1,
                            ),

                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(20),
                            ),
							
                            elevation: 2,
                            shadowColor: const Color(0xFF8B5CF6).withOpacity(0.2),
                        );
                    }).toList(),
                ),
            ],
        );
    }

    Widget _buildBottomNavigationBar() {
        return Container(
            decoration: BoxDecoration(
                color: const Color(0xFF1A1625),
                boxShadow: [
                    BoxShadow(
                        color: Colors.black.withOpacity(0.3),
                        blurRadius: 10,
                        offset: const Offset(0, -2),
                    ),
                ],
            ),

            child: BottomNavigationBar(
                currentIndex: _selectedIndex,
                onTap: (index) {
                    setState(() {
                        _selectedIndex = index;
                    });
                },

                items: const [
                    BottomNavigationBarItem(
                        icon: Icon(Icons.home_rounded),
                        label: 'Home',
                    ),

                    BottomNavigationBarItem(
                        icon: Icon(Icons.search_rounded),
                        label: 'Search',
                    ),
					
                    BottomNavigationBarItem(
                        icon: Icon(Icons.library_music_rounded),
                        label: 'Library',
                    ),
                ],
            ),
        );
    }

    void _generatePlaylist(PlaylistProvider provider) async {
        final prompt = _promptController.text.trim();
        if (prompt.isEmpty) {
            _showSnackBar('Please enter a description for your playlist');
            return;
        }

        try {
            await provider.generatePlaylist(prompt);
            if (!mounted) return;
            
            if (provider.error != null) {
                _showErrorDialog(provider.error!);
            } else {
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

    void _showSnackBar(String message) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
                content: Text(message),
                backgroundColor: const Color(0xFF8B5CF6),
                behavior: SnackBarBehavior.floating,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
        );
    }

    void _showErrorDialog(String error) {
        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text(
                    'Error',
                    style: TextStyle(color: Colors.white),
                ),

                content: Text(
                    error,
                    style: const TextStyle(color: Colors.white70),
                ),
				
                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'OK',
                            style: TextStyle(color: Color(0xFF8B5CF6)),
                        ),
                    ),
                ],
            ),
        );
    }
}

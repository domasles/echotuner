import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../providers/playlist_provider.dart';
import '../config/app_colors.dart';
import '../utils/app_logger.dart';

class ProfileScreen extends StatefulWidget {
    const ProfileScreen({super.key});

    @override
    State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
    bool _isLoading = true;
    String? _error;
    int _draftCount = 0;
    int _spotifyPlaylistCount = 0;
    String? _provider;
    String? _displayName;

    @override
    void initState() {
        super.initState();
        _loadProfileData();
    }

    Future<void> _loadProfileData() async {
        setState(() {
            _isLoading = true;
            _error = null;
        });

        try {
            final playlistProvider = context.read<PlaylistProvider>();
            final apiService = context.read<ApiService>();

            // Get profile information from API
            final profileData = await apiService.getUserProfile();
            _provider = profileData['provider'] ?? 'Unknown';
            _displayName = profileData['display_name'];

            // Get playlist counts
            final libraryResponse = await playlistProvider.getLibraryPlaylists();
            _draftCount = libraryResponse.drafts.length;
            _spotifyPlaylistCount = libraryResponse.spotifyPlaylists.length;

        } catch (e) {
            AppLogger.error('Failed to load profile data: $e');
            _error = 'Failed to load profile information';
        } finally {
            if (mounted) {
                setState(() {
                    _isLoading = false;
                });
            }
        }
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Profile'),
                centerTitle: true,
            ),
            body: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? _buildErrorState()
                    : _buildProfileContent(),
        );
    }

    Widget _buildErrorState() {
        return Center(
            child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                    const Icon(
                        Icons.error_outline,
                        size: 64,
                        color: Colors.red,
                    ),
                    const SizedBox(height: 16),
                    Text(
                        _error!,
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: AppColors.textSecondary,
                        ),
                        textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                        onPressed: _loadProfileData,
                        child: const Text('Retry'),
                    ),
                ],
            ),
        );
    }

    Widget _buildProfileContent() {
        return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                    const SizedBox(height: 32),
                    
                    // Profile Picture (simple icon for now)
                    const CircleAvatar(
                        radius: 60,
                        backgroundColor: AppColors.surfaceVariant,
                        child: Icon(
                            Icons.person,
                            size: 80,
                            color: AppColors.textSecondary,
                        ),
                    ),

                    const SizedBox(height: 24),

                    // User Name
                    Text(
                        _displayName ?? 'Unknown',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                    ),

                    const SizedBox(height: 24),

                    // Profile Information Card
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Text(
                                        'Profile Information',
                                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                            fontWeight: FontWeight.bold,
                                        ),
                                    ),
                                    const SizedBox(height: 16),
                                    
                                    _buildInfoRow(
                                        'Login Provider',
                                        _provider?.toUpperCase() ?? 'Unknown',
                                        Icons.login,
                                    ),
                                    
                                    const Divider(height: 24),
                                    
                                    _buildInfoRow(
                                        'Playlist Drafts',
                                        _draftCount.toString(),
                                        Icons.drafts,
                                    ),
                                    
                                    const Divider(height: 24),
                                    
                                    _buildInfoRow(
                                        'Spotify Playlists',
                                        _spotifyPlaylistCount.toString(),
                                        Icons.playlist_play,
                                    ),
                                ],
                            ),
                        ),
                    ),

                    const SizedBox(height: 24),

                    // Coming Soon Card
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Row(
                                        children: [
                                            const Icon(
                                                Icons.construction,
                                                color: AppColors.textSecondary,
                                            ),
                                            const SizedBox(width: 8),
                                            Text(
                                                'Coming Soon',
                                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                                    fontWeight: FontWeight.bold,
                                                ),
                                            ),
                                        ],
                                    ),
                                    const SizedBox(height: 12),
                                    Text(
                                        '• Profile Picture Management\n'
                                        '• Account Information Editing\n'
                                        '• Privacy Information',
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                            color: AppColors.textSecondary,
                                            height: 1.5,
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ),

                    const SizedBox(height: 32),
                ],
            ),
        );
    }

    Widget _buildInfoRow(String label, String value, IconData icon) {
        return Row(
            children: [
                Icon(
                    icon,
                    size: 20,
                    color: AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Expanded(
                    child: Text(
                        label,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                        ),
                    ),
                ),
                Text(
                    value,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                    ),
                ),
            ],
        );
    }
}

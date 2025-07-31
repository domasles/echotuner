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
    String? _accountType;
    String? _provider;
    String? _displayName;
    String? _email;
    String? _profilePictureUrl;

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
            _accountType = profileData['account_type'] ?? 'Unknown';
            _provider = profileData['provider'] ?? 'Unknown';
            _displayName = profileData['display_name'];
            _email = profileData['email'];
            _profilePictureUrl = profileData['profile_picture_url'];

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
                    
                    // Profile Picture
                    CircleAvatar(
                        radius: 60,
                        backgroundColor: AppColors.surfaceVariant,
                        backgroundImage: _profilePictureUrl != null && _profilePictureUrl!.isNotEmpty
                            ? NetworkImage(_profilePictureUrl!)
                            : null,
                        child: _profilePictureUrl == null || _profilePictureUrl!.isEmpty
                            ? const Icon(
                                Icons.person,
                                size: 80,
                                color: AppColors.textSecondary,
                            )
                            : null,
                    ),

                    const SizedBox(height: 24),

                    // User Name
                    Text(
                        _displayName ?? 'User',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                    ),

                    const SizedBox(height: 8),

                    // User Email
                    if (_email != null && _email!.isNotEmpty)
                        Text(
                            _email!,
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                color: AppColors.textSecondary,
                            ),
                            textAlign: TextAlign.center,
                        ),

                    const SizedBox(height: 24),

                    // Coming Soon Notice
                    Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                            color: AppColors.surfaceVariant.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: AppColors.surfaceVariant,
                                width: 1,
                            ),
                        ),
                        child: Row(
                            children: [
                                const Icon(
                                    Icons.info_outline,
                                    color: AppColors.textSecondary,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                    child: Text(
                                        'Profile editing coming soon!',
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                            color: AppColors.textSecondary,
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),

                    const SizedBox(height: 32),

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
                                        'Account Type',
                                        _accountType ?? 'Unknown',
                                        Icons.account_circle,
                                    ),
                                    
                                    const Divider(height: 24),
                                    
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

                    // Additional Info Card
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Text(
                                        'Coming Soon',
                                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                            fontWeight: FontWeight.bold,
                                        ),
                                    ),
                                    const SizedBox(height: 12),
                                    Text(
                                        '• Profile picture from Google/Spotify\n'
                                        '• Display name and surname\n'
                                        '• Detailed playlist statistics\n'
                                        '• User preferences overview',
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

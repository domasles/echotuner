import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../systems/universal_screen_focus_api_system.dart';
import '../providers/playlist_provider.dart';
import '../services/message_service.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../config/app_colors.dart';
import '../utils/app_logger.dart';

class ProfileScreen extends StatefulWidget {
    const ProfileScreen({super.key});

    @override
    State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> with WidgetsBindingObserver, UniversalScreenFocusApiMixin {
    bool _isLoading = true;
    String? _error;
    int _draftCount = 0;
    int _spotifyPlaylistCount = 0;
    String? _provider;
    String? _displayName;

    @override
    void initState() {
        super.initState();
        WidgetsBinding.instance.addObserver(this);
        
        WidgetsBinding.instance.addPostFrameCallback((_) {
            initializeScreenFocusApiSystem(isActiveTab: true);
        });

    }

    @override
    void dispose() {
        WidgetsBinding.instance.removeObserver(this);
        super.dispose();
    }

    @override
    void registerScreenFocusApiCalls() {
        screenFocusApiSystem.registerApiCall(ScreenFocusApiCall(
            name: 'profile_data_refresh',
            apiCall: (context) async { await _loadProfileData(); },
            runOnScreenEnter: true,
            runOnAppResume: true,
            oncePerSession: false,
        ));
    }

    Future<void> _loadProfileData() async {
        setState(() {
            _isLoading = true;
            _error = null;
        });

        try {
            final playlistProvider = context.read<PlaylistProvider>();
            final apiService = context.read<ApiService>();
            final profileData = await apiService.getUserProfile();

            _provider = profileData['provider'] ?? 'Unknown';
            _displayName = profileData['display_name'];

            final libraryResponse = await playlistProvider.getLibraryPlaylists();

            _draftCount = libraryResponse.drafts.length;
            _spotifyPlaylistCount = libraryResponse.spotifyPlaylists.length;

        }

        catch (e) {
            AppLogger.error('Failed to load profile data: $e');
            _error = 'Failed to load profile information';
        }

        finally {
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

        body: _isLoading ? const Center(child: CircularProgressIndicator()) :
            _error != null
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
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSecondary),
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

                    Text(
                        _displayName ?? 'Unknown',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                    ),

                    const SizedBox(height: 24),
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

                    Consumer<AuthService>(
                        builder: (context, authService, child) {
                            if (!authService.isAuthenticated || authService.userId == null) {
                                return const SizedBox.shrink();
                            }

                            return Card(
                                child: Padding(
                                    padding: const EdgeInsets.all(16),
                                    child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                            Text(
                                                'API Developer Info',
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
                                            _buildCopyableInfoRow(
                                                'API Token (User ID)',
                                                authService.userId!,
                                                Icons.key,
                                                context,
                                            ),
                                        ],
                                    ),
                                ),
                            );
                        },
                    ),

                    const SizedBox(height: 24),

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
                                                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
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

    Widget _buildCopyableInfoRow(String label, String value, IconData icon, BuildContext context) {
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

                const SizedBox(width: 8),
                IconButton(
                    onPressed: () => _copyToClipboard(context, value),
                    icon: const Icon(Icons.copy),
                    iconSize: 16,
                    tooltip: 'Copy token',
                    style: IconButton.styleFrom(
                        backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                        foregroundColor: AppColors.primary,
                        minimumSize: const Size(32, 32),
                    ),
                ),
            ],
        );
    }

    void _copyToClipboard(BuildContext context, String text) async {
        try {
            await Clipboard.setData(ClipboardData(text: text));

            if (context.mounted) {
                MessageService.showSuccess(context, 'Token copied to clipboard');
            }
        }

        catch (e) {
            if (context.mounted) {
                MessageService.showError(context, 'Failed to copy token: $e');
            }
        }
    }
}

import 'package:flutter/material.dart';

import '../models/playlist_draft_models.dart';
import '../models/rate_limit_models.dart';
import '../models/playlist_request.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/info_message.dart';
import '../models/user_context.dart';
import '../models/song.dart';
import '../models/app_config.dart';
import '../utils/app_logger.dart';

class PlaylistProvider extends ChangeNotifier {
    final ApiService _apiService;
    final AuthService _authService;

    List<Song> _currentPlaylist = [];

    String _currentPrompt = '';
    String? _currentPlaylistId;

    bool _isPlaylistAddedToSpotify = false;
    SpotifyPlaylistInfo? _spotifyPlaylistInfo;

    bool _isLoading = false;
    bool _isAddingToSpotify = false;

    UserContext? _userContext;
    RateLimitStatus? _rateLimitStatus;
    AppConfigData? _config;

    String? _error;

    final List<InfoMessage> _infoMessages = [];

    PlaylistProvider(this._apiService, this._authService) {
        _loadConfig();
        _authService.addListener(_onAuthStateChanged);

        Future.delayed(const Duration(milliseconds: 100), () {
            if (_authService.isAuthenticated) _loadRateLimitStatus();
        });
    }

    @override
    void dispose() {
        _authService.removeListener(_onAuthStateChanged);
        super.dispose();
    }

    void _onAuthStateChanged() {
        if (_authService.isAuthenticated && _authService.userId != null) {
            Future.delayed(const Duration(milliseconds: 500), () {
                if (_authService.isAuthenticated && _authService.userId != null) _loadRateLimitStatus();
            });
        }

        else {
            _rateLimitStatus = null;
            _currentPlaylist = [];
            _currentPlaylistId = null;
            _spotifyPlaylistInfo = null;
            _isPlaylistAddedToSpotify = false;
            _userContext = null;
            _error = null;

            notifyListeners();
        }
    }

    List<Song> get currentPlaylist => _currentPlaylist;

    String get currentPrompt => _currentPrompt;
    String? get currentPlaylistId => _currentPlaylistId;

    RateLimitStatus? get rateLimitStatus => _rateLimitStatus;

    bool get showPlaylistLimits => _rateLimitStatus?.playlistLimitEnabled ?? false;

    Future<void> _loadConfig() async {
        try {
            _config = await _apiService.getConfig();
            AppLogger.info('Loaded API config: max songs=${_config?.playlists.maxSongsPerPlaylist}, max daily=${_config?.playlists.maxPlaylistsPerDay}');
            
            // If API is available and we got config, also try to load rate limit status
            await _loadRateLimitStatus();
        } catch (e) {
            AppLogger.warning('Failed to load API config, using defaults: $e');
            // Fallback to default values if config loading fails
        }
    }

    int get maxSongsPerPlaylist => _config?.playlists.maxSongsPerPlaylist ?? 20;
    int get maxPlaylistsPerDay => _config?.playlists.maxPlaylistsPerDay ?? 20;

    bool get isPlaylistAddedToSpotify => _isPlaylistAddedToSpotify;

    SpotifyPlaylistInfo? get spotifyPlaylistInfo => _spotifyPlaylistInfo;

    bool get isLoading => _isLoading;
    bool get isAddingToSpotify => _isAddingToSpotify;

    UserContext? get userContext => _userContext;
    String? get error => _error;

    List<InfoMessage> get infoMessages => _infoMessages.where((msg) => !msg.isExpired).toList();

    void addInfoMessage(String message, InfoMessageType type, {String? actionLabel, VoidCallback? onAction, String? actionUrl, Duration? duration}) {
        final infoMessage = InfoMessage(
            id: DateTime.now().millisecondsSinceEpoch.toString(),
            message: message,
            type: type,
            actionLabel: actionLabel,
            onAction: onAction,
            actionUrl: actionUrl,
            duration: duration,
        );

        _infoMessages.add(infoMessage);
        notifyListeners();

        if (duration != null) {
            Future.delayed(duration, () {
                _infoMessages.removeWhere((msg) => msg.id == infoMessage.id);
                notifyListeners();
            });
        }
    }

    void removeInfoMessage(String id) {
        _infoMessages.removeWhere((msg) => msg.id == id);
        notifyListeners();
    }

    void clearInfoMessages() {
        _infoMessages.clear();
        notifyListeners();
    }

    void updateUserContext(UserContext? context) {
        _userContext = context;
        notifyListeners();
    }

    // Local storage methods removed - all playlists are now server-based

    Future<void> generatePlaylist(String prompt, {String? discoveryStrategy}) async {
        _isLoading = true;
        _error = null;
        _isPlaylistAddedToSpotify = false;
        _spotifyPlaylistInfo = null;

        notifyListeners();

        try {
            final userId = _authService.userId;

            AppLogger.debug('Generating playlist with user: ${userId?.substring(0, 20)}...');

            if (userId == null) {
                throw Exception('Not authenticated');
            }

            final request = PlaylistRequest(
                prompt: prompt,
                userContext: _userContext,
                discoveryStrategy: discoveryStrategy ?? 'balanced',
                count: maxSongsPerPlaylist, // Use config value
            );

            final response = await _apiService.generatePlaylist(request);

            _currentPlaylist = response.songs;
            _currentPrompt = prompt;
            _currentPlaylistId = response.playlistId;
            _error = null;

            // Playlist generated successfully
            // (Local storage removed - all playlists are server-based now)

            // Refresh rate limit status after successful playlist generation
            await _loadRateLimitStatus();
        }

        catch (e, stackTrace) {
            AppLogger.error('Playlist generation error', error: e, stackTrace: stackTrace);

            if (e.toString().contains('timeout')) {
                _error = 'Request timed out. Please try again.';
            }

            else if (e.toString().contains('network')) {
                _error = 'Network error. Please check your connection.';
            }

            else if (e.toString().contains('authentication')) {
                _error = 'Authentication error. Please log in again.';
            }

            else {
                _error = 'Failed to generate playlist. Please try again.';
            }

            _currentPlaylist = [];
        }

        finally {
            _isLoading = false;
            notifyListeners();
        }
    }

    void removeSong(Song song) async {
        _currentPlaylist.removeWhere((s) => s == song);
        notifyListeners();
        
        // Update the draft on the server
        await _updateDraftPlaylist();
    }

    Future<void> _updateDraftPlaylist() async {
        if (_currentPlaylistId == null) return;

        try {
            final userId = _authService.userId;
            if (userId == null) return;

            final request = PlaylistRequest(
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Updated playlist',
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.updatePlaylistDraft(request, _currentPlaylistId!);
            _currentPlaylistId = response.playlistId;
            
            // Draft updated successfully on server
        }

        catch (e) {
            AppLogger.error('Failed to update draft playlist', error: e);
        }
    }

    Future<bool> removeSongFromSpotifyPlaylist(String playlistId, String trackUri, String userId) async {
        try {
            return await _apiService.removeTrackFromSpotifyPlaylist(playlistId, trackUri);
        }

        catch (e) {
            return false;
        }
    }

    void addSong(Song song) async {
        if (!_currentPlaylist.contains(song)) {
            _currentPlaylist.add(song);

            if (_currentPlaylistId != null) {
                await _updateDraftPlaylist();
            }

            notifyListeners();
        }
    }

    void reorderSongs(int oldIndex, int newIndex) {
        if (newIndex > oldIndex) newIndex -= 1;

        final Song song = _currentPlaylist.removeAt(oldIndex);
        _currentPlaylist.insert(newIndex, song);
        notifyListeners();
    }

    void clearPlaylist() {
        _currentPlaylist = [];
        _currentPrompt = '';
        _currentPlaylistId = null;
        _isPlaylistAddedToSpotify = false;
        _spotifyPlaylistInfo = null;
        _error = null;

        notifyListeners();
    }

    Future<void> _loadRateLimitStatus() async {
        try {
            if (_authService.isAuthenticated && _authService.userId != null) {
                _rateLimitStatus = await getRateLimitStatus();
                notifyListeners();
            }
        }

        catch (e) {
            AppLogger.error(
                'Failed to load rate limit status: $e',
                error: e,
            );
            // Don't set _rateLimitStatus to null here - keep trying on next API call
        }
    }

    Future<void> onAuthenticationChanged() async {
        if (_authService.isAuthenticated && _authService.userId != null) {
            await _loadRateLimitStatus();
        }

        else {
            _rateLimitStatus = null;
            notifyListeners();
        }
    }

    Future<void> refreshRateLimitStatus() async {
        await _loadRateLimitStatus();
    }

    Future<String> addToSpotify({required String playlistName, String? description}) async {
        if (_currentPlaylistId == null) {
            if (_currentPlaylist.isEmpty) throw Exception('No playlist to add to Spotify');

            final userId = _authService.userId;
            if (userId == null) throw Exception('Not authenticated');

            final request = PlaylistRequest(
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Spotify playlist update',
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.updatePlaylistDraft(request, _currentPlaylistId!);
            _currentPlaylistId = response.playlistId;
        }

        final userId = _authService.userId;
        if (userId == null) throw Exception('Not authenticated');

        _isAddingToSpotify = true;
        notifyListeners();

        try {

            final request = SpotifyPlaylistRequest(
                name: playlistName,
                description: description,
                public: false,
                songs: _currentPlaylist, // Always include songs for new system
            );

            final response = await _apiService.createSpotifyPlaylist(request, _currentPlaylistId!);

            if (response.success) {
                _isPlaylistAddedToSpotify = true;

                // Playlist successfully added to Spotify (local storage removed)
                await _loadRateLimitStatus(); // Ensure rate limit status is loaded after successful API call

                return response.playlistUrl;
            }

            else {
                throw Exception(response.message);
            }
        }

        finally {
            _isAddingToSpotify = false;
            notifyListeners();
        }
    }

    Future<RateLimitStatus> getRateLimitStatus() async {
        final userId = _authService.userId;
        
        if (_authService.isAuthenticated && userId != null) {
            try {
                return await _apiService.getUserRateLimitStatus();
            } catch (e) {
                AppLogger.warning('Failed to get rate limit status from API: $e');
                // Return fallback status with config values
                return RateLimitStatus(
                    userId: userId,
                    requestsMadeToday: 0,
                    maxRequestsPerDay: maxPlaylistsPerDay,
                    canMakeRequest: true,
                    playlistLimitEnabled: _config?.features.playlistLimitEnabled ?? false,
                );
            }
        }

        else {
            return RateLimitStatus(
                userId: userId ?? '',
                requestsMadeToday: 0,
                maxRequestsPerDay: 0,
                canMakeRequest: false,
                playlistLimitEnabled: false,
            );
        }
    }

    Future<LibraryPlaylistsResponse> getLibraryPlaylists({bool forceRefresh = false}) async {
        final userId = _authService.userId;

        if (userId == null) throw Exception('Not authenticated');

        // Load playlists from server (local storage removed)
        return await _apiService.getLibraryPlaylists();
    }

    Future<LibraryPlaylistsResponse> refreshLibraryPlaylists() async {
        return await getLibraryPlaylists(forceRefresh: true);
    }

    Future<void> loadDraft(PlaylistDraft draft) async {
        _currentPlaylist = draft.songs;
        _currentPrompt = draft.prompt;
        _currentPlaylistId = draft.id;

        _isPlaylistAddedToSpotify = draft.isAddedToSpotify;
        _spotifyPlaylistInfo = null;
        _error = null;

        // Draft loaded (local storage removed)
        notifyListeners();
    }

    Future<void> deleteDraft(String playlistId) async {
        final userId = _authService.userId;
        if (userId == null) throw Exception('Not authenticated');
        
        // Delete draft from server (local storage removed)
        await _apiService.deleteDraftPlaylist(playlistId);
    }

    Future<void> deleteSpotifyPlaylist(String playlistId) async {
        final userId = _authService.userId;

        if (userId == null) throw Exception('Not authenticated');
        
        // Delete from Spotify via API (local storage removed)
        await _apiService.deleteSpotifyPlaylist(playlistId);
    }

    Future<void> loadSpotifyPlaylist(Map<String, dynamic> spotifyPlaylist) async {
        _isLoading = true;
        _error = null;

        notifyListeners();

        try {
            final userId = _authService.userId;
            if (userId == null) throw Exception('Not authenticated');

            final spotifyTracks = await _apiService.getSpotifyPlaylistTracks(
                spotifyPlaylist['id']
            );

            final songs = spotifyTracks.map((track) {
                final trackData = track['track'];

                return Song(
                    title: trackData['name'] ?? 'Unknown',
                    artist: trackData['artists'] != null && trackData['artists'].length > 0 ? trackData['artists'][0]['name'] ?? 'Unknown' : 'Unknown',
                    album: trackData['album']?['name'] ?? 'Unknown',
                    spotifyId: trackData['id'],
                );

            }).toList();

            _currentPlaylist = songs;
            _currentPrompt = 'Refining Spotify playlist: ${spotifyPlaylist['name']}';
            _currentPlaylistId = null;
            _isPlaylistAddedToSpotify = false;
            _spotifyPlaylistInfo = null;
            _error = null;
        }

        catch (e) {
            _error = e.toString();
        }

        finally {
            _isLoading = false;
            notifyListeners();
        }
    }
}

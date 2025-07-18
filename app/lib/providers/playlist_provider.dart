import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';
import 'dart:convert';

import '../models/playlist_draft_models.dart';
import '../models/rate_limit_models.dart';
import '../services/device_service.dart';
import '../models/playlist_request.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/info_message.dart';
import '../models/user_context.dart';
import '../models/song.dart';
import '../utils/app_logger.dart';

class PlaylistProvider extends ChangeNotifier {
    static const String _demoPlaylistsKey = 'demo_playlists';
    static const String _demoCurrentPlaylistKey = 'demo_current_playlist';

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

    String? _deviceId;
    String? _error;

    final List<InfoMessage> _infoMessages = [];

    PlaylistProvider({required ApiService apiService, required AuthService authService}) : _apiService = apiService, _authService = authService {
        _initializeDeviceId();
        if (_authService.isAuthenticated) _loadRateLimitStatus();

        _initializeDemoData();
        _authService.addListener(_onAuthStateChanged);
    }

    @override
    void dispose() {
        _authService.removeListener(_onAuthStateChanged);
        super.dispose();
    }

    void _onAuthStateChanged() {
        if (_authService.isAuthenticated && _authService.sessionId != null) {
            Future.delayed(const Duration(milliseconds: 500), () {
                if (_authService.isAuthenticated && _authService.sessionId != null) _loadRateLimitStatus();
            });
        }

        else {
            _rateLimitStatus = null;
            _deviceId = null;
            _currentPlaylist = [];
            _currentPlaylistId = null;
            _spotifyPlaylistInfo = null;
            _isPlaylistAddedToSpotify = false;
            _userContext = null;
            _error = null;

            notifyListeners();
        }
    }

    Future<void> _initializeDemoData() async {
        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) {
            await _loadCurrentPlaylistLocally();
            notifyListeners();
        }
    }

    List<Song> get currentPlaylist => _currentPlaylist;

    String get currentPrompt => _currentPrompt;
    String? get currentPlaylistId => _currentPlaylistId;

    RateLimitStatus? get rateLimitStatus => _rateLimitStatus;

    bool get showPlaylistLimits => _rateLimitStatus?.playlistLimitEnabled ?? false;
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

    Future<void> _initializeDeviceId() async {
        _deviceId = await DeviceService.getDeviceId();
    }

    void updateUserContext(UserContext? context) {
        _userContext = context;
        notifyListeners();
    }

    Future<bool> _isDemoAccount() async {
        try {
            final response = await _apiService.get('/server/mode');
            return response['demo_mode'] as bool? ?? false;
        }
		
		catch (e) {
            AppLogger.debug('Failed to check demo mode: $e');
            return false;
        }
    }

    Future<void> _savePlaylistLocally(PlaylistDraft draft) async {
        final prefs = await SharedPreferences.getInstance();
        final existingDataJson = prefs.getString(_demoPlaylistsKey);
        
        List<dynamic> existingPlaylists = [];

        if (existingDataJson != null) existingPlaylists = jsonDecode(existingDataJson);

        existingPlaylists.removeWhere((p) => p['id'] == draft.id);
        existingPlaylists.add(draft.toJson());
        
        await prefs.setString(_demoPlaylistsKey, jsonEncode(existingPlaylists));
        AppLogger.playlist('Saved playlist ${draft.id} locally');
    }

    Future<void> _saveCurrentPlaylistLocally() async {
        if (_currentPlaylist.isEmpty) return;
        final prefs = await SharedPreferences.getInstance();

        final currentData = {
            'songs': _currentPlaylist.map((s) => s.toJson()).toList(),
            'prompt': _currentPrompt,
            'playlist_id': _currentPlaylistId,
            'is_added_to_spotify': _isPlaylistAddedToSpotify,
            'saved_at': DateTime.now().toIso8601String(),
        };

        await prefs.setString(_demoCurrentPlaylistKey, jsonEncode(currentData));
        AppLogger.playlist('Saved current playlist locally');
    }

    Future<List<PlaylistDraft>> _loadPlaylistsLocally() async {
        final prefs = await SharedPreferences.getInstance();
        final dataJson = prefs.getString(_demoPlaylistsKey);

        if (dataJson == null) return [];

        try {
            final List<dynamic> playlistsData = jsonDecode(dataJson);
            return playlistsData.map((data) => PlaylistDraft.fromJson(data)).toList();
        }

        catch (e) {
            AppLogger.playlist('Failed to load local playlists: $e');
            return [];
        }
    }

    Future<void> _loadCurrentPlaylistLocally() async {
        final prefs = await SharedPreferences.getInstance();
        final dataJson = prefs.getString(_demoCurrentPlaylistKey);

        if (dataJson == null) return;
       
        try {
            final Map<String, dynamic> data = jsonDecode(dataJson);

            _currentPlaylist = (data['songs'] as List<dynamic>).map((s) => Song.fromJson(s)).toList();
            _currentPrompt = data['prompt'] ?? '';
            _currentPlaylistId = data['playlist_id'];
            _isPlaylistAddedToSpotify = data['is_added_to_spotify'] ?? false;

            AppLogger.playlist('Loaded current playlist from local storage');
        }

        catch (e) {
            AppLogger.playlist('Failed to load current playlist locally: $e');
        }
    }

    Future<void> _deletePlaylistLocally(String playlistId) async {
        final prefs = await SharedPreferences.getInstance();
        final existingDataJson = prefs.getString(_demoPlaylistsKey);

        if (existingDataJson == null) return;

        try {
            List<dynamic> existingPlaylists = jsonDecode(existingDataJson);
            existingPlaylists.removeWhere((p) => p['id'] == playlistId);

            await prefs.setString(_demoPlaylistsKey, jsonEncode(existingPlaylists));
            AppLogger.playlist('Deleted playlist $playlistId locally');
        }

        catch (e) {
            AppLogger.playlist('Failed to delete local playlist: $e');
        }
    }

    Future<void> _saveSpotifyPlaylistLocally(Map<String, dynamic> spotifyInfo) async {
        final prefs = await SharedPreferences.getInstance();
        const spotifyPlaylistsKey = 'demo_spotify_playlists';
        final existingDataJson = prefs.getString(spotifyPlaylistsKey);

        List<dynamic> existingSpotifyPlaylists = [];

        if (existingDataJson != null) existingSpotifyPlaylists = jsonDecode(existingDataJson);
        existingSpotifyPlaylists.add(spotifyInfo);
        
        await prefs.setString(spotifyPlaylistsKey, jsonEncode(existingSpotifyPlaylists));
        AppLogger.playlist('Saved Spotify playlist ${spotifyInfo['id']} locally');
    }

    Future<List<Map<String, dynamic>>> _loadSpotifyPlaylistsLocally() async {
        final prefs = await SharedPreferences.getInstance();
        const spotifyPlaylistsKey = 'demo_spotify_playlists';
        final dataJson = prefs.getString(spotifyPlaylistsKey);

        if (dataJson == null) return [];

        try {
            final List<dynamic> playlistsData = jsonDecode(dataJson);
            return playlistsData.cast<Map<String, dynamic>>();
        }

        catch (e) {
            AppLogger.playlist('Failed to load local Spotify playlists: $e');
            return [];
        }
    }

    Future<void> _deleteSpotifyPlaylistLocally(String playlistId) async {
        try {
            final prefs = await SharedPreferences.getInstance();
            const spotifyPlaylistsKey = 'demo_spotify_playlists';
            final existingDataJson = prefs.getString(spotifyPlaylistsKey);

            if (existingDataJson == null) return;

            List<dynamic> existingSpotifyPlaylists = jsonDecode(existingDataJson);
            
            // Remove the playlist with the matching ID
            existingSpotifyPlaylists.removeWhere((playlist) => playlist['id'] == playlistId);
            
            await prefs.setString(spotifyPlaylistsKey, jsonEncode(existingSpotifyPlaylists));
            AppLogger.playlist('Deleted Spotify playlist $playlistId from local storage');
        }

        catch (e) {
            AppLogger.playlist('Failed to delete Spotify playlist locally: $e');
            throw Exception('Failed to delete playlist from library');
        }
    }

    Future<void> generatePlaylist(String prompt, {String? discoveryStrategy}) async {
        if (_deviceId == null) await _initializeDeviceId();

        _isLoading = true;
        _error = null;
        _isPlaylistAddedToSpotify = false;
        _spotifyPlaylistInfo = null;

        notifyListeners();

        try {
            final sessionId = _authService.sessionId;
            final deviceId = _authService.deviceId;

            AppLogger.debug('Generating playlist with session: ${sessionId?.substring(0, 20)}... device: ${deviceId?.substring(0, 20)}...');

            if (sessionId == null) {
                throw Exception('Not authenticated');
            }

            final request = PlaylistRequest(
                prompt: prompt,
                deviceId: _deviceId!,
                sessionId: sessionId,
                userContext: _userContext,
                discoveryStrategy: discoveryStrategy ?? 'balanced',
            );

            final response = await _apiService.generatePlaylist(request);

            _currentPlaylist = response.songs;
            _currentPrompt = prompt;
            _currentPlaylistId = response.playlistId;
            _error = null;

            final isDemoAccount = await _isDemoAccount();
    
            if (isDemoAccount && response.playlistId != null) {
                await _saveCurrentPlaylistLocally();

                final draft = PlaylistDraft(
                    id: response.playlistId!,
                    deviceId: deviceId!,
                    sessionId: sessionId,
                    prompt: prompt,
                    songs: response.songs,
                    createdAt: DateTime.now(),
                    updatedAt: DateTime.now(),
                    status: 'draft',
                );

                await _savePlaylistLocally(draft);
            }

            _loadRateLimitStatus();
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

        if (_currentPlaylistId != null) {
            await _updateDraftPlaylist();
        }

        notifyListeners();
    }

    Future<void> _updateDraftPlaylist() async {
        if (_currentPlaylistId == null || _deviceId == null) return;

        try {
            final sessionId = _authService.sessionId;
            if (sessionId == null) return;

            final request = PlaylistRequest(
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Updated playlist',
                deviceId: _deviceId!,
                sessionId: sessionId,
                currentSongs: _currentPlaylist,
                playlistId: _currentPlaylistId,
            );

            final response = await _apiService.updatePlaylistDraft(request);
            _currentPlaylistId = response.playlistId;
            
            // Update local storage with the current playlist
            final updatedDraft = PlaylistDraft(
                id: _currentPlaylistId!,
                deviceId: _deviceId!,
                sessionId: sessionId,
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Updated playlist',
                songs: _currentPlaylist,
                status: 'draft',
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
            );
            
            await _savePlaylistLocally(updatedDraft);
        }

        catch (e) {
            AppLogger.error('Failed to update draft playlist', error: e);
        }
    }

    Future<bool> removeSongFromSpotifyPlaylist(String playlistId, String trackUri, String sessionId, String deviceId) async {
        try {
            return await _apiService.removeTrackFromSpotifyPlaylist(playlistId, trackUri, sessionId, deviceId);
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
            if (_authService.isAuthenticated && _authService.sessionId != null) {
                _rateLimitStatus = await getRateLimitStatus();
                notifyListeners();
            }
        }

        catch (e) {
            AppLogger.error(
                'Failed to load rate limit status: $e',
                error: e,
            );
        }
    }

    Future<void> onAuthenticationChanged() async {
        if (_authService.isAuthenticated && _authService.sessionId != null) {
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
            if (_deviceId == null) await _initializeDeviceId();

            final sessionId = _authService.sessionId;
            if (sessionId == null) throw Exception('Not authenticated');

            final request = PlaylistRequest(
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Spotify playlist update',
                deviceId: _deviceId!,
                sessionId: sessionId,
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.updatePlaylistDraft(request);
            _currentPlaylistId = response.playlistId;
        }

        if (_deviceId == null) await _initializeDeviceId();
        final sessionId = _authService.sessionId;
        if (sessionId == null) throw Exception('Not authenticated');

        _isAddingToSpotify = true;
        notifyListeners();

        try {
            final isDemoAccount = await _isDemoAccount();

            final request = SpotifyPlaylistRequest(
                playlistId: _currentPlaylistId!,
                deviceId: _deviceId!,
                sessionId: sessionId,
                name: playlistName,
                description: description,
                public: false,
                songs: isDemoAccount ? _currentPlaylist : null,
            );

            final response = await _apiService.createSpotifyPlaylist(request);

            if (response.success) {
                _isPlaylistAddedToSpotify = true;

                if (isDemoAccount && _currentPlaylistId != null) {
                    await _deletePlaylistLocally(_currentPlaylistId!);

                    final spotifyInfo = {
                        'id': response.spotifyPlaylistId,
                        'name': playlistName,
                        'url': response.playlistUrl,
                        'tracks_count': _currentPlaylist.length,
                        'created_at': DateTime.now().toIso8601String(),
                    };

                    await _saveSpotifyPlaylistLocally(spotifyInfo);
                }

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
        if (_deviceId == null) {
            await _initializeDeviceId();
        }

        if (_authService.isAuthenticated && _authService.sessionId != null) {
            return await _apiService.getAuthenticatedRateLimitStatus(
                _authService.sessionId!,
                _deviceId!
            );
        }

        else {
            return RateLimitStatus(
                deviceId: _deviceId ?? '',
                requestsMadeToday: 0,
                maxRequestsPerDay: 0,
                canMakeRequest: false,
                playlistLimitEnabled: false,
            );
        }
    }

    Future<LibraryPlaylistsResponse> getLibraryPlaylists({bool forceRefresh = false}) async {
        if (_deviceId == null) await _initializeDeviceId();
        final sessionId = _authService.sessionId;

        if (sessionId == null) throw Exception('Not authenticated');
        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) {
            final localDrafts = await _loadPlaylistsLocally();
            final localSpotifyPlaylists = await _loadSpotifyPlaylistsLocally();
            final updatedDrafts = <PlaylistDraft>[];

            for (final draft in localDrafts) {
                updatedDrafts.add(draft);
            }

            final spotifyPlaylistInfos = localSpotifyPlaylists.map((playlist) {
                return SpotifyPlaylistInfo(
                    id: playlist['id'] as String,
                    name: playlist['name'] as String,
                    tracksCount: playlist['tracks_count'] as int? ?? 0,
                    spotifyUrl: playlist['url'] as String,
                );
            }).toList();

            return LibraryPlaylistsResponse(
                drafts: updatedDrafts,
                spotifyPlaylists: spotifyPlaylistInfos,
            );
        }

        final request = LibraryPlaylistsRequest(
            deviceId: _deviceId!,
            sessionId: sessionId,
            includeDrafts: true,
            forceRefresh: forceRefresh,
        );

        return await _apiService.getLibraryPlaylists(request);
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

        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) await _saveCurrentPlaylistLocally();
        notifyListeners();
    }

    Future<void> deleteDraft(String playlistId) async {
        if (_deviceId == null) await _initializeDeviceId();
        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) {
            await _deletePlaylistLocally(playlistId);
            return;
        }

        await _apiService.deleteDraftPlaylist(playlistId, _deviceId!);
    }

    Future<void> deleteSpotifyPlaylist(String playlistId) async {
        if (_deviceId == null) await _initializeDeviceId();
        final sessionId = _authService.sessionId;

        if (sessionId == null) throw Exception('Not authenticated');
        
        // Always call the API to delete from Spotify
        await _apiService.deleteSpotifyPlaylist(playlistId, sessionId, _deviceId!);
        
        // Additionally, if this is a demo account, remove from local storage
        final isDemoAccount = await _isDemoAccount();
        if (isDemoAccount) {
            await _deleteSpotifyPlaylistLocally(playlistId);
        }
    }

    Future<void> loadSpotifyPlaylist(Map<String, dynamic> spotifyPlaylist) async {
        _isLoading = true;
        _error = null;

        notifyListeners();

        try {
            if (_deviceId == null) await _initializeDeviceId();
            final sessionId = _authService.sessionId;
            if (sessionId == null) throw Exception('Not authenticated');

            final spotifyTracks = await _apiService.getSpotifyPlaylistTracks(
                spotifyPlaylist['id'], 
                sessionId, 
                _deviceId!
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

import 'package:flutter/material.dart';
import 'dart:developer' as developer;

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
    final ApiService _apiService;
    final AuthService _authService;

    List<Song> _currentPlaylist = [];
    String _currentPrompt = '';
    String? _currentPlaylistId;
    bool _isPlaylistAddedToSpotify = false;
    SpotifyPlaylistInfo? _spotifyPlaylistInfo;

    int _refinementsUsed = 0;
    bool _isLoading = false;
    bool _isAddingToSpotify = false;

    UserContext? _userContext;
    RateLimitStatus? _rateLimitStatus;

    String? _deviceId;
    String? _error;

    final List<InfoMessage> _infoMessages = [];

    PlaylistProvider({required ApiService apiService, required AuthService authService}) : _apiService = apiService, _authService = authService {
        _initializeDeviceId();
        _loadRateLimitStatus();
    }

    List<Song> get currentPlaylist => _currentPlaylist;

    String get currentPrompt => _currentPrompt;
    String? get currentPlaylistId => _currentPlaylistId;

    int get refinementsUsed {
        if (_isPlaylistAddedToSpotify && _spotifyPlaylistInfo != null) {
            return _spotifyPlaylistInfo!.refinementsUsed;
        }
        
        return _refinementsUsed;
    }

    RateLimitStatus? get rateLimitStatus => _rateLimitStatus;

    bool get canRefine {
        if (_isPlaylistAddedToSpotify && _spotifyPlaylistInfo != null) {
            return _spotifyPlaylistInfo!.canRefine;
        }

        if (_rateLimitStatus?.refinementLimitEnabled == true) {
            return _refinementsUsed < (_rateLimitStatus?.maxRefinements ?? 3);
        }

        return true;
    }

    bool get showRefinementLimits => _rateLimitStatus?.refinementLimitEnabled ?? false;
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

    Future<void> generatePlaylist(String prompt) async {
        if (_deviceId == null) {
        await _initializeDeviceId();
        }

        _isLoading = true;
        _error = null;
        _refinementsUsed = 0;
        _isPlaylistAddedToSpotify = false;
        _spotifyPlaylistInfo = null;

        notifyListeners();

        try {
            final sessionId = _authService.sessionId;

            if (sessionId == null) {
                throw Exception('Not authenticated');
            }

            final request = PlaylistRequest(
                prompt: prompt,
                deviceId: _deviceId!,
                sessionId: sessionId,
                userContext: _userContext,
            );

            final response = await _apiService.generatePlaylist(request);

            _currentPlaylist = response.songs;
            _currentPrompt = prompt;
            _currentPlaylistId = response.playlistId;
            _error = null;

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

    Future<void> refinePlaylist(String refinementPrompt) async {
        if (_deviceId == null || !canRefine) return;

        _isLoading = true;
        _error = null;

        notifyListeners();

        try {
            final sessionId = _authService.sessionId;

            if (sessionId == null) {
                throw Exception('Not authenticated');
            }

            PlaylistResponse response;

            if (_isPlaylistAddedToSpotify && _spotifyPlaylistInfo != null) {
                response = await _apiService.refineSpotifyPlaylist(
                    spotifyPlaylistId: _spotifyPlaylistInfo!.id,
                    prompt: refinementPrompt,
                    deviceId: _deviceId!,
                    sessionId: sessionId,
                );
 
                _spotifyPlaylistInfo = SpotifyPlaylistInfo(
                    id: _spotifyPlaylistInfo!.id,
                    name: _spotifyPlaylistInfo!.name,
                    description: _spotifyPlaylistInfo!.description,
                    tracksCount: response.songs.length,
                    refinementsUsed: _spotifyPlaylistInfo!.refinementsUsed + 1,
                    maxRefinements: _spotifyPlaylistInfo!.maxRefinements,
                    canRefine: (_spotifyPlaylistInfo!.refinementsUsed + 1) < _spotifyPlaylistInfo!.maxRefinements,
                    spotifyUrl: _spotifyPlaylistInfo!.spotifyUrl,
                    images: _spotifyPlaylistInfo!.images,
                );
            }

            else {
                final request = PlaylistRequest(
                    prompt: refinementPrompt,
                    deviceId: _deviceId!,
                    sessionId: sessionId,
                    userContext: _userContext,
                    currentSongs: _currentPlaylist,
                    playlistId: _currentPlaylistId,
                );

                response = await _apiService.refinePlaylist(request);
            }

            _currentPlaylist = response.songs;

            if (!_isPlaylistAddedToSpotify || _spotifyPlaylistInfo == null) {
                _currentPlaylistId = response.playlistId;
                _refinementsUsed++;
            }

            _error = null;
            _loadRateLimitStatus();
        }

        catch (e, stackTrace) {
            AppLogger.error('Playlist refinement error', error: e, stackTrace: stackTrace);

            if (e.toString().contains('timeout')) {
                _error = 'Refinement timed out. Please try again.';
            }

            else if (e.toString().contains('authentication')) {
                _error = 'Authentication error. Please log in again.';
            }

            else {
                _error = 'Failed to refine playlist. Please try again.';
            }
        }

        finally {
            _isLoading = false;
            notifyListeners();
        }
    }

    void removeSong(Song song) {
        _currentPlaylist.removeWhere((s) => s == song);
        notifyListeners();
    }

    void addSong(Song song) {
        if (!_currentPlaylist.contains(song)) {
            _currentPlaylist.add(song);
            notifyListeners();
        }
    }

    void reorderSongs(int oldIndex, int newIndex) {
        if (newIndex > oldIndex) {
            newIndex -= 1;
        }

        final Song song = _currentPlaylist.removeAt(oldIndex);
        _currentPlaylist.insert(newIndex, song);
        notifyListeners();
    }

    void clearPlaylist() {
        _currentPlaylist = [];
        _currentPrompt = '';
        _currentPlaylistId = null;
        _refinementsUsed = 0;
        _isPlaylistAddedToSpotify = false;
        _spotifyPlaylistInfo = null;
        _error = null;

        notifyListeners();
    }

    Future<void> _loadRateLimitStatus() async {
        try {
            _rateLimitStatus = await getRateLimitStatus();
            notifyListeners();
        }

        catch (e) {
            developer.log(
                'Failed to load rate limit status: $e',
                name: 'PlaylistProvider._loadRateLimitStatus',
                error: e,
            );
        }
    }

    /// Public method to refresh rate limit status (for daily limit refresh)
    Future<void> refreshRateLimitStatus() async {
        await _loadRateLimitStatus();
    }

    Future<String> addToSpotify({required String playlistName, String? description}) async {
        if (_currentPlaylistId == null) {
            if (_currentPlaylist.isEmpty) {
                throw Exception('No playlist to add to Spotify');
            }

            if (_deviceId == null) {
                await _initializeDeviceId();
            }

            final sessionId = _authService.sessionId;

            if (sessionId == null) {
                throw Exception('Not authenticated');
            }

            final request = PlaylistRequest(
                prompt: _currentPrompt.isNotEmpty ? _currentPrompt : 'Spotify playlist update',
                deviceId: _deviceId!,
                sessionId: sessionId,
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.refinePlaylist(request);
            _currentPlaylistId = response.playlistId;
        }

        if (_deviceId == null) {
            await _initializeDeviceId();
        }

        final sessionId = _authService.sessionId;

        if (sessionId == null) {
            throw Exception('Not authenticated');
        }

        _isAddingToSpotify = true;
        notifyListeners();

        try {
            final request = SpotifyPlaylistRequest(
                playlistId: _currentPlaylistId!,
                deviceId: _deviceId!,
                sessionId: sessionId,
                name: playlistName,
                description: description,
                public: false,
            );

            final response = await _apiService.createSpotifyPlaylist(request);

            if (response.success) {
                _isPlaylistAddedToSpotify = true;
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
            try {
                return await _apiService.getAuthenticatedRateLimitStatus(
                    _authService.sessionId!,
                    _deviceId!
                );
            }

            catch (e, stackTrace) {
                developer.log(
                    'Authenticated rate limit check failed, falling back: $e',
                    name: 'PlaylistProvider.getRateLimitStatus',
                    error: e,
                    stackTrace: stackTrace,
                );

                return await _apiService.getRateLimitStatus(_deviceId!);
            }
        }

        else {
            return await _apiService.getRateLimitStatus(_deviceId!);
        }
    }

    Future<LibraryPlaylistsResponse> getLibraryPlaylists() async {
        if (_deviceId == null) {
            await _initializeDeviceId();
        }

        final sessionId = _authService.sessionId;

        if (sessionId == null) {
            throw Exception('Not authenticated');
        }

        final request = LibraryPlaylistsRequest(
            deviceId: _deviceId!,
            sessionId: sessionId,
            includeDrafts: true,
        );

        return await _apiService.getLibraryPlaylists(request);
    }

    Future<void> loadDraft(PlaylistDraft draft) async {
        _currentPlaylist = draft.songs;
        _currentPrompt = draft.prompt;
        _currentPlaylistId = draft.id;
        _refinementsUsed = draft.refinementsUsed;
        _isPlaylistAddedToSpotify = draft.isAddedToSpotify;
        _spotifyPlaylistInfo = null;
        _error = null;

        notifyListeners();
    }

    Future<void> deleteDraft(String playlistId) async {
        if (_deviceId == null) {
            await _initializeDeviceId();
        }

        await _apiService.deleteDraftPlaylist(playlistId, _deviceId!);
    }

    Future<void> deleteSpotifyPlaylist(String playlistId) async {
        if (_deviceId == null) {
            await _initializeDeviceId();
        }

        final sessionId = _authService.sessionId;

        if (sessionId == null) {
            throw Exception('Not authenticated');
        }

        await _apiService.deleteSpotifyPlaylist(playlistId, sessionId, _deviceId!);
    }

    Future<void> loadSpotifyPlaylist(Map<String, dynamic> spotifyPlaylist) async {
        _isLoading = true;
        _error = null;

        notifyListeners();

        try {
            if (_deviceId == null) {
                await _initializeDeviceId();
            }

            final sessionId = _authService.sessionId;

            if (sessionId == null) {
                throw Exception('Not authenticated');
            }

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
            _refinementsUsed = 0;
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

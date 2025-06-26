import 'package:flutter/material.dart';
import 'dart:developer' as developer;

import '../models/rate_limit_models.dart';
import '../services/device_service.dart';
import '../models/playlist_request.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/user_context.dart';
import '../models/song.dart';

class PlaylistProvider extends ChangeNotifier {
    final ApiService _apiService;
    final AuthService _authService;
    
    List<Song> _currentPlaylist = [];
    String _currentPrompt = '';

    int _refinementsUsed = 0;
    bool _isLoading = false;

    UserContext? _userContext;
    RateLimitStatus? _rateLimitStatus;

    String? _deviceId;
    String? _error;

    PlaylistProvider({required ApiService apiService, required AuthService authService}) : _apiService = apiService, _authService = authService {
        _initializeDeviceId();
        _loadRateLimitStatus();
    }

    List<Song> get currentPlaylist => _currentPlaylist;

    String get currentPrompt => _currentPrompt;
    int get refinementsUsed => _refinementsUsed;
    RateLimitStatus? get rateLimitStatus => _rateLimitStatus;

    bool get canRefine {
        if (_rateLimitStatus?.refinementLimitEnabled == true) {
            return _refinementsUsed < (_rateLimitStatus?.maxRefinements ?? 3);
        }

        return true;
    }
    
    bool get showRefinementLimits => _rateLimitStatus?.refinementLimitEnabled ?? false;
    bool get showPlaylistLimits => _rateLimitStatus?.playlistLimitEnabled ?? false;
    
    bool get isLoading => _isLoading;

    UserContext? get userContext => _userContext;
    String? get error => _error;

    Future<void> _initializeDeviceId() async {
        _deviceId = await DeviceService.getDeviceId();
    }

    void updateUserContext(UserContext context) {
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
            _error = null;
            
            _loadRateLimitStatus();
        }
        
        catch (e, stackTrace) {
            debugPrint('Playlist generation error: $e');
            debugPrint('Stack trace: $stackTrace');

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

            final request = PlaylistRequest(
                prompt: refinementPrompt,
                deviceId: _deviceId!,
                sessionId: sessionId,
                userContext: _userContext,
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.refinePlaylist(request);
            
            _currentPlaylist = response.songs;
            _refinementsUsed++;
            _error = null;

            _loadRateLimitStatus();
        }
        
        catch (e, stackTrace) {
            debugPrint('Playlist refinement error: $e');
            debugPrint('Stack trace: $stackTrace');
            
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
        _refinementsUsed = 0;
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

    Future<String> createSpotifyPlaylist({required String accessToken, required String playlistName, String? description}) async {
        if (_currentPlaylist.isEmpty) {
            throw Exception('No playlist to create');
        }

        return await _apiService.createSpotifyPlaylist(
            accessToken: accessToken,
            playlistName: playlistName,
            songs: _currentPlaylist,
            description: description,
        );
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
}

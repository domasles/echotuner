import 'package:flutter/material.dart';

import '../services/device_service.dart';
import '../models/playlist_request.dart';
import '../services/api_service.dart';
import '../models/user_context.dart';
import '../models/song.dart';

class PlaylistProvider extends ChangeNotifier {
    final ApiService _apiService;
    
    List<Song> _currentPlaylist = [];
    String _currentPrompt = '';

    int _refinementsUsed = 0;
    bool _isLoading = false;

    UserContext? _userContext;

    String? _deviceId;
    String? _error;

    PlaylistProvider({required ApiService apiService}) : _apiService = apiService {
        _initializeDeviceId();
    }

    List<Song> get currentPlaylist => _currentPlaylist;

    String get currentPrompt => _currentPrompt;
    int get refinementsUsed => _refinementsUsed;

    bool get canRefine => _refinementsUsed < 3;
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
            final request = PlaylistRequest(
                prompt: prompt,
                deviceId: _deviceId!,
                userContext: _userContext,
            );

            final response = await _apiService.generatePlaylist(request);
            
            _currentPlaylist = response.songs;
            _currentPrompt = prompt;
            _error = null;
        }
        
        catch (e) {
            _error = e.toString();
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
            final request = PlaylistRequest(
                prompt: refinementPrompt,
                deviceId: _deviceId!,
                userContext: _userContext,
                currentSongs: _currentPlaylist,
            );

            final response = await _apiService.refinePlaylist(request);
            
            _currentPlaylist = response.songs;
            _refinementsUsed++;
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

    Future<Map<String, dynamic>> getRateLimitStatus() async {
        if (_deviceId == null) {
            await _initializeDeviceId();
        }
        
        return await _apiService.getRateLimitStatus(_deviceId!);
    }
}

import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/playlist_request.dart';
import '../models/rate_limit_models.dart';
import '../models/playlist_draft_models.dart';
import '../config/app_config.dart';

class ApiService {
    final http.Client _client = http.Client();

    Future<PlaylistResponse> generatePlaylist(PlaylistRequest request) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/generate-playlist')),
            
            headers: {
                'Content-Type': 'application/json',
            },

            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return PlaylistResponse.fromJson(jsonDecode(response.body));
        }
        
        else if (response.statusCode == 429) {
            throw ApiException('Daily limit reached. Try again tomorrow.');
        }
        
        else if (response.statusCode == 400) {
            final error = jsonDecode(response.body);
            throw ApiException(error['detail'] ?? 'Invalid request');
        }
        
        else {
            throw ApiException('Failed to generate playlist. Please try again.');
        }
    }

    Future<PlaylistResponse> refinePlaylist(PlaylistRequest request) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/refine-playlist')),
            
            headers: {
                'Content-Type': 'application/json',
            },

            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return PlaylistResponse.fromJson(jsonDecode(response.body));
        }
        
        else if (response.statusCode == 429) {
            throw ApiException('Maximum refinements reached for this playlist.');
        }
        
        else if (response.statusCode == 400) {
            final error = jsonDecode(response.body);
            throw ApiException(error['detail'] ?? 'Invalid refinement request');
        }
        
        else {
            throw ApiException('Failed to refine playlist. Please try again.');
        }
    }

    Future<RateLimitStatus> getRateLimitStatus(String deviceId) async {
        final response = await _client.get(
            Uri.parse(AppConfig.apiUrl('/rate-limit-status/$deviceId')),
        );

        if (response.statusCode == 200) {
            return RateLimitStatus.fromJson(jsonDecode(response.body));
        }
        
        else {
            throw ApiException('Failed to get rate limit status');
        }
    }

    Future<RateLimitStatus> getAuthenticatedRateLimitStatus(String sessionId, String deviceId) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/auth/rate-limit-status')),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
                'session_id': sessionId,
                'device_id': deviceId,
            }),
        );

        if (response.statusCode == 200) {
            return RateLimitStatus.fromJson(jsonDecode(response.body));
        }
        
        else if (response.statusCode == 401) {
            throw ApiException('Authentication required');
        }
        
        else {
            throw ApiException('Failed to get rate limit status');
        }
    }

    Future<bool> checkApiHealth() async {
        try {
            final response = await _client.get(Uri.parse(AppConfig.apiUrl('/health'))).timeout(const Duration(seconds: 5));
            return response.statusCode == 200;
        }
        
        catch (e) {
            return false;
        }
    }

    Future<SpotifyPlaylistResponse> createSpotifyPlaylist(SpotifyPlaylistRequest request) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/spotify/create-playlist')),

            headers: {
                'Content-Type': 'application/json',
            },

            body: jsonEncode(request.toJson()),
        ).timeout(const Duration(seconds: 30)); // Add reasonable timeout for Spotify API

        if (response.statusCode == 200) {
            return SpotifyPlaylistResponse.fromJson(jsonDecode(response.body));
        }
        else if (response.statusCode == 401) {
            throw ApiException('Authentication required');
        }
        else if (response.statusCode == 404) {
            throw ApiException('Draft playlist not found');
        }
        else {
            throw ApiException('Failed to create Spotify playlist');
        }
    }

    Future<LibraryPlaylistsResponse> getLibraryPlaylists(LibraryPlaylistsRequest request) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/library/playlists')),

            headers: {
                'Content-Type': 'application/json',
            },

            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return LibraryPlaylistsResponse.fromJson(jsonDecode(response.body));
        }
        else if (response.statusCode == 401) {
            throw ApiException('Authentication required');
        }
        else {
            throw ApiException('Failed to get library playlists');
        }
    }

    Future<PlaylistDraft> getDraftPlaylist(String playlistId, String deviceId) async {
        final response = await _client.get(
            Uri.parse(AppConfig.apiUrl('/drafts/$playlistId?device_id=$deviceId')),
        );

        if (response.statusCode == 200) {
            return PlaylistDraft.fromJson(jsonDecode(response.body));
        }
        else if (response.statusCode == 404) {
            throw ApiException('Draft playlist not found');
        }
        else if (response.statusCode == 403) {
            throw ApiException('Access denied');
        }
        else {
            throw ApiException('Failed to get draft playlist');
        }
    }

    Future<bool> deleteDraftPlaylist(String playlistId, String deviceId) async {
        final response = await _client.delete(
            Uri.parse(AppConfig.apiUrl('/drafts/$playlistId?device_id=$deviceId')),
        );

        return response.statusCode == 200;
    }

    Future<List<Map<String, dynamic>>> getSpotifyPlaylistTracks(
        String playlistId, 
        String sessionId, 
        String deviceId
    ) async {
        final response = await _client.get(
            Uri.parse(AppConfig.apiUrl('/spotify/playlist/$playlistId/tracks?session_id=$sessionId&device_id=$deviceId')),
        );

        if (response.statusCode == 200) {
            final data = json.decode(response.body);
            return List<Map<String, dynamic>>.from(data['tracks']);
        }
        else {
            throw ApiException('Failed to get Spotify playlist tracks');
        }
    }

    void dispose() {
        _client.close();
    }
}

class ApiException implements Exception {
    final String message;
    ApiException(this.message);
    
    @override
    String toString() => message;
}

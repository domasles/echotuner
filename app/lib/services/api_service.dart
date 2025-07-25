import 'package:http/http.dart' as http;
import 'dart:convert';

import '../models/playlist_draft_models.dart';
import '../models/rate_limit_models.dart';
import '../models/playlist_request.dart';
import '../models/app_config.dart';
import '../utils/app_logger.dart';
import '../config/settings.dart';
import 'auth_service.dart';

class ApiService {
    final http.Client _client = http.Client();
    AuthService? _authService;

    void setAuthService(AuthService authService) {
        _authService = authService;
    }

    Future<void> _handle401() async {
        AppLogger.api('Received 401 - triggering logout');

        if (_authService != null) {
            await _authService!.logout();
        }
    }

    Future<Map<String, dynamic>> get(String endpoint, {Map<String, String>? headers}) async {
        AppLogger.api('GET $endpoint');

        final response = await _client.get(
            Uri.parse(AppConfig.apiUrl(endpoint)),
            headers: headers,
        );

        if (response.statusCode == 200) {
            AppLogger.api('GET $endpoint - Success');
            return jsonDecode(response.body);
        }

        else if (response.statusCode == 401) {
            AppLogger.api('GET $endpoint - 401 Unauthorized');
            await _handle401();
            throw ApiException('Authentication required');
        }

        else if (response.statusCode == 404) {
            AppLogger.api('GET $endpoint - 404 Not Found');
            throw ApiException('Resource not found');
        }

        else {
            throw ApiException('Request failed with status ${response.statusCode}');
        }
    }

    Future<Map<String, dynamic>> post(String endpoint, {Map<String, dynamic>? body, Map<String, String>? headers}) async {
        AppLogger.api('POST $endpoint');

        final defaultHeaders = {'Content-Type': 'application/json'};
        final mergedHeaders = headers != null ? {...defaultHeaders, ...headers} : defaultHeaders;

        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl(endpoint)),
            headers: mergedHeaders,
            body: body != null ? jsonEncode(body) : null,
        );

        if (response.statusCode == 200) {
            AppLogger.api('POST $endpoint - Success');
            return jsonDecode(response.body);
        }

        else if (response.statusCode == 401) {
            AppLogger.api('POST $endpoint - 401 Unauthorized');
            await _handle401();
            throw ApiException('Authentication required');
        }

        else if (response.statusCode == 404) {
            AppLogger.api('POST $endpoint - 404 Not Found');
            throw ApiException('Resource not found');
        }

        else {
            AppLogger.api('POST $endpoint - ${response.statusCode} Error');
            throw ApiException('Request failed with status ${response.statusCode}');
        }
    }

    Future<PlaylistResponse> generatePlaylist(PlaylistRequest request) async {
        final userId = _authService?.userId;
        if (userId == null) {
            throw ApiException('User not authenticated');
        }

        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/playlist/generate')),

            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId,
            },

            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return PlaylistResponse.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
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

    Future<RateLimitStatus> getRateLimitStatus(String deviceId) async {
        final response = await _client.get(
            Uri.parse(AppConfig.apiUrl('/rate-limit-status/$deviceId')),
        );

        if (response.statusCode == 200) {
            return RateLimitStatus.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
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
            await _handle401();
            throw ApiException('Authentication required');
        }

        else {
            throw ApiException('Failed to get rate limit status');
        }
    }

    Future<bool> checkApiHealth() async {
        try {
            AppLogger.api('Checking API health');

            final response = await _client.get(Uri.parse(AppConfig.apiUrl('/config/health'))).timeout(const Duration(seconds: 5));
            final isHealthy = response.statusCode == 200;

            AppLogger.api('API health check: ${isHealthy ? 'Healthy' : 'Unhealthy'}');

            return isHealthy;
        }

        catch (e) {
            AppLogger.api('API health check failed', error: e);
            return false;
        }
    }

    Future<AppConfigData> getConfig() async {
        final response = await _client.get(Uri.parse(AppConfig.apiUrl('/config')));
        
        if (response.statusCode == 200) {
            return AppConfigData.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        else {
            throw ApiException('Failed to get configuration');
        }
    }

    Future<SpotifyPlaylistResponse> createSpotifyPlaylist(SpotifyPlaylistRequest request) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/spotify/create-playlist')),

            headers: {
                'Content-Type': 'application/json',
            },

            body: jsonEncode(request.toJson()),
        ).timeout(const Duration(seconds: 30));

        if (response.statusCode == 200) {
            return SpotifyPlaylistResponse.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
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
        final userId = _authService?.userId;
        if (userId == null) {
            throw ApiException('User not authenticated');
        }

        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/playlist/library')),

            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId,
            },

            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return LibraryPlaylistsResponse.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        else {
            throw ApiException('Failed to get library playlists');
        }
    }

    Future<PlaylistDraft> getDraftPlaylist(String playlistId, String userId) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/playlist/drafts')),
            headers: {
                'Content-Type': 'application/json',
            },
            body: jsonEncode({
                'playlist_id': playlistId,
                'user_id': userId,
            }),
        );

        if (response.statusCode == 200) {
            return PlaylistDraft.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
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

    Future<bool> deleteDraftPlaylist(String playlistId, String userId) async {
        final response = await _client.delete(
            Uri.parse(AppConfig.apiUrl('/playlist/drafts')),
            headers: {
                'Content-Type': 'application/json',
            },
            body: jsonEncode({
                'playlist_id': playlistId,
                'user_id': userId,
            }),
        );

        if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        return response.statusCode == 200;
    }

    Future<bool> deleteSpotifyPlaylist(String playlistId, String userId) async {
        final response = await _client.delete(
            Uri.parse(AppConfig.apiUrl('/spotify/playlist')),
            headers: {
                'Content-Type': 'application/json',
            },
            body: jsonEncode({
                'playlist_id': playlistId,
                'user_id': userId,
            }),
        );

        if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        return response.statusCode == 200;
    }

    Future<bool> removeTrackFromSpotifyPlaylist(String playlistId, String trackUri, String userId) async {
        final response = await _client.delete(
            Uri.parse(AppConfig.apiUrl('/spotify/playlist/track')),
            headers: {
                'Content-Type': 'application/json',
            },
            body: jsonEncode({
                'playlist_id': playlistId,
                'track_uri': trackUri,
                'user_id': userId,
            }),
        );

        if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        return response.statusCode == 200;
    }

    Future<List<Map<String, dynamic>>> getSpotifyPlaylistTracks(String playlistId, String userId) async {
        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/spotify/playlist/tracks')),
            headers: {
                'Content-Type': 'application/json',
            },
            body: jsonEncode({
                'playlist_id': playlistId,
                'user_id': userId,
            }),
        );

        if (response.statusCode == 200) {
            final data = json.decode(response.body);
            return List<Map<String, dynamic>>.from(data['tracks']);
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        else {
            throw ApiException('Failed to get Spotify playlist tracks');
        }
    }

    Future<PlaylistResponse> updatePlaylistDraft(PlaylistRequest request) async {
        final userId = _authService?.userId;
        if (userId == null) {
            throw ApiException('User not authenticated');
        }

        final response = await _client.post(
            Uri.parse(AppConfig.apiUrl('/playlist/update-draft')),
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId,
            },
            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return PlaylistResponse.fromJson(jsonDecode(response.body));
        }

        else if (response.statusCode == 401) {
            await _handle401();
            throw ApiException('Authentication required');
        }

        else if (response.statusCode == 404) {
            throw ApiException('Draft playlist not found.');
        }

        else if (response.statusCode == 400) {
            final error = jsonDecode(response.body);
            throw ApiException(error['detail'] ?? 'Invalid update request');
        }

        else {
            throw ApiException('Failed to update draft playlist. Please try again.');
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

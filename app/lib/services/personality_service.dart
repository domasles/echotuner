import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

import '../services/config_service.dart';
import '../services/auth_service.dart';
import '../models/user_context.dart';
import '../utils/app_logger.dart';

import 'api_service.dart';

class PersonalityService {
    static const String _lastSyncKey = 'last_artist_sync';
    static const String _demoPersonalityKey = 'demo_personality';

    final ApiService _apiService;
    final AuthService _authService;
    final ConfigService _configService;

    PersonalityService({required ApiService apiService, required AuthService authService, required ConfigService configService}) : _apiService = apiService, _authService = authService, _configService = configService;

    Future<bool> _isDemoAccount() async {
        try {
            final sessionId = await _getSessionId();
            if (sessionId == null) return false;
            
            final deviceId = await _getDeviceId();
            if (deviceId == null) return false;
            
            AppLogger.personality('Checking account type for session: ${sessionId.substring(0, 8)}...');

            final response = await _apiService.post('/auth/account-type', body: {
                'session_id': sessionId,
                'device_id': deviceId
            });

            final isDemo = response['account_type'] == 'demo';
            AppLogger.personality('Account type check result: isDemo=$isDemo');

            return isDemo;
        }

        catch (e) {
            AppLogger.personality('Failed to get account type: $e');

            if (e.toString().contains('404') || e.toString().contains('401')) {
                AppLogger.personality('Session invalid, triggering logout for re-authentication');
                await _authService.logout();
            }

            return false;
        }
    }

    Future<bool> isDemoAccount() async {
        return await _isDemoAccount();
    }

    Future<void> saveUserContext(UserContext context) async {
        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) {
            AppLogger.personality('Demo account: Saving context locally...');
            AppLogger.personality('Demo account: Context to save: ${context.toJson()}');

            final prefs = await SharedPreferences.getInstance();
            await prefs.setString(_demoPersonalityKey, jsonEncode(context.toJson()));

            AppLogger.personality('Demo account: Context saved locally successfully');

            return;
        }

        AppLogger.personality('Saving context to API...');
        AppLogger.personality('Context data: ${context.toJson()}');

        final response = await _apiService.post('/personality/save', body: {
            'session_id': await _getSessionId(),                              
            'device_id': await _getDeviceId(),
            'user_context': context.toJson(),
        });

        AppLogger.personality('API response: $response');

        if (!response['success']) {
            throw Exception(response['message'] ?? 'Failed to save personality to server');
        }

        AppLogger.personality('API save successful');
    }

    Future<UserContext?> loadUserContext() async {
        final isDemoAccount = await _isDemoAccount();

        if (isDemoAccount) {
            AppLogger.personality('Demo account: Loading context from local storage...');

            final prefs = await SharedPreferences.getInstance();
            final personalityJson = prefs.getString(_demoPersonalityKey);

            AppLogger.personality('Demo account: Raw data from storage: $personalityJson');

            if (personalityJson != null) {
                try {
                    final contextData = jsonDecode(personalityJson);
                    final context = UserContext.fromJson(contextData);

                    AppLogger.personality('Demo account: Loaded context from local storage: ${context.toJson()}');

                    return context;
                }

                catch (e) {
                    AppLogger.personality('Demo account: Failed to parse local personality: $e');
                }
            }

            AppLogger.personality('Demo account: No local personality found - returning null');
            return null;
        }

        AppLogger.personality('Loading context from API...');

        try {
            final response = await _apiService.get('/personality/load', headers: {
                'session_id': await _getSessionId() ?? '',
                'device_id': await _getDeviceId() ?? '',
            });

            final userContextData = response['user_context'];

            if (userContextData != null) {
                AppLogger.personality('Loaded context from API: $userContextData');
                return UserContext.fromJson(userContextData);
            }

            AppLogger.personality('No context found in API');
            return null;
        }

        catch (e) {
            AppLogger.personality('Failed to load context from API: $e');

            if (e.toString().contains('401') || e.toString().contains('404')) {
                AppLogger.personality('Session invalid, triggering logout for re-authentication');
                await _authService.logout();
            }

            return null;
        }
    }

    Future<void> clearUserContext() async {
        AppLogger.personality('Clearing context from API ONLY...');

        await _apiService.post('/personality/clear', body: {
            'session_id': await _getSessionId(),
            'device_id': await _getDeviceId(),
        });

        AppLogger.personality('Context cleared from API');
    }

    Future<List<SpotifyArtist>> fetchFollowedArtists({String? sessionId}) async {
        try {
            final isDemoAccount = await _isDemoAccount();

            if (isDemoAccount) {
                AppLogger.personality('Demo account: Skipping followed artists fetch');
                return [];
            }
            
            final sessionIdToUse = sessionId ?? await _getSessionId();
            if (sessionIdToUse == null) throw Exception('No session ID available');

            final response = await _apiService.get('/personality/followed-artists', headers: {
                'session_id': sessionIdToUse,
                'device_id': await _getDeviceId() ?? '',
            });

            final List<dynamic> artistsJson = response['artists'] ?? [];
            final config = await _configService.getPersonalityConfig();

            return artistsJson.map((json) => SpotifyArtist.fromJson(json)).take(config.maxFavoriteArtists).toList();
        }

        catch (e) {
            AppLogger.personality('Failed to fetch followed artists: $e');

            if (e.toString().contains('401') || e.toString().contains('404')) {
                AppLogger.personality('Session invalid, triggering logout for re-authentication');
                await _authService.logout();
            }

            return [];
        }
    }

    Future<List<SpotifyArtist>> searchArtists(String query) async {
        try {
            final sessionId = await _getSessionId();

            if (sessionId == null) {
                throw Exception('No session ID available');
            }

            final response = await _apiService.post('/personality/search-artists', body: {
                'session_id': sessionId,
                'device_id': await _getDeviceId(),
                'query': query,
                'limit': 20,
            });

            final List<dynamic> artistsJson = response['artists'] ?? [];

            return artistsJson
                .map((json) => SpotifyArtist.fromJson(json))
                .toList();
        }

        catch (e) {
            AppLogger.personality('Failed to search artists: $e');

            if (e.toString().contains('401') || e.toString().contains('404')) {
                AppLogger.personality('Session invalid, triggering logout for re-authentication');
                await _authService.logout();
            }

            return [];
        }
    }

    Future<String?> _getSessionId() async {
        return _authService.sessionId;
    }

    Future<String?> _getDeviceId() async {
        return _authService.deviceId;
    }

    Future<bool> shouldSyncArtists() async {
        final prefs = await SharedPreferences.getInstance();
        final lastSync = prefs.getInt(_lastSyncKey);

        if (lastSync == null) return true;

        final lastSyncDate = DateTime.fromMillisecondsSinceEpoch(lastSync);
        final now = DateTime.now();

        return now.difference(lastSyncDate).inHours >= 24;
    }

    Future<void> markArtistsSynced() async {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt(_lastSyncKey, DateTime.now().millisecondsSinceEpoch);
    }

    Future<UserContext> getDefaultPersonalityContext({String? sessionId}) async {
        final followedArtists = sessionId != null ? await fetchFollowedArtists(sessionId: sessionId) : <SpotifyArtist>[];

        return UserContext(
            favoriteArtists: followedArtists.map((artist) => artist.name).toList(),
            favoriteGenres: [],
            dislikedArtists: [],
            musicDiscoveryPreference: null,
            energyPreference: null,
            discoveryOpenness: null,
            explicitContentPreference: null,
            instrumentalPreference: null,
            decadePreference: [], // Empty by default
        );
    }

    List<String> getAvailableGenres() {
        return [
            'Pop', 'Rock', 'Hip Hop', 'R&B', 'Country', 'Electronic',
            'Jazz', 'Classical', 'Reggae', 'Blues', 'Folk', 'Punk',
            'Alternative', 'Indie', 'Metal', 'Funk', 'Soul', 'Gospel',
            'Latin', 'World', 'Ambient', 'House', 'Techno', 'Dubstep',
            'Drum & Bass', 'Trance', 'Reggaeton', 'K-Pop', 'J-Pop',
            'Afrobeat', 'Bossa Nova', 'Synthwave', 'Lo-fi', 'Shoegaze'
        ];
    }

    List<String> getAvailableDecades() {
        return [
            '1920s', '1930s', '1940s', '1950s', '1960s', '1970s', '1980s', '1990s', 
            '2000s', '2010s', '2020s'
        ];
    }

    Map<String, Map<String, dynamic>> getPersonalityQuestions() {
        return {
            'music_activity_preference': {
                'question': 'When do you listen to music most?',
                'options': [
                    'While working or studying',
                    'During workouts and exercise',
                    'For relaxation and downtime',
                    'At parties and social events',
                    'When feeling emotional'
                ],
                'type': 'single_choice'
            },
            'energy_preference': {
                'question': 'What energy level do you prefer in music?',
                'options': [
                    'High energy and upbeat',
                    'Moderate and balanced',
                    'Low energy and calm',
                    'Depends on my mood'
                ],
                'type': 'single_choice'
            },
            'genre_openness': {
                'question': 'How would you describe your music taste?',
                'options': [
                    'I stick to a few favorite genres',
                    'I enjoy a wide variety of genres',
                    'I like mixing familiar and new styles',
                    'I prefer what\'s currently popular'
                ],
                'type': 'single_choice'
            },
            'vocal_preference': {
                'question': 'Do you prefer music with or without vocals?',
                'options': [
                    'Always with vocals and lyrics',
                    'Usually with vocals',
                    'Good mix of both',
                    'Often instrumental',
                    'Depends on the situation'
                ],
                'type': 'single_choice'
            },
            'explicit_content_preference': {
                'question': 'How do you feel about explicit content in music?',
                'options': [
                    'No problem with explicit content',
                    'Prefer clean versions when available',
                    'Avoid explicit content'
                ],
                'type': 'single_choice'
            },
            'discovery_openness': {
                'question': 'How open are you to discovering new music?',
                'options': [
                    'I love discovering new artists',
                    'I enjoy some new music',
                    'I prefer familiar songs',
                    'I stick to what I know'
                ],
                'type': 'single_choice'
            },
            'instrumental_preference': {
                'question': 'How do you feel about instrumental music?',
                'options': [
                    'I love instrumental music',
                    'I enjoy it sometimes',
                    'I prefer music with vocals',
                    'I rarely listen to instrumental'
                ],
                'type': 'single_choice'
            },
            'music_discovery_preference': {
                'question': 'How do you prefer to discover music?',
                'options': [
                    'Through recommendations',
                    'By exploring similar artists',
                    'Through popular charts',
                    'By genre exploration',
                    'Random discovery'
                ],
                'type': 'single_choice'
            }
        };
    }
}

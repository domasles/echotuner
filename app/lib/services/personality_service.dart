import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_context.dart';
import '../services/auth_service.dart';
import '../services/config_service.dart';
import 'api_service.dart';

class PersonalityService {
    static const String _userContextKey = 'user_context';
    static const String _lastSyncKey = 'last_artist_sync';

    final ApiService _apiService;
    final AuthService _authService;
    final ConfigService _configService;

    PersonalityService({
        required ApiService apiService, 
        required AuthService authService,
        required ConfigService configService,
    }) : _apiService = apiService, 
         _authService = authService,
         _configService = configService;

    /// Save user context to backend
    Future<void> saveUserContext(UserContext context) async {
        try {
            final response = await _apiService.post('/personality/save', body: {
                'session_id': await _getSessionId(),
                'device_id': await _getDeviceId(),
                'user_context': context.toJson(),
            });
            
            if (!response['success']) {
                throw Exception(response['message'] ?? 'Failed to save personality');
            }
        } catch (e) {
            throw Exception('Failed to save personality: $e');
        }
    }

    /// Load user context from backend
    Future<UserContext?> loadUserContext() async {
        try {
            final response = await _apiService.get('/personality/load', headers: {
                'session-id': await _getSessionId() ?? '',
                'device-id': await _getDeviceId() ?? '',
            });
            
            final userContextData = response['user_context'];
            if (userContextData != null) {
                return UserContext.fromJson(userContextData);
            }
            
            return null;
        } catch (e) {
            return null;
        }
    }

    /// Clear user context from backend and local storage
    Future<void> clearUserContext() async {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove(_userContextKey);
        await prefs.remove(_lastSyncKey);
        // Note: Could add backend clear endpoint if needed
    }

    /// Fetch user's followed artists from backend
    Future<List<SpotifyArtist>> fetchFollowedArtists({String? sessionId}) async {
        try {
            final sessionIdToUse = sessionId ?? await _getSessionId();
            if (sessionIdToUse == null) {
                throw Exception('No session ID available');
            }

            final response = await _apiService.get('/user/followed-artists', headers: {
                'session-id': sessionIdToUse,
                'device-id': await _getDeviceId() ?? '',
            });

            final List<dynamic> artistsJson = response['artists'] ?? [];
            final config = await _configService.getPersonalityConfig();
            return artistsJson
                .map((json) => SpotifyArtist.fromJson(json))
                .take(config.maxFavoriteArtists)
                .toList();
        } catch (e) {
            // Return empty list if unable to fetch
            return [];
        }
    }

    /// Search for artists on Spotify
    Future<List<SpotifyArtist>> searchArtists(String query) async {
        try {
            final sessionId = await _getSessionId();
            if (sessionId == null) {
                throw Exception('No session ID available');
            }

            final response = await _apiService.post('/user/search-artists', body: {
                'session_id': sessionId,
                'device_id': await _getDeviceId(),
                'query': query,
                'limit': 20,
            });

            final List<dynamic> artistsJson = response['artists'] ?? [];
            return artistsJson
                .map((json) => SpotifyArtist.fromJson(json))
                .toList();
        } catch (e) {
            return [];
        }
    }

    /// Helper to get session ID from auth service
    Future<String?> _getSessionId() async {
        return _authService.sessionId;
    }

    /// Helper to get device ID
    Future<String?> _getDeviceId() async {
        return _authService.deviceId;
    }

    /// Check if artist sync is needed (daily refresh)
    Future<bool> shouldSyncArtists() async {
        final prefs = await SharedPreferences.getInstance();
        final lastSync = prefs.getInt(_lastSyncKey);
        
        if (lastSync == null) return true;
        
        final lastSyncDate = DateTime.fromMillisecondsSinceEpoch(lastSync);
        final now = DateTime.now();
        
        // Sync if it's been more than 24 hours
        return now.difference(lastSyncDate).inHours >= 24;
    }

    /// Mark that artists have been synced
    Future<void> markArtistsSynced() async {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt(_lastSyncKey, DateTime.now().millisecondsSinceEpoch);
    }

    /// Get default personality context with fetched artists
    Future<UserContext> getDefaultPersonalityContext({String? sessionId}) async {
        final followedArtists = sessionId != null 
            ? await fetchFollowedArtists(sessionId: sessionId)
            : <SpotifyArtist>[];

        return UserContext(
            favoriteArtists: followedArtists.map((artist) => artist.name).toList(),
            favoriteGenres: [],
            dislikedArtists: [],
            musicDiscoveryPreference: 'balanced',
            energyPreference: 'medium',
            discoveryOpenness: 'moderate',
            explicitContentPreference: 'allow',
            instrumentalPreference: 'mixed',
            decadePreference: ['2010s', '2020s'],
        );
    }

    /// Get all available music genres
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

    /// Get available decades
    List<String> getAvailableDecades() {
        return [
            '1960s', '1970s', '1980s', '1990s', 
            '2000s', '2010s', '2020s'
        ];
    }

    /// Get personality questions with their options
    Map<String, Map<String, dynamic>> getPersonalityQuestions() {
        return {
            'happy_music_preference': {
                'question': 'What do you like to listen to when you\'re happy?',
                'options': [
                    'Upbeat pop and dance music',
                    'Feel-good rock and indie',
                    'Energetic hip-hop and rap',
                    'Cheerful acoustic and folk',
                    'Electronic and EDM'
                ],
                'type': 'single_choice'
            },
            'sad_music_preference': {
                'question': 'What comforts you when you\'re feeling down?',
                'options': [
                    'Melancholic indie and alternative',
                    'Emotional ballads and slow songs',
                    'Classical and instrumental',
                    'R&B and soul',
                    'I prefer uplifting music to cheer me up'
                ],
                'type': 'single_choice'
            },
            'workout_music_preference': {
                'question': 'What gets you pumped during workouts?',
                'options': [
                    'High-energy electronic and EDM',
                    'Aggressive rock and metal',
                    'Motivational hip-hop and rap',
                    'Fast-paced pop hits',
                    'I don\'t listen to music while working out'
                ],
                'type': 'single_choice'
            },
            'focus_music_preference': {
                'question': 'What helps you concentrate while studying or working?',
                'options': [
                    'Instrumental and ambient',
                    'Lo-fi hip-hop and chillhop',
                    'Classical music',
                    'Nature sounds and white noise',
                    'Complete silence'
                ],
                'type': 'single_choice'
            },
            'relaxation_music_preference': {
                'question': 'What do you listen to when you want to relax?',
                'options': [
                    'Chill acoustic and indie',
                    'Ambient and new age',
                    'Jazz and blues',
                    'Soft rock and easy listening',
                    'Classical and orchestral'
                ],
                'type': 'single_choice'
            },
            'party_music_preference': {
                'question': 'What\'s your go-to for parties and social gatherings?',
                'options': [
                    'Dance and electronic hits',
                    'Hip-hop and rap',
                    'Pop chart-toppers',
                    'Classic rock anthems',
                    'Latin and reggaeton'
                ],
                'type': 'single_choice'
            },
            'discovery_openness': {
                'question': 'How open are you to discovering new music?',
                'options': [
                    'Very open - I love exploring new artists and genres',
                    'Moderately open - I like some new music mixed in',
                    'Somewhat cautious - I prefer familiar sounds',
                    'Conservative - I mostly stick to what I know'
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
            'instrumental_preference': {
                'question': 'What\'s your preference for instrumental vs vocal music?',
                'options': [
                    'Mostly vocal music with lyrics',
                    'Good mix of both',
                    'Mostly instrumental music',
                    'Depends on my mood/activity'
                ],
                'type': 'single_choice'
            }
        };
    }
}

import '../models/app_config.dart';

import 'api_service.dart';

class ConfigService {
    final ApiService _apiService;

    AppConfigData? _cachedConfig;
    ConfigService(this._apiService);

    Future<AppConfigData> getConfig({bool forceRefresh = false}) async {
        if (_cachedConfig != null && !forceRefresh) {
            return _cachedConfig!;
        }

        try {
            _cachedConfig = await _apiService.getConfig();
            return _cachedConfig!;
        }

        catch (e) {
            return _getDefaultConfig();
        }
    }

    void clearCache() {
        _cachedConfig = null;
    }

    AppConfigData _getDefaultConfig() {
        return const AppConfigData(
            personality: PersonalityConfig(
                maxFavoriteArtists: 12,
                maxDislikedArtists: 20,
                maxFavoriteGenres: 10,
                maxPreferredDecades: 5,
            ),

            playlists: PlaylistConfig(
                maxSongsPerPlaylist: 30,
                maxPlaylistsPerDay: 3,
                maxPromptLength: 128,
                maxPlaylistNameLength: 100,
            ),

            features: FeatureConfig(
                authRequired: true,
                playlistLimitEnabled: false,
            ),
        );
    }

    Future<PersonalityConfig> getPersonalityConfig() async {
        final config = await getConfig();
        return config.personality;
    }

    Future<PlaylistConfig> getPlaylistConfig() async {
        final config = await getConfig();
        return config.playlists;
    }

    Future<FeatureConfig> getFeatureConfig() async {
        final config = await getConfig();
        return config.features;
    }
}

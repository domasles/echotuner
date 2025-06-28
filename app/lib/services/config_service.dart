import '../models/app_config.dart';
import 'api_service.dart';

class ConfigService {
  final ApiService _apiService;
  AppConfigData? _cachedConfig;

  ConfigService(this._apiService);

  /// Get configuration from backend with caching
  Future<AppConfigData> getConfig({bool forceRefresh = false}) async {
    if (_cachedConfig != null && !forceRefresh) {
      return _cachedConfig!;
    }

    try {
      _cachedConfig = await _apiService.getConfig();
      return _cachedConfig!;
    } catch (e) {
      // If we can't fetch config, return default values
      return _getDefaultConfig();
    }
  }

  /// Clear cached configuration
  void clearCache() {
    _cachedConfig = null;
  }

  /// Get default configuration values (fallback)
  AppConfigData _getDefaultConfig() {
    return const AppConfigData(
      personality: PersonalityConfig(
        maxFavoriteArtists: 12,
        maxDislikedArtists: 20,
        maxFavoriteGenres: 10,
      ),
      playlists: PlaylistConfig(
        maxSongsPerPlaylist: 30,
        maxPlaylistsPerDay: 3,
        maxRefinementsPerPlaylist: 3,
      ),
      features: FeatureConfig(
        authRequired: true,
        playlistLimitEnabled: false,
        refinementLimitEnabled: false,
      ),
    );
  }

  /// Get specific personality limits
  Future<PersonalityConfig> getPersonalityConfig() async {
    final config = await getConfig();
    return config.personality;
  }

  /// Get specific playlist limits
  Future<PlaylistConfig> getPlaylistConfig() async {
    final config = await getConfig();
    return config.playlists;
  }

  /// Get feature flags
  Future<FeatureConfig> getFeatureConfig() async {
    final config = await getConfig();
    return config.features;
  }
}

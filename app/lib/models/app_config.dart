import 'package:json_annotation/json_annotation.dart';

part 'app_config.g.dart';

@JsonSerializable()
class AppConfigData {
    final PersonalityConfig personality;
    final PlaylistConfig playlists;
    final FeatureConfig features;

    const AppConfigData({
        required this.personality,
        required this.playlists,
        required this.features,
    });

    factory AppConfigData.fromJson(Map<String, dynamic> json) => _$AppConfigDataFromJson(json);
    Map<String, dynamic> toJson() => _$AppConfigDataToJson(this);
}

@JsonSerializable()
class PersonalityConfig {
    @JsonKey(name: 'max_favorite_artists')
    final int maxFavoriteArtists;
    
    @JsonKey(name: 'max_disliked_artists')
    final int maxDislikedArtists;
    
    @JsonKey(name: 'max_favorite_genres')
    final int maxFavoriteGenres;
    
    @JsonKey(name: 'max_preferred_decades')
    final int maxPreferredDecades;

    const PersonalityConfig({
        required this.maxFavoriteArtists,
        required this.maxDislikedArtists,
        required this.maxFavoriteGenres,
        required this.maxPreferredDecades,
    });

    factory PersonalityConfig.fromJson(Map<String, dynamic> json) => _$PersonalityConfigFromJson(json);
    Map<String, dynamic> toJson() => _$PersonalityConfigToJson(this);
}

@JsonSerializable()
class PlaylistConfig {
    @JsonKey(name: 'max_songs_per_playlist')
    final int maxSongsPerPlaylist;
    
    @JsonKey(name: 'max_playlists_per_day')
    final int maxPlaylistsPerDay;
    
    @JsonKey(name: 'max_refinements_per_playlist')
    final int maxRefinementsPerPlaylist;

    const PlaylistConfig({
        required this.maxSongsPerPlaylist,
        required this.maxPlaylistsPerDay,
        required this.maxRefinementsPerPlaylist,
    });

    factory PlaylistConfig.fromJson(Map<String, dynamic> json) => _$PlaylistConfigFromJson(json);
    Map<String, dynamic> toJson() => _$PlaylistConfigToJson(this);
}

@JsonSerializable()
class FeatureConfig {
    @JsonKey(name: 'auth_required')
    final bool authRequired;
    
    @JsonKey(name: 'playlist_limit_enabled')
    final bool playlistLimitEnabled;
    
    @JsonKey(name: 'refinement_limit_enabled')
    final bool refinementLimitEnabled;

    const FeatureConfig({
        required this.authRequired,
        required this.playlistLimitEnabled,
        required this.refinementLimitEnabled,
    });

    factory FeatureConfig.fromJson(Map<String, dynamic> json) => _$FeatureConfigFromJson(json);
    Map<String, dynamic> toJson() => _$FeatureConfigToJson(this);
}

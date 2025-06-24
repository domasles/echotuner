import 'package:json_annotation/json_annotation.dart';

part 'user_context.g.dart';

@JsonSerializable()
class UserContext {
  @JsonKey(name: 'age_range')
  final String? ageRange;
  @JsonKey(name: 'favorite_genres')
  final List<String>? favoriteGenres;
  @JsonKey(name: 'favorite_artists')
  final List<String>? favoriteArtists;
  @JsonKey(name: 'recent_listening_history')
  final List<String>? recentListeningHistory;
  @JsonKey(name: 'music_discovery_preference')
  final String? musicDiscoveryPreference;
  @JsonKey(name: 'energy_preference')
  final String? energyPreference;

  UserContext({
    this.ageRange,
    this.favoriteGenres,
    this.favoriteArtists,
    this.recentListeningHistory,
    this.musicDiscoveryPreference = 'balanced',
    this.energyPreference = 'medium',
  });

  factory UserContext.fromJson(Map<String, dynamic> json) => _$UserContextFromJson(json);
  Map<String, dynamic> toJson() => _$UserContextToJson(this);
}

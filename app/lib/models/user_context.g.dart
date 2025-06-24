// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_context.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UserContext _$UserContextFromJson(Map<String, dynamic> json) => UserContext(
      ageRange: json['age_range'] as String?,
      favoriteGenres: (json['favorite_genres'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      favoriteArtists: (json['favorite_artists'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
      recentListeningHistory:
          (json['recent_listening_history'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList(),
      musicDiscoveryPreference:
          json['music_discovery_preference'] as String? ?? 'balanced',
      energyPreference: json['energy_preference'] as String? ?? 'medium',
    );

Map<String, dynamic> _$UserContextToJson(UserContext instance) =>
    <String, dynamic>{
      'age_range': instance.ageRange,
      'favorite_genres': instance.favoriteGenres,
      'favorite_artists': instance.favoriteArtists,
      'recent_listening_history': instance.recentListeningHistory,
      'music_discovery_preference': instance.musicDiscoveryPreference,
      'energy_preference': instance.energyPreference,
    };

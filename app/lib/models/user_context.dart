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

    @JsonKey(name: 'disliked_artists')
    final List<String>? dislikedArtists;

    @JsonKey(name: 'recent_listening_history')
    final List<String>? recentListeningHistory;

    @JsonKey(name: 'music_discovery_preference')
    final String? musicDiscoveryPreference;

    @JsonKey(name: 'energy_preference')
    final String? energyPreference;

    // Personality questions responses
    @JsonKey(name: 'happy_music_preference')
    final String? happyMusicPreference;

    @JsonKey(name: 'sad_music_preference')
    final String? sadMusicPreference;

    @JsonKey(name: 'workout_music_preference')
    final String? workoutMusicPreference;

    @JsonKey(name: 'focus_music_preference')
    final String? focusMusicPreference;

    @JsonKey(name: 'relaxation_music_preference')
    final String? relaxationMusicPreference;

    @JsonKey(name: 'party_music_preference')
    final String? partyMusicPreference;

    @JsonKey(name: 'discovery_openness')
    final String? discoveryOpenness;

    @JsonKey(name: 'explicit_content_preference')
    final String? explicitContentPreference;

    @JsonKey(name: 'instrumental_preference')
    final String? instrumentalPreference;

    @JsonKey(name: 'decade_preference')
    final List<String>? decadePreference;

    @JsonKey(name: 'include_spotify_artists')
    final bool? includeSpotifyArtists;

    UserContext({
        this.ageRange,
        this.favoriteGenres,
        this.favoriteArtists,
        this.dislikedArtists,
        this.recentListeningHistory,
        this.musicDiscoveryPreference = 'balanced',
        this.energyPreference = 'medium',
        this.happyMusicPreference,
        this.sadMusicPreference,
        this.workoutMusicPreference,
        this.focusMusicPreference,
        this.relaxationMusicPreference,
        this.partyMusicPreference,
        this.discoveryOpenness,
        this.explicitContentPreference,
        this.instrumentalPreference,
        this.decadePreference,
        this.includeSpotifyArtists = true,
    });

    factory UserContext.fromJson(Map<String, dynamic> json) => _$UserContextFromJson(json);
    Map<String, dynamic> toJson() => _$UserContextToJson(this);

    UserContext copyWith({
        String? ageRange,
        List<String>? favoriteGenres,
        List<String>? favoriteArtists,
        List<String>? dislikedArtists,
        List<String>? recentListeningHistory,
        String? musicDiscoveryPreference,
        String? energyPreference,
        String? happyMusicPreference,
        String? sadMusicPreference,
        String? workoutMusicPreference,
        String? focusMusicPreference,
        String? relaxationMusicPreference,
        String? partyMusicPreference,
        String? discoveryOpenness,
        String? explicitContentPreference,
        String? instrumentalPreference,
        List<String>? decadePreference,
        bool? includeSpotifyArtists,
    }) {
        return UserContext(
            ageRange: ageRange ?? this.ageRange,
            favoriteGenres: favoriteGenres ?? this.favoriteGenres,
            favoriteArtists: favoriteArtists ?? this.favoriteArtists,
            dislikedArtists: dislikedArtists ?? this.dislikedArtists,
            recentListeningHistory: recentListeningHistory ?? this.recentListeningHistory,
            musicDiscoveryPreference: musicDiscoveryPreference ?? this.musicDiscoveryPreference,
            energyPreference: energyPreference ?? this.energyPreference,
            happyMusicPreference: happyMusicPreference ?? this.happyMusicPreference,
            sadMusicPreference: sadMusicPreference ?? this.sadMusicPreference,
            workoutMusicPreference: workoutMusicPreference ?? this.workoutMusicPreference,
            focusMusicPreference: focusMusicPreference ?? this.focusMusicPreference,
            relaxationMusicPreference: relaxationMusicPreference ?? this.relaxationMusicPreference,
            partyMusicPreference: partyMusicPreference ?? this.partyMusicPreference,
            discoveryOpenness: discoveryOpenness ?? this.discoveryOpenness,
            explicitContentPreference: explicitContentPreference ?? this.explicitContentPreference,
            instrumentalPreference: instrumentalPreference ?? this.instrumentalPreference,
            decadePreference: decadePreference ?? this.decadePreference,
            includeSpotifyArtists: includeSpotifyArtists ?? this.includeSpotifyArtists,
        );
    }
}

@JsonSerializable()
class SpotifyArtist {
    final String id;
    final String name;
    @JsonKey(name: 'image_url')
    final String? imageUrl;
    final List<String>? genres;
    final int? popularity;

    SpotifyArtist({
        required this.id,
        required this.name,
        this.imageUrl,
        this.genres,
        this.popularity,
    });

    factory SpotifyArtist.fromJson(Map<String, dynamic> json) => _$SpotifyArtistFromJson(json);
    Map<String, dynamic> toJson() => _$SpotifyArtistToJson(this);
}

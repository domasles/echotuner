import 'package:json_annotation/json_annotation.dart';

part 'song.g.dart';

@JsonSerializable()
class Song {
    final String title;
    final String artist;
    final String? album;

    @JsonKey(name: 'spotify_id')
    final String? spotifyId;

    @JsonKey(name: 'preview_url')
    final String? previewUrl;

    @JsonKey(name: 'duration_ms')
    final int? durationMs;

    final int? popularity;
    final List<String>? genres;

    Song({
        required this.title,
        required this.artist,

        this.album,
        this.spotifyId,
        this.previewUrl,
        this.durationMs,
        this.popularity,
        this.genres,
    });

    factory Song.fromJson(Map<String, dynamic> json) => _$SongFromJson(json);
    Map<String, dynamic> toJson() => _$SongToJson(this);

    @override
    bool operator ==(Object other) => identical(this, other) || (
        other is Song &&
        runtimeType == other.runtimeType &&
        title == other.title &&
        artist == other.artist
    );

    @override
    int get hashCode => title.hashCode ^ artist.hashCode;

    String get displayDuration {
        if (durationMs == null) return '';

        final minutes = (durationMs! / 60000).floor();
        final seconds = ((durationMs! / 1000) % 60).floor();

        return '$minutes:${seconds.toString().padLeft(2, '0')}';
    }

    String get uri {
        return spotifyId != null ? 'spotify:track:$spotifyId' : '';
    }
}

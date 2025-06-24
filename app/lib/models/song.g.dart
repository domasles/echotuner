// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'song.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Song _$SongFromJson(Map<String, dynamic> json) => Song(
      title: json['title'] as String,
      artist: json['artist'] as String,
      album: json['album'] as String?,
      spotifyId: json['spotify_id'] as String?,
      previewUrl: json['preview_url'] as String?,
      durationMs: (json['duration_ms'] as num?)?.toInt(),
      popularity: (json['popularity'] as num?)?.toInt(),
      genres:
          (json['genres'] as List<dynamic>?)?.map((e) => e as String).toList(),
    );

Map<String, dynamic> _$SongToJson(Song instance) => <String, dynamic>{
      'title': instance.title,
      'artist': instance.artist,
      'album': instance.album,
      'spotify_id': instance.spotifyId,
      'preview_url': instance.previewUrl,
      'duration_ms': instance.durationMs,
      'popularity': instance.popularity,
      'genres': instance.genres,
    };

import 'package:json_annotation/json_annotation.dart';

import 'user_context.dart';
import 'song.dart';

part 'playlist_request.g.dart';

@JsonSerializable()
class PlaylistRequest {
    final String prompt;

    @JsonKey(name: 'user_context')
    final UserContext? userContext;

    @JsonKey(name: 'current_songs')
    final List<Song>? currentSongs;

    @JsonKey(name: 'discovery_strategy')
    final String? discoveryStrategy;

    final int? count;

    PlaylistRequest({
        required this.prompt,

        this.userContext,
        this.currentSongs,
        this.discoveryStrategy,
        this.count,
    });

    factory PlaylistRequest.fromJson(Map<String, dynamic> json) => _$PlaylistRequestFromJson(json);
    Map<String, dynamic> toJson() => _$PlaylistRequestToJson(this);
}

@JsonSerializable()
class PlaylistResponse {
    final List<Song> songs;

    @JsonKey(name: 'generated_from')
    final String generatedFrom;

    @JsonKey(name: 'total_count')
    final int totalCount;

    @JsonKey(name: 'confidence_score')
    final double? confidenceScore;

    @JsonKey(name: 'playlist_id')
    final String? playlistId;

    PlaylistResponse({
        required this.songs,
        required this.generatedFrom,
        required this.totalCount,

        this.confidenceScore,
        this.playlistId,
    });

    factory PlaylistResponse.fromJson(Map<String, dynamic> json) => _$PlaylistResponseFromJson(json);
    Map<String, dynamic> toJson() => _$PlaylistResponseToJson(this);
}

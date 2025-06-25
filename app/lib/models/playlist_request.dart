import 'package:json_annotation/json_annotation.dart';

import 'user_context.dart';
import 'song.dart';

part 'playlist_request.g.dart';

@JsonSerializable()
class PlaylistRequest {
    final String prompt;

    @JsonKey(name: 'device_id')
    final String deviceId;

    @JsonKey(name: 'session_id')
    final String sessionId;

    @JsonKey(name: 'user_context')
    final UserContext? userContext;

    @JsonKey(name: 'current_songs')
    final List<Song>? currentSongs;

    PlaylistRequest({
        required this.prompt,
        required this.deviceId,
        required this.sessionId,
		
        this.userContext,
        this.currentSongs,
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

    @JsonKey(name: 'is_refinement')
    final bool? isRefinement;
    
    @JsonKey(name: 'confidence_score')
    final double? confidenceScore;

    PlaylistResponse({
        required this.songs,
        required this.generatedFrom,
        required this.totalCount,
        this.isRefinement,
        this.confidenceScore,
    });

    factory PlaylistResponse.fromJson(Map<String, dynamic> json) => _$PlaylistResponseFromJson(json);
    Map<String, dynamic> toJson() => _$PlaylistResponseToJson(this);
}

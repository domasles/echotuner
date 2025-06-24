// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'playlist_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PlaylistRequest _$PlaylistRequestFromJson(Map<String, dynamic> json) =>
    PlaylistRequest(
      prompt: json['prompt'] as String,
      deviceId: json['device_id'] as String,
      userContext: json['user_context'] == null
          ? null
          : UserContext.fromJson(json['user_context'] as Map<String, dynamic>),
      currentSongs: (json['current_songs'] as List<dynamic>?)
          ?.map((e) => Song.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$PlaylistRequestToJson(PlaylistRequest instance) =>
    <String, dynamic>{
      'prompt': instance.prompt,
      'device_id': instance.deviceId,
      'user_context': instance.userContext,
      'current_songs': instance.currentSongs,
    };

PlaylistResponse _$PlaylistResponseFromJson(Map<String, dynamic> json) =>
    PlaylistResponse(
      songs: (json['songs'] as List<dynamic>)
          .map((e) => Song.fromJson(e as Map<String, dynamic>))
          .toList(),
      generatedFrom: json['generated_from'] as String,
      totalCount: (json['total_count'] as num).toInt(),
      isRefinement: json['is_refinement'] as bool?,
      confidenceScore: (json['confidence_score'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$PlaylistResponseToJson(PlaylistResponse instance) =>
    <String, dynamic>{
      'songs': instance.songs,
      'generated_from': instance.generatedFrom,
      'total_count': instance.totalCount,
      'is_refinement': instance.isRefinement,
      'confidence_score': instance.confidenceScore,
    };

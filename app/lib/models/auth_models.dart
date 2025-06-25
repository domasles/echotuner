import 'package:json_annotation/json_annotation.dart';

part 'auth_models.g.dart';

@JsonSerializable()
class AuthInitRequest {
    @JsonKey(name: 'device_id')

    final String deviceId;
    final String platform;

    AuthInitRequest({
        required this.deviceId,
        required this.platform,
    });

    factory AuthInitRequest.fromJson(Map<String, dynamic> json) => _$AuthInitRequestFromJson(json);
    Map<String, dynamic> toJson() => _$AuthInitRequestToJson(this);
}

@JsonSerializable()
class AuthInitResponse {
    @JsonKey(name: 'auth_url')

    final String authUrl;
    final String state;

    AuthInitResponse({
        required this.authUrl,
        required this.state,
    });

    factory AuthInitResponse.fromJson(Map<String, dynamic> json) => _$AuthInitResponseFromJson(json);
    Map<String, dynamic> toJson() => _$AuthInitResponseToJson(this);
}

@JsonSerializable()
class SessionValidationRequest {
    @JsonKey(name: 'session_id')
    final String sessionId;
	
    @JsonKey(name: 'device_id')
    final String deviceId;

    SessionValidationRequest({
        required this.sessionId,
        required this.deviceId,
    });

    factory SessionValidationRequest.fromJson(Map<String, dynamic> json) => _$SessionValidationRequestFromJson(json);
    Map<String, dynamic> toJson() => _$SessionValidationRequestToJson(this);
}

@JsonSerializable()
class SessionValidationResponse {
    final bool valid;

    @JsonKey(name: 'user_id')
    final String? userId;

    @JsonKey(name: 'spotify_user_id')
    final String? spotifyUserId;

    SessionValidationResponse({
        required this.valid,
		
        this.userId,
        this.spotifyUserId,
    });

    factory SessionValidationResponse.fromJson(Map<String, dynamic> json) => _$SessionValidationResponseFromJson(json);
    Map<String, dynamic> toJson() => _$SessionValidationResponseToJson(this);
}

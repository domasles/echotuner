import 'package:json_annotation/json_annotation.dart';

part 'auth_models.g.dart';

@JsonSerializable()
class AuthInitRequest {
    final String platform;

    AuthInitRequest({
        required this.platform,
    });

    factory AuthInitRequest.fromJson(Map<String, dynamic> json) => _$AuthInitRequestFromJson(json);
    Map<String, dynamic> toJson() => _$AuthInitRequestToJson(this);
}

@JsonSerializable()
class AuthInitResponse {
    @JsonKey(name: 'auth_url')
    final String authUrl;
    
    @JsonKey(name: 'session_uuid')
    final String sessionUuid;

    final String? action;
    final String? message;

    AuthInitResponse({
        required this.authUrl,
        required this.sessionUuid,
        this.action,
        this.message,
    });

    factory AuthInitResponse.fromJson(Map<String, dynamic> json) => _$AuthInitResponseFromJson(json);
    Map<String, dynamic> toJson() => _$AuthInitResponseToJson(this);
}

@JsonSerializable()
class AuthStatusRequest {
    @JsonKey(name: 'session_uuid')
    final String sessionUuid;

    AuthStatusRequest({
        required this.sessionUuid,
    });

    factory AuthStatusRequest.fromJson(Map<String, dynamic> json) => _$AuthStatusRequestFromJson(json);
    Map<String, dynamic> toJson() => _$AuthStatusRequestToJson(this);
}

@JsonSerializable()
class AuthStatusResponse {
    final String status;

    @JsonKey(name: 'session_token')
    final String? sessionToken;

    AuthStatusResponse({
        required this.status,
        this.sessionToken,
    });

    factory AuthStatusResponse.fromJson(Map<String, dynamic> json) => _$AuthStatusResponseFromJson(json);
    Map<String, dynamic> toJson() => _$AuthStatusResponseToJson(this);
}

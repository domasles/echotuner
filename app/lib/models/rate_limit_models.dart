import 'package:json_annotation/json_annotation.dart';

part 'rate_limit_models.g.dart';

@JsonSerializable()
class RateLimitStatus {
    @JsonKey(name: 'device_id')
    final String deviceId;

    @JsonKey(name: 'requests_made_today')
    final int requestsMadeToday;

    @JsonKey(name: 'max_requests_per_day')
    final int maxRequestsPerDay;

    @JsonKey(name: 'refinements_used')
    final int refinementsUsed;

    @JsonKey(name: 'max_refinements')
    final int maxRefinements;

    @JsonKey(name: 'can_make_request')
    final bool canMakeRequest;

    @JsonKey(name: 'can_refine')
    final bool canRefine;

    @JsonKey(name: 'reset_time')
    final String? resetTime;

    @JsonKey(name: 'playlist_limit_enabled')
    final bool playlistLimitEnabled;

    @JsonKey(name: 'refinement_limit_enabled')
    final bool refinementLimitEnabled;

    RateLimitStatus({
        required this.deviceId,
        required this.requestsMadeToday,
        required this.maxRequestsPerDay,
        required this.refinementsUsed,
        required this.maxRefinements,
        required this.canMakeRequest,
        required this.canRefine,
        required this.playlistLimitEnabled,
        required this.refinementLimitEnabled,

        this.resetTime,
    });

    factory RateLimitStatus.fromJson(Map<String, dynamic> json) => _$RateLimitStatusFromJson(json);
    Map<String, dynamic> toJson() => _$RateLimitStatusToJson(this);
}

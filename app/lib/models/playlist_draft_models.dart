import 'package:json_annotation/json_annotation.dart';

import 'song.dart';

part 'playlist_draft_models.g.dart';

@JsonSerializable()
class PlaylistDraft {
    final String id;

    @JsonKey(name: 'user_id')
    final String userId;

    final String prompt;
    final List<Song> songs;

    @JsonKey(name: 'created_at')
    final DateTime createdAt;

    @JsonKey(name: 'updated_at')
    final DateTime updatedAt;

    final String status;

    @JsonKey(name: 'spotify_playlist_id')
    final String? spotifyPlaylistId;

    PlaylistDraft({
        required this.id,
        required this.userId,

        required this.prompt,
        required this.songs,
        required this.createdAt,
        required this.updatedAt,
        required this.status,

        this.spotifyPlaylistId,
    });

    factory PlaylistDraft.fromJson(Map<String, dynamic> json) => _$PlaylistDraftFromJson(json);
    Map<String, dynamic> toJson() => _$PlaylistDraftToJson(this);

    bool get isDraft => status == 'draft';
    bool get isAddedToSpotify => status == 'added_to_spotify';
}

@JsonSerializable()
class SpotifyPlaylistRequest {
    final String name;
    final String? description;
    final bool? public;
    final List<Song>? songs;

    SpotifyPlaylistRequest({
        required this.name,
        this.description,
        this.public,
        this.songs,
    });

    factory SpotifyPlaylistRequest.fromJson(Map<String, dynamic> json) => _$SpotifyPlaylistRequestFromJson(json);
    Map<String, dynamic> toJson() => _$SpotifyPlaylistRequestToJson(this);
}

@JsonSerializable()
class SpotifyPlaylistResponse {
    final bool success;

    @JsonKey(name: 'spotify_playlist_id')
    final String spotifyPlaylistId;

    @JsonKey(name: 'playlist_url')
    final String playlistUrl;

    final String message;

    SpotifyPlaylistResponse({
        required this.success,
        required this.spotifyPlaylistId,
        required this.playlistUrl,
        required this.message,
    });

    factory SpotifyPlaylistResponse.fromJson(Map<String, dynamic> json) => _$SpotifyPlaylistResponseFromJson(json);
    Map<String, dynamic> toJson() => _$SpotifyPlaylistResponseToJson(this);
}

@JsonSerializable()
class LibraryPlaylistsRequest {
    @JsonKey(name: 'include_drafts')
    final bool? includeDrafts;

    LibraryPlaylistsRequest({
        this.includeDrafts,
    });

    factory LibraryPlaylistsRequest.fromJson(Map<String, dynamic> json) => _$LibraryPlaylistsRequestFromJson(json);
    Map<String, dynamic> toJson() => _$LibraryPlaylistsRequestToJson(this);
}

@JsonSerializable()
class LibraryPlaylistsResponse {
    final List<PlaylistDraft> drafts;

    @JsonKey(name: 'spotify_playlists')
    final List<SpotifyPlaylistInfo> spotifyPlaylists;

    LibraryPlaylistsResponse({
        required this.drafts,
        required this.spotifyPlaylists,
    });

    factory LibraryPlaylistsResponse.fromJson(Map<String, dynamic> json) => _$LibraryPlaylistsResponseFromJson(json);
    Map<String, dynamic> toJson() => _$LibraryPlaylistsResponseToJson(this);
}

@JsonSerializable()
class SpotifyPlaylistInfo {
    final String id;
    final String name;
    final String? description;

    @JsonKey(name: 'tracks_count')
    final int tracksCount;

    @JsonKey(name: 'spotify_url')
    final String? spotifyUrl;

    final List<Map<String, dynamic>>? images;

    SpotifyPlaylistInfo({
        required this.id,
        required this.name,

        this.description,

        required this.tracksCount,

        this.spotifyUrl,
        this.images,
    });

    factory SpotifyPlaylistInfo.fromJson(Map<String, dynamic> json) => _$SpotifyPlaylistInfoFromJson(json);
    Map<String, dynamic> toJson() => _$SpotifyPlaylistInfoToJson(this);
}

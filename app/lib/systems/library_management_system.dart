import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../models/playlist_draft_models.dart';
import '../providers/playlist_provider.dart';

class LibraryManagementSystem {
    List<PlaylistDraft> _drafts = [];
    List<SpotifyPlaylistInfo> _spotifyPlaylists = [];

    bool _isLoading = true;
    String? _error;

    List<PlaylistDraft> get drafts => _drafts;
    List<SpotifyPlaylistInfo> get spotifyPlaylists => _spotifyPlaylists;

    bool get isLoading => _isLoading;
    String? get error => _error;

    Future<void> loadLibraryData(BuildContext context) async {
        _isLoading = true;
        _error = null;

        try {
            final provider = Provider.of<PlaylistProvider>(context, listen: false);
            final response = await provider.getLibraryPlaylists();

            _drafts = response.drafts;
            _spotifyPlaylists = response.spotifyPlaylists;
            _isLoading = false;
            _error = null;

        }

        catch (e) {
            _error = e.toString();
            _isLoading = false;
        }
    }

    Future<void> silentRefresh(BuildContext context) async {
        try {
            final provider = Provider.of<PlaylistProvider>(context, listen: false);
            final response = await provider.refreshLibraryPlaylists();

            _drafts = response.drafts;
            _spotifyPlaylists = response.spotifyPlaylists;

            if (_error != null) _error = null;
        }

        catch (e) {
            // Silent refresh - intentionally ignore errors to avoid disrupting UI
        }
    }

    void updateState({List<PlaylistDraft>? drafts, List<SpotifyPlaylistInfo>? spotifyPlaylists, bool? isLoading, String? error}) {
        if (drafts != null) _drafts = drafts;
        if (spotifyPlaylists != null) _spotifyPlaylists = spotifyPlaylists;
        if (isLoading != null) _isLoading = isLoading;
        if (error != null) _error = error;
    }

    void clearError() {
        _error = null;
    }
}

mixin LibraryManagementMixin on State {
    final LibraryManagementSystem _librarySystem = LibraryManagementSystem();
    
    List<PlaylistDraft> get drafts => _librarySystem.drafts;
    List<SpotifyPlaylistInfo> get spotifyPlaylists => _librarySystem.spotifyPlaylists;

    bool get isLibraryLoading => _librarySystem.isLoading;
    String? get libraryError => _librarySystem.error;

    Future<void> loadLibraryData() async {
        await _librarySystem.loadLibraryData(context);
        if (mounted) setState(() {});
    }

    Future<void> silentRefreshLibrary() async {
        await _librarySystem.silentRefresh(context);
        if (mounted) setState(() {});
    }

    void updateLibraryState({List<PlaylistDraft>? drafts, List<SpotifyPlaylistInfo>? spotifyPlaylists, bool? isLoading, String? error}) {
        _librarySystem.updateState(
            drafts: drafts,
            spotifyPlaylists: spotifyPlaylists,
            isLoading: isLoading,
            error: error,
        );

        if (mounted) setState(() {});
    }

    void clearLibraryError() {
        _librarySystem.clearError();
        if (mounted) setState(() {});
    }
}

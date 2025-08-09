import 'package:flutter/foundation.dart' show kIsWeb, ChangeNotifier;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'dart:io' show Platform;
import 'dart:convert';
import 'package:uuid/uuid.dart';

import '../models/auth_models.dart';
import '../config/settings.dart';
import '../utils/app_logger.dart';

class AuthService extends ChangeNotifier {
    static const String _userIdKey = 'user_id';
    static const String _tempSessionUuidKey = 'temp_session_uuid';

    String? _userId;
    String? _tempSessionUuid;
    String? _authUrl; // Cache auth URL for synchronous login

    bool _isAuthenticated = false;
    bool _isLoading = false;

    String? get userId => _userId;
    String? get sessionUuid => _tempSessionUuid;
    String? get authUrl => _authUrl; // Cached auth URL for synchronous login
    bool get isAuthenticated => _isAuthenticated;
    bool get isLoading => _isLoading;

    Future<void> initialize() async {
        _isLoading = true;
        notifyListeners();

        try {
            final prefs = await SharedPreferences.getInstance();
            _userId = prefs.getString(_userIdKey);
            _tempSessionUuid = prefs.getString(_tempSessionUuidKey);

            AppLogger.debug('Auth initialization - User ID: ${_userId?.substring(0, 20)}...');

            if (_userId != null) {
                _isAuthenticated = await validateUserOnStartup();
            }
            
            // If not authenticated, prefetch auth URL for synchronous login
            if (!_isAuthenticated) {
                try {
                    await _prefetchAuthUrl();
                } catch (e) {
                    AppLogger.debug('Failed to prefetch auth URL: $e');
                    // Continue even if prefetch fails
                }
            }
        }

        catch (e, stackTrace) {
            AppLogger.error(
                'Auth initialization error: $e',
                error: e,
                stackTrace: stackTrace,
            );

            _isAuthenticated = false;
        }

        _isLoading = false;
        notifyListeners();
    }

    Future<void> _prefetchAuthUrl() async {
        // Generate UUID for session
        const uuid = Uuid();
        _tempSessionUuid = uuid.v4();
        
        // Save temporary session UUID
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_tempSessionUuidKey, _tempSessionUuid!);

        final request = AuthInitRequest(
            platform: _getPlatform(),
        );

        final response = await http.post(
            Uri.parse(AppConfig.apiUrl('/auth/init')),
            headers: {
                'Content-Type': 'application/json',
                'X-Session-UUID': _tempSessionUuid!,
            },
            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            final authResponse = AuthInitResponse.fromJson(jsonDecode(response.body));
            _authUrl = authResponse.authUrl;
            AppLogger.debug('Auth URL prefetched successfully');
        } else {
            throw Exception('Failed to prefetch auth URL: ${response.body}');
        }
    }

    // Synchronous login method that uses prefetched auth URL
    String? getSynchronousAuthUrl() {
        return _authUrl;
    }

    Future<AuthInitResponse> initiateAuth() async {
        // Generate UUID for session
        const uuid = Uuid();
        _tempSessionUuid = uuid.v4();
        
        // Save temporary session UUID
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_tempSessionUuidKey, _tempSessionUuid!);

        final request = AuthInitRequest(
            platform: _getPlatform(),
        );

        final response = await http.post(
            Uri.parse(AppConfig.apiUrl('/auth/init')),
            headers: {
                'Content-Type': 'application/json',
                'X-Session-UUID': _tempSessionUuid!,
            },
            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            final authResponse = AuthInitResponse.fromJson(jsonDecode(response.body));
            return authResponse;
        }

        else {
            throw Exception('Failed to initiate auth: ${response.body}');
        }
    }

    Future<void> handleSetupRequired() async {
        // For setup scenarios - just open browser, don't poll
        // The setup will be handled completely in browser
        AppLogger.info('Setup required - opening browser for owner setup');
        // No polling needed, setup is browser-only
    }

    Future<String> completeNormalAuth() async {
        // For normal auth scenarios - poll until completion
        return await completeAuth();
    }

    Future<AuthInitResponse> initiateDesktopAuth() async {
        return await initiateAuth();
    }

    Future<String> completeDesktopAuth() async {
        return await completeAuth();
    }

    Future<String> completeAuth() async {
        if (_tempSessionUuid == null) {
            throw Exception('No temporary session UUID available - must call initiateAuth first');
        }

        for (int i = 0; i < 150; i++) {
            await Future.delayed(const Duration(seconds: 2));

            try {
                final response = await http.get(
                    Uri.parse(AppConfig.apiUrl('/auth/status')),
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Session-UUID': _tempSessionUuid!,
                    },
                );

                if (response.statusCode == 200) {
                    final data = jsonDecode(response.body);
                    final authStatus = AuthStatusResponse.fromJson(data);

                    if (authStatus.status == 'completed' && authStatus.userId != null) {
                        await setUserId(authStatus.userId!);
                        return authStatus.userId!;
                    }
                }
            }

            catch (e, stackTrace) {
                AppLogger.error(
                    'Polling error: $e',
                    error: e,
                    stackTrace: stackTrace,
                );
            }
        }

        throw Exception('Authentication timeout - please try again');
    }

    Future<bool> _validateUser() async {
        if (_userId == null) {
            return false;
        }

        // In the new unified system, user validation is handled at the endpoint level
        // via X-User-ID headers, so we don't need a separate validation call
        return true;
    }

    Future<bool> validateUserOnStartup() async {
        try {
            AppLogger.debug('Validating user on startup...');

            if (_userId != null) {
                final isValid = await _validateUser();

                if (!isValid) {
                    AppLogger.debug('User invalid, clearing local data');
                    await _clearAllLocalData();
                    return false;
                }

                return true;
            }

            return false;

        }

        catch (e) {
            AppLogger.debug('User validation on startup failed: $e');

            await _clearAllLocalData();
            return false;
        }
    }

    Future<void> setUserId(String userId) async {
        _userId = userId;
        _isAuthenticated = true;

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userIdKey, userId);
        await prefs.remove(_tempSessionUuidKey); // Clear temp session UUID

        notifyListeners();
    }

    Future<void> _clearUser() async {
        _userId = null;
        _tempSessionUuid = null;
        _isAuthenticated = false;

        final prefs = await SharedPreferences.getInstance();
        await prefs.remove(_userIdKey);
        await prefs.remove(_tempSessionUuidKey);

        notifyListeners();
    }

    Future<void> logout() async {
        AppLogger.debug('Starting logout process...');

        await _clearAllLocalData();
        AppLogger.debug('Logout completed. isAuthenticated: $_isAuthenticated');
    }

    Future<void> _clearAllLocalData() async {
        await _clearUser();

        final prefs = await SharedPreferences.getInstance();
        await prefs.clear();

        AppLogger.debug('All local data cleared');
    }

    Future<Map<String, dynamic>> checkServerMode() async {
        try {
            final response = await http.get(
                Uri.parse(AppConfig.apiUrl('/server/mode')),
                headers: {'Content-Type': 'application/json'},
            );

            if (response.statusCode == 200) return jsonDecode(response.body);
        }

        catch (e) {
            AppLogger.debug('Failed to check server mode: $e');
        }

        return {'error': 'Failed to get server mode'};
    }

    Future<bool> checkAuthStatus() async {
        if (_userId == null) return false;
        final isValid = await _validateUser();

        if (!isValid) await _clearUser();
        return isValid;
    }

    String _getPlatform() {
        if (kIsWeb) return 'web';
        if (Platform.isAndroid) return 'android';
        if (Platform.isIOS) return 'ios';
        if (Platform.isWindows) return 'windows';
        if (Platform.isMacOS) return 'macos';
        if (Platform.isLinux) return 'linux';

        return 'unknown';
    }
}

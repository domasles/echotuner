import 'package:flutter/foundation.dart' show kIsWeb, ChangeNotifier;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'dart:io' show Platform;
import 'dart:convert';

import '../models/auth_models.dart';
import '../config/settings.dart';
import '../utils/app_logger.dart';

class AuthService extends ChangeNotifier {
    static const String _sessionIdKey = 'session_id';
    static const String _deviceIdKey = 'device_id';

    String? _sessionId;
    String? _deviceId;
    String? _tempDeviceId;

    bool _isAuthenticated = false;
    bool _isLoading = false;

    String? get sessionId => _sessionId;
    String? get deviceId => _deviceId;

    bool get isAuthenticated => _isAuthenticated;
    bool get isLoading => _isLoading;

    Future<void> initialize() async {
        _isLoading = true;
        notifyListeners();

        try {
            final prefs = await SharedPreferences.getInstance();
            _sessionId = prefs.getString(_sessionIdKey);
            _deviceId = prefs.getString(_deviceIdKey);

            AppLogger.debug('Auth initialization - Device ID: ${_deviceId?.substring(0, 20)}..., Session ID: ${_sessionId?.substring(0, 20)}...');

            if (_sessionId != null && _deviceId != null) {
                final modeResponse = await http.get(
                    Uri.parse(AppConfig.apiUrl('/auth/mode')),
                );
                
                if (modeResponse.statusCode == 200) {
                    final mode = jsonDecode(modeResponse.body);
                    final isDemo = mode['demo'] as bool;
                    
                    await _validateSessionMode(isDemo);
                }

                _isAuthenticated = await validateSessionOnStartup();
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

    Future<AuthInitResponse> initiateAuth() async {
        final request = AuthInitRequest(
            deviceId: '',
            platform: _getPlatform(),
        );

        final response = await http.post(
            Uri.parse(AppConfig.apiUrl('/auth/init')),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            final authResponse = AuthInitResponse.fromJson(jsonDecode(response.body));
            _tempDeviceId = authResponse.deviceId;
            return authResponse;
        }

        else {
            throw Exception('Failed to initiate auth: ${response.body}');
        }
    }

    Future<AuthInitResponse> initiateDesktopAuth() async {
        return await initiateAuth();
    }

    Future<String> completeDesktopAuth() async {
        return await completeAuth();
    }

    Future<String> completeAuth() async {
        if (_tempDeviceId == null) {
            throw Exception('No temporary device ID available - must call initiateAuth first');
        }

        for (int i = 0; i < 150; i++) {
            await Future.delayed(const Duration(seconds: 2));

            try {
                final response = await http.get(
                    Uri.parse(AppConfig.apiUrl('/auth/check-session')),
                    headers: {
                        'Content-Type': 'application/json',
                        'device_id': _tempDeviceId!,
                    },
                );

                if (response.statusCode == 200) {
                    final data = jsonDecode(response.body);

                    if (data['session_id'] != null) {
                        final sessionId = data['session_id'] as String;

                        _deviceId = _tempDeviceId;

                        final prefs = await SharedPreferences.getInstance();
                        await prefs.setString(_deviceIdKey, _deviceId!);
                        
                        await setSession(sessionId);
                        return sessionId;
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

    Future<bool> _validateSession() async {
        if (_sessionId == null || _deviceId == null) {
            return false;
        }

        try {
            final request = SessionValidationRequest(
                sessionId: _sessionId!,
                deviceId: _deviceId!,
            );

            final response = await http.post(
                Uri.parse(AppConfig.apiUrl('/auth/validate')),
                headers: {'Content-Type': 'application/json'},
                body: jsonEncode(request.toJson()),
            );

            if (response.statusCode == 200) {
                final validationResponse = SessionValidationResponse.fromJson(
                    jsonDecode(response.body)
                );
                return validationResponse.valid;
            }

            else if (response.statusCode == 401) {
                AppLogger.debug('Session validation failed with 401 (mode mismatch or invalid session), logging out');
                await logout();
                return false;
            }

            else {
                AppLogger.debug('Session validation request failed with status ${response.statusCode}, logging out');
                await logout();
                return false;
            }
        }

        catch (e, stackTrace) {
            AppLogger.error(
                'Session validation error: $e',
                error: e,
                stackTrace: stackTrace,
            );

            await logout();
            return false;
        }
    }

    Future<void> setSession(String sessionId) async {
        _sessionId = sessionId;
        _isAuthenticated = true;

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_sessionIdKey, sessionId);

        notifyListeners();
    }

    Future<void> _clearSession() async {
        _sessionId = null;
        _deviceId = null;
        _isAuthenticated = false;

        final prefs = await SharedPreferences.getInstance();
        await prefs.remove(_sessionIdKey);
        await prefs.remove(_deviceIdKey);

        notifyListeners();
    }

    Future<void> logout() async {
        AppLogger.debug('Starting logout process...');

        try {
            if (_deviceId != null) {
                AppLogger.debug('Clearing all device data on server...');

                final logoutResponse = await http.post(
                    Uri.parse(AppConfig.apiUrl('/auth/logout')),
                    headers: {
                        'Content-Type': 'application/json',
                        'device_id': _deviceId!,
                    },
                );

                if (logoutResponse.statusCode == 200) {
                    AppLogger.debug('Device data cleared on server successfully');
                }

                else {
                    AppLogger.debug('Failed to clear device data on server: ${logoutResponse.body}');
                }
            }
        }
        
        catch (e) {
            AppLogger.debug('Error during server logout operations: $e');
        }

        await _clearAllLocalData();
        AppLogger.debug('Logout completed. isAuthenticated: $_isAuthenticated');
    }

    Future<void> _clearAllLocalData() async {
        await _clearSession();

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
            AppLogger.debug('Error checking server mode: $e');
        }

        return {'demo_mode': false, 'mode': 'normal'};
    }

    Future<bool> validateSessionOnStartup() async {
        try {
            final serverMode = await checkServerMode();
            AppLogger.debug('Server mode: ${serverMode['mode']}');

            if (_sessionId != null) {
                final isValid = await _validateSession();

                if (!isValid) {
                    AppLogger.debug('Session invalid, clearing local data');
                    await _clearAllLocalData();
                    return false;
                }

                return true;
            }

            return false;

        }

        catch (e) {
            AppLogger.debug('Session validation on startup failed: $e');

            await _clearAllLocalData();
            return false;
        }
    }

    Future<bool> checkAuthStatus() async {
        if (_sessionId == null) return false;
        final isValid = await _validateSession();

        if (!isValid) await _clearSession();
        return isValid;
    }

    Future<bool> checkAuthStatusWithModeValidation() async {
        if (_sessionId == null || _deviceId == null) return false;

        try {
            final modeResponse = await http.get(
                Uri.parse(AppConfig.apiUrl('/auth/mode')),
            );

            if (modeResponse.statusCode == 200) {
                final mode = jsonDecode(modeResponse.body);
                final isDemo = mode['demo'] as bool;

                await _validateSessionMode(isDemo);
            }

            final isValid = await _validateSession();

            if (!isValid) {
                await logout();
                return false;
            }

            return true;
        }

        catch (e) {
            AppLogger.debug('Auth status check with mode validation failed: $e');

            await logout();
            return false;
        }
    }

    Future<void> _validateSessionMode(bool serverIsDemo) async {
        if (_sessionId == null || _deviceId == null) return;

        try {
            final response = await http.post(
                Uri.parse(AppConfig.apiUrl('/auth/validate')),
                headers: {'Content-Type': 'application/json'},
                body: jsonEncode({
                    'session_id': _sessionId,
                    'device_id': _deviceId,
                }),
            );

            if (response.statusCode == 401) {
                AppLogger.debug('Session invalid due to mode mismatch, logging out');
                await logout();
            }
        }

        catch (e) {
            AppLogger.debug('Error validating session mode: $e');
            await logout();
        }
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

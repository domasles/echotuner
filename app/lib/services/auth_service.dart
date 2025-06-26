import 'dart:developer' as developer;
import 'dart:io' show Platform;
import 'dart:convert';

import 'package:flutter/foundation.dart' show kIsWeb, ChangeNotifier;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:http/http.dart' as http;

import '../models/auth_models.dart';
import '../config/app_config.dart';

class AuthService extends ChangeNotifier {
    static const String _sessionIdKey = 'session_id';
    static const String _deviceIdKey = 'device_id';
    
    String? _sessionId;
    String? _deviceId;

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
            _deviceId = prefs.getString(_deviceIdKey);


            if (_deviceId == null || _isClientGeneratedId(_deviceId!)) {
                try {
                    _deviceId = await _registerDeviceWithServer();
                    await prefs.setString(_deviceIdKey, _deviceId!);
                    developer.log('Registered new device with server: $_deviceId');
                }
				
				catch (e) {
                    developer.log('Failed to register device with server: $e');
                    _deviceId = await _generateDeviceId();
					
                    await prefs.setString(_deviceIdKey, _deviceId!);
                }
            }

            _sessionId = prefs.getString(_sessionIdKey);
            
            if (_sessionId != null) {
                _isAuthenticated = await _validateSession();
                if (!_isAuthenticated) {
                    await _clearSession();
                }
            }
        }
		
		catch (e, stackTrace) {
            developer.log(
                'Auth initialization error: $e',
                name: 'AuthService',
                error: e,
                stackTrace: stackTrace,
            );

            _isAuthenticated = false;
        }

        _isLoading = false;
        notifyListeners();
    }

    Future<String> _generateDeviceId() async {
        final deviceInfo = DeviceInfoPlugin();
        
        if (kIsWeb) {
            return 'web_${DateTime.now().millisecondsSinceEpoch}';
        }
		
		else if (Platform.isAndroid) {
            final androidInfo = await deviceInfo.androidInfo;
            return 'android_${androidInfo.id}';
        }
		
		else if (Platform.isIOS) {
            final iosInfo = await deviceInfo.iosInfo;
            return 'ios_${iosInfo.identifierForVendor ?? DateTime.now().millisecondsSinceEpoch}';
        }
		
		else {
            return 'unknown_${DateTime.now().millisecondsSinceEpoch}';
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

    Future<AuthInitResponse> initiateAuth() async {
        if (_deviceId == null) {
            throw Exception('Device ID not initialized');
        }

        final request = AuthInitRequest(
            deviceId: _deviceId!,
            platform: _getPlatform(),
        );

        final response = await http.post(
            Uri.parse(AppConfig.apiUrl('/auth/init')),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(request.toJson()),
        );

        if (response.statusCode == 200) {
            return AuthInitResponse.fromJson(jsonDecode(response.body));
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
        if (_deviceId == null) {
            throw Exception('Device ID not initialized');
        }

        for (int i = 0; i < 150; i++) {
            await Future.delayed(const Duration(seconds: 2));
            
            try {
                final response = await http.get(
                    Uri.parse(AppConfig.apiUrl('/auth/check-session/${_deviceId!}')),
                    headers: {'Content-Type': 'application/json'},
                );
                
                if (response.statusCode == 200) {
                    final data = jsonDecode(response.body);

                    if (data['session_id'] != null) {
                        final sessionId = data['session_id'] as String;
                        await setSession(sessionId);
                        return sessionId;
                    }
                }
            }
			
			catch (e, stackTrace) {
                developer.log(
                    'Polling error: $e',
                    name: 'AuthService.completeAuth',
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
        }
		
		catch (e, stackTrace) {
            developer.log(
                'Session validation error: $e',
                name: 'AuthService._validateSession',
                error: e,
                stackTrace: stackTrace,
            );
        }

        return false;
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
        _isAuthenticated = false;
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove(_sessionIdKey);
        
        notifyListeners();
    }

    Future<void> logout() async {
        developer.log('Starting logout process...');
        await _clearSession();
        developer.log('Logout completed. isAuthenticated: $_isAuthenticated');
    }

    Future<bool> checkAuthStatus() async {
        if (_sessionId == null) {
            return false;
        }
        
        final isValid = await _validateSession();

        if (!isValid) {
            await _clearSession();
        }
        
        return isValid;
    }

    bool _isClientGeneratedId(String deviceId) {
        // Check if this is an old client-generated device ID
        return deviceId.startsWith('android_') || 
               deviceId.startsWith('ios_') || 
               deviceId.startsWith('web_') || 
               deviceId.startsWith('unknown_');
    }

    Future<String> _registerDeviceWithServer() async {
        try {
            final platform = _getPlatform();
            
            final request = DeviceRegistrationRequest(
                platform: platform,
                appVersion: '1.2.0',
            );

            final response = await http.post(
                Uri.parse(AppConfig.apiUrl('/auth/register-device')),
                headers: {'Content-Type': 'application/json'},
                body: jsonEncode(request.toJson()),
            );

            if (response.statusCode == 200) {
                final data = jsonDecode(response.body);
                final deviceResponse = DeviceRegistrationResponse.fromJson(data);
                return deviceResponse.deviceId;
            }
			
			else {
                throw Exception('Server returned ${response.statusCode}: ${response.body}');
            }
        }
		
		catch (e) {
            developer.log('Device registration failed: $e');
            rethrow;
        }
    }
}

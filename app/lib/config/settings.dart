import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_dotenv/flutter_dotenv.dart';

import '../utils/app_logger.dart';
import 'app_constants.dart';

import 'environment/env_loader.dart';

class AppConfig {
    static String get apiBaseUrl {
        final runtimeHost = kIsWeb ? getEnvVar('API_URL') : null;
        if (runtimeHost != null && runtimeHost.isNotEmpty) return runtimeHost;

        return dotenv.env['API_URL'] ?? AppConstants.defaultApiUrl;
    }

    static bool get isDebugMode {
        final runtimeDebug = kIsWeb ? getEnvVar('DEBUG_MODE') : null;
        if (runtimeDebug != null && runtimeDebug.isNotEmpty) return runtimeDebug.toLowerCase() == 'true';

        return (dotenv.env['DEBUG_MODE'] ?? '').toLowerCase() == 'true';
    }

    static bool get isLoggingEnabled {
        final runtimeLogging = kIsWeb ? getEnvVar('ENABLE_LOGGING') : null;
        if (runtimeLogging != null && runtimeLogging.isNotEmpty) return runtimeLogging.toLowerCase() == 'true';

        return (dotenv.env['ENABLE_LOGGING'] ?? '').toLowerCase() == 'true';
    }

    static String apiUrl(String endpoint) {
        final baseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.substring(0, apiBaseUrl.length - 1) : apiBaseUrl;
        final cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/$endpoint';

        return '$baseUrl$cleanEndpoint';
    }

    static void printConfig() {
        if (isDebugMode) {
            AppLogger.debug('API Base URL: $apiBaseUrl');
            AppLogger.debug('Debug Mode: $isDebugMode');
            AppLogger.debug('Logging: $isLoggingEnabled');
        }
    }
}

import 'package:flutter_dotenv/flutter_dotenv.dart';

import '../utils/app_logger.dart';
import 'app_constants.dart';

class AppConfig {
    static String get apiHost => 
        dotenv.env['API_HOST'] ?? AppConstants.defaultApiHost;

    static int get apiPort => 
        int.tryParse(dotenv.env['API_PORT'] ?? '') ?? AppConstants.defaultApiPort;

    static String get apiBaseUrl => 
        ("http://$apiHost:$apiPort");

    static bool get isDebugMode => 
        dotenv.env['DEBUG_MODE']?.toLowerCase() == 'true';

    static bool get isLoggingEnabled => 
        dotenv.env['ENABLE_LOGGING']?.toLowerCase() == 'true';

    static String apiUrl(String endpoint) {
        final baseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.substring(0, apiBaseUrl.length - 1) : apiBaseUrl;
        final cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/$endpoint';

        return '$baseUrl$cleanEndpoint';
    }

    static void printConfig() {
        if (isDebugMode) {
            AppLogger.debug('API Base URL: $apiBaseUrl');
            AppLogger.debug('API Host: $apiHost');
            AppLogger.debug('API Port: $apiPort');
            AppLogger.debug('Debug Mode: $isDebugMode');
            AppLogger.debug('Logging: $isLoggingEnabled');
        }
    }
}

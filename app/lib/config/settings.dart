import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:developer' as developer;

class AppConfig {
    static String get apiHost => 
        dotenv.env['API_HOST'] ?? 'localhost';

    static int get apiPort => 
        int.tryParse(dotenv.env['API_PORT'] ?? '') ?? 8000;

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
            developer.log('API Base URL: $apiBaseUrl');
            developer.log('API Host: $apiHost');
            developer.log('API Port: $apiPort');
            developer.log('Debug Mode: $isDebugMode');
            developer.log('Logging: $isLoggingEnabled');
        }
    }
}

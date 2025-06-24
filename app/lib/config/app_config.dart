import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  /// API base URL (e.g., http://localhost:8000 or http://192.168.1.100:8000)
  static String get apiBaseUrl => 
      dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000';
  
  /// API host (e.g., localhost or my-pc.local)
  static String get apiHost => 
      dotenv.env['API_HOST'] ?? 'localhost';
  
  /// API port
  static int get apiPort => 
      int.tryParse(dotenv.env['API_PORT'] ?? '') ?? 8000;
  
  /// Debug mode flag
  static bool get isDebugMode => 
      dotenv.env['DEBUG_MODE']?.toLowerCase() == 'true';
  
  /// Logging enabled flag
  static bool get isLoggingEnabled => 
      dotenv.env['ENABLE_LOGGING']?.toLowerCase() == 'true';
  
  /// Full API URL for endpoints
  static String apiUrl(String endpoint) {
    final baseUrl = apiBaseUrl.endsWith('/') 
        ? apiBaseUrl.substring(0, apiBaseUrl.length - 1)
        : apiBaseUrl;
    final cleanEndpoint = endpoint.startsWith('/') 
        ? endpoint 
        : '/$endpoint';
    return '$baseUrl$cleanEndpoint';
  }
  
  /// Print configuration (for debugging)
  static void printConfig() {
    if (isDebugMode) {
      print('=== App Configuration ===');
      print('API Base URL: $apiBaseUrl');
      print('API Host: $apiHost');
      print('API Port: $apiPort');
      print('Debug Mode: $isDebugMode');
      print('Logging: $isLoggingEnabled');
      print('========================');
    }
  }
}

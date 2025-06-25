import 'dart:io';
import 'package:flutter/services.dart';

class HtmlTemplateService {
  static final Map<String, String> _cache = {};

  /// Load HTML template from lib/templates/ directory
  static Future<String> loadTemplate(String templateName) async {
    // Check cache first
    if (_cache.containsKey(templateName)) {
      return _cache[templateName]!;
    }

    try {
      // Load from assets using rootBundle
      final String content = await rootBundle.loadString('lib/templates/$templateName');
      _cache[templateName] = content;
      return content;
    } catch (e) {
      // Fallback: try to read directly from file system (for development)
      try {
        final file = File('lib/templates/$templateName');
        if (await file.exists()) {
          final content = await file.readAsString();
          _cache[templateName] = content;
          return content;
        }
      } catch (_) {
        // Ignore file system errors
      }
      
      throw Exception('Could not load template: $templateName');
    }
  }

  /// Load OAuth success template
  static Future<String> getSuccessTemplate() async {
    return await loadTemplate('oauth_success.html');
  }

  /// Load OAuth error template
  static Future<String> getErrorTemplate() async {
    return await loadTemplate('oauth_error.html');
  }

  /// Clear template cache
  static void clearCache() {
    _cache.clear();
  }
}

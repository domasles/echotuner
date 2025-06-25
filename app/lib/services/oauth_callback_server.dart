import 'dart:io';
import 'dart:async';
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import 'html_template_service.dart';

class OAuthCallbackServer {
  static OAuthCallbackServer? _instance;
  static OAuthCallbackServer get instance => _instance ??= OAuthCallbackServer._();
  
  OAuthCallbackServer._();
  
  HttpServer? _server;
  Completer<String>? _sessionCompleter;
  String? _expectedState;
  
  /// Set the expected state for validation
  void setExpectedState(String state) {
    _expectedState = state;
  }
  
  /// Start the local callback server on an available port
  Future<int> startServer(String expectedState) async {
    _expectedState = expectedState;
    _sessionCompleter = Completer<String>();
    
    // Find an available port starting from 8080
    for (int port = 8080; port < 8090; port++) {
      try {
        _server = await HttpServer.bind('localhost', port);
        
        _server!.listen((HttpRequest request) async {
          try {
            if (request.uri.path == '/auth/callback') {
              await _handleOAuthCallback(request);
            } else {
              request.response.statusCode = 404;
              request.response.write('Not Found');
            }
          } catch (e, stackTrace) {
            debugPrint('OAuth callback error: $e');
            debugPrint('Stack trace: $stackTrace');
            request.response.statusCode = 500;
            request.response.write('Internal Server Error');
          } finally {
            await request.response.close();
          }
        });
        
        return port;
      } catch (e) {
        // Port is occupied, try next one
        debugPrint('Failed to bind to port $port: $e');
        continue;
      }
    }
    
    throw Exception('Could not find available port for OAuth callback server');
  }
  
  Future<void> _handleOAuthCallback(HttpRequest request) async {
    final code = request.uri.queryParameters['code'];
    final state = request.uri.queryParameters['state'];
    final error = request.uri.queryParameters['error'];
    
    request.response.headers.contentType = ContentType.html;
    
    if (error != null) {
      _sessionCompleter!.completeError(Exception('OAuth error: $error'));
      request.response.write(await _buildErrorPage(error));
      return;
    }
    
    if (code == null || state == null) {
      _sessionCompleter!.completeError(Exception('Missing authorization code or state'));
      request.response.write(await _buildErrorPage('Missing authorization code or state'));
      return;
    }
    
    if (state != _expectedState) {
      _sessionCompleter!.completeError(Exception('Invalid state parameter'));
      request.response.write(await _buildErrorPage('Invalid state parameter'));
      return;
    }
    
    // Forward to the main API to exchange code for session
    _handleCallback(code, state);
    
    request.response.write(await _buildSuccessPage());
  }
  
  /// Wait for the OAuth callback to complete
  Future<String> waitForCallback() async {
    if (_sessionCompleter == null) {
      throw Exception('Server not started');
    }
    return _sessionCompleter!.future;
  }
  
  /// Stop the callback server
  Future<void> stopServer() async {
    if (_server != null) {
      await _server!.close();
      _server = null;
    }
    _sessionCompleter = null;
    _expectedState = null;
  }
  
  void _handleCallback(String code, String state) async {
    try {
      // Make a request to our main API to exchange the code for a session
      final response = await http.get(
        Uri.parse('${AppConfig.apiUrl('/auth/callback')}?code=$code&state=$state'),
      );
      
      if (response.statusCode == 200) {
        // Parse the HTML response to extract session ID
        final responseBody = response.body;
        
        // Extract session ID from the HTML response
        final sessionMatch = RegExp(r"sessionId: '([^']+)'").firstMatch(responseBody);
        if (sessionMatch != null) {
          final sessionId = sessionMatch.group(1)!;
          _sessionCompleter!.complete(sessionId);
        } else {
          _sessionCompleter!.completeError(Exception('Could not extract session ID from response'));
        }
      } else {
        _sessionCompleter!.completeError(Exception('Failed to exchange code for session'));
      }
    } catch (e, stackTrace) {
      debugPrint('OAuth callback exchange error: $e');
      debugPrint('Stack trace: $stackTrace');
      _sessionCompleter!.completeError(e);
    }
  }
  
  Future<String> _buildSuccessPage() async {
    return await HtmlTemplateService.getSuccessTemplate();
  }
  
  Future<String> _buildErrorPage(String error) async {
    final template = await HtmlTemplateService.getErrorTemplate();
    return template.replaceAll('{{error}}', error);
  }
}

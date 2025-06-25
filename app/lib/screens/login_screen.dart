import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

import '../services/auth_service.dart';
import '../models/auth_models.dart';
import '../config/app_config.dart';

class LoginScreen extends StatefulWidget {
    const LoginScreen({super.key});

    @override
    State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
    bool _isLoading = false;

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            backgroundColor: const Color(0xFF0F0A1A),
            body: SafeArea(
                child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                            const Spacer(),

                            _buildLogo(),
                            const SizedBox(height: 40),

                            _buildWelcomeText(),
                            const SizedBox(height: 60),

                            _buildFeaturesList(),

                            const Spacer(),

                            _buildLoginButton(),
                            const SizedBox(height: 32),
                        ],
                    ),
                ),
            ),
        );
    }

    Widget _buildLogo() {
        return Column(
            children: [
                Material(
                    type: MaterialType.transparency,
                    child: Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                            gradient: LinearGradient(
                                colors: [
                                    const Color(0xFF8B5CF6),
                                    const Color(0xFFA78BFA),
                                ],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(25),
                            // Explicitly disable any shadows/elevation effects
                            boxShadow: null,
                        ),
                        child: Icon(
                            Icons.music_note_rounded,
                            size: 50,
                            color: Colors.white,
                            shadows: const [], // Explicitly no shadows
                            textDirection: TextDirection.ltr, // Ensure no RTL effects
                        ),
                    ),
                ),
                const SizedBox(height: 24),
                Text(
                    'EchoTuner',
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        shadows: const [], // Ensure no text shadows either
                    ),
                ),
            ],
        );
    }

    Widget _buildWelcomeText() {
        return Column(
            children: [
                Text(
                    'Welcome',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontSize: 28,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                    ),
                ),

                const SizedBox(height: 12),
                Text(
                    'Connect your Spotify account to create personalized playlists with AI',
                    textAlign: TextAlign.center,

                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontSize: 16,
                        color: Colors.white70,
                        height: 1.5,
                    ),
                ),
            ],
        );
    }

    Widget _buildFeaturesList() {
        final features = [
            {'icon': Icons.smart_toy_rounded, 'text': 'AI-powered playlist generation'},
            {'icon': Icons.search_rounded, 'text': 'Real-time song search'},
            {'icon': Icons.tune_rounded, 'text': 'Personalized recommendations'},
        ];

        return Column(
            children: features.map((feature) => 
                Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8.0),
                    child: Row(
                        children: [
                            Container(
                                width: 40,
                                height: 40,

                                decoration: BoxDecoration(
                                    color: const Color(0xFF1A1625),
                                    borderRadius: BorderRadius.circular(12),
                                ),

                                child: Icon(
                                    feature['icon'] as IconData,
                                    color: const Color(0xFF8B5CF6),
                                    size: 20,
                                ),
                            ),

                            const SizedBox(width: 16),
                            Expanded(
                                child: Text(
                                    feature['text'] as String,
                                    style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                        fontWeight: FontWeight.w500,
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ).toList(),
        );
    }

    Widget _buildLoginButton() {
        return SizedBox(
            width: double.infinity,
            height: 56,

            child: ElevatedButton(
                onPressed: _isLoading ? null : _handleLogin,
                style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1DB954),
                    foregroundColor: Colors.white,
                    elevation: 4,
                    shadowColor: const Color(0xFF1DB954).withValues(alpha: 255 * 0.3),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                ),

                child: _isLoading ? const Row(
					mainAxisAlignment: MainAxisAlignment.center,
					children: [
						SizedBox(
							width: 24,
							height: 24,

							child: CircularProgressIndicator(
								strokeWidth: 2.5,
								valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
							),
						),

						SizedBox(width: 16),
						Text(
							'Connecting...',
							style: TextStyle(
								fontSize: 16,
								fontWeight: FontWeight.w600,
							),
						),
					],
				)
				
				: Row(
					mainAxisAlignment: MainAxisAlignment.center,
					children: [
						Image.asset(
							'assets/spotify_icon.png',
							width: 24,
							height: 24,

							errorBuilder: (context, error, stackTrace) => const Icon(
								Icons.music_note,
								size: 24,
							),
						),

						const SizedBox(width: 12),
						const Text(
							'Connect with Spotify',
							style: TextStyle(
								fontSize: 16,
								fontWeight: FontWeight.w600,
							),
						),
					],
				),
            ),
        );
    }

    Future<void> _handleLogin() async {
        setState(() {
            _isLoading = true;
        });

        try {
            final authService = context.read<AuthService>();
            AuthInitResponse authResponse;

            if (kIsWeb || Platform.isWindows || Platform.isMacOS || Platform.isLinux) {
                authResponse = await authService.initiateDesktopAuth();
                await _handleDesktopAuth(authResponse);
            }
			
			else {
                authResponse = await authService.initiateAuth();
                await _handleMobileAuth(authResponse);
            }
        }
		
		catch (e, stackTrace) {
            // Log the detailed error for debugging
            debugPrint('Login error: $e');
            debugPrint('Stack trace: $stackTrace');
            
            // Show user-friendly error message
            String errorMessage = 'Failed to connect to Spotify. Please try again.';
            if (e.toString().contains('timeout')) {
                errorMessage = 'Connection timeout. Please check your internet connection and try again.';
            } else if (e.toString().contains('network')) {
                errorMessage = 'Network error. Please check your internet connection.';
            }
            
            _showErrorDialog(errorMessage);
        }
		
		finally {
            setState(() {
                _isLoading = false;
            });
        }
    }

    Future<void> _handleDesktopAuth(AuthInitResponse authResponse) async {
        if (await canLaunchUrl(Uri.parse(authResponse.authUrl))) {
            if (!mounted) return;
            final authService = context.read<AuthService>();

            await launchUrl(
                Uri.parse(authResponse.authUrl),
                mode: LaunchMode.externalApplication,
            );

            _showInfoDialog(
                'Complete the Spotify authentication in your browser. '
                'This app will automatically detect when you\'re done.'
            );
            
            try {
                await authService.completeDesktopAuth();
            }
			
			catch (e, stackTrace) {
                if (mounted) {
                    debugPrint('Desktop auth error: $e');
                    debugPrint('Stack trace: $stackTrace');
                    
                    String errorMessage = 'Authentication failed or timed out.';
                    if (e.toString().contains('timeout')) {
                        errorMessage = 'Authentication timed out. Please try again.';
                    } else if (e.toString().contains('cancelled')) {
                        errorMessage = 'Authentication was cancelled.';
                    }
                    
                    _showErrorDialog(errorMessage);
                }
            }
        }
    }

    Future<void> _handleMobileAuth(AuthInitResponse authResponse) async {
        if (!mounted) return;
        
        final result = await Navigator.of(context).push<String>(
            MaterialPageRoute(
                builder: (context) => SpotifyAuthWebView(
                    authUrl: authResponse.authUrl,
                ),
            ),
        );

        if (result != null && mounted) {
            final authService = context.read<AuthService>();
            await authService.setSession(result);
        }
    }

    void _showErrorDialog(String message) {
        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text(
                    'Error',
                    style: TextStyle(color: Colors.white),
                ),

                content: Text(
                    message,
                    style: const TextStyle(color: Colors.white70),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'OK',
                            style: TextStyle(color: Color(0xFF8B5CF6)),
                        ),
                    ),
                ],
            ),
        );
    }

    void _showInfoDialog(String message) {
        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text(
                    'Information',
                    style: TextStyle(color: Colors.white),
                ),

                content: Text(
                    message,
                    style: const TextStyle(color: Colors.white70),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'OK',
                            style: TextStyle(color: Color(0xFF8B5CF6)),
                        ),
                    ),
                ],
            ),
        );
    }
}

class SpotifyAuthWebView extends StatefulWidget {
    final String authUrl;

    const SpotifyAuthWebView({
        super.key,
        required this.authUrl,
    });

    @override
    State<SpotifyAuthWebView> createState() => _SpotifyAuthWebViewState();
}

class _SpotifyAuthWebViewState extends State<SpotifyAuthWebView> {
    WebViewController? _controller;

    @override
    void initState() {
        super.initState();
        
        if (Platform.isAndroid || Platform.isIOS) {
            _controller = WebViewController()
                ..setJavaScriptMode(JavaScriptMode.unrestricted)
                ..setNavigationDelegate(
                    NavigationDelegate(
                        onPageFinished: (String url) {
                            if (url.contains('${AppConfig.apiHost}:${AppConfig.apiPort}/auth/callback')) {
                                _controller!.runJavaScript('''
                                    if (document.body.innerHTML.includes('SPOTIFY_AUTH_SUCCESS')) {
                                        // Extract session ID from the page
                                        var scripts = document.getElementsByTagName('script');
                                        for (var i = 0; i < scripts.length; i++) {
                                            var scriptContent = scripts[i].innerHTML;
                                            var sessionMatch = scriptContent.match(/sessionId: '([^']+)'/);
                                            if (sessionMatch) {
                                                window.flutter_inappwebview.callHandler('sessionId', sessionMatch[1]);
                                            }
                                        }
                                    }
                                ''');
                            }
                        },
                    ),
                )
                ..addJavaScriptChannel(
                    'sessionId',
                    onMessageReceived: (JavaScriptMessage message) {
                        Navigator.of(context).pop(message.message);
                    },
                )
                ..loadRequest(Uri.parse(widget.authUrl));
        }
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            backgroundColor: const Color(0xFF0F0A1A),
            appBar: AppBar(
                backgroundColor: const Color(0xFF0F0A1A),
                foregroundColor: Colors.white,
                title: const Text('Connect Spotify'),

                leading: IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                ),
            ),

            body: _controller != null ? WebViewWidget(controller: _controller!) : const Center(
				child: Text(
					'WebView not available on this platform',
					style: TextStyle(color: Colors.white),
				),
			),
        );
    }
}

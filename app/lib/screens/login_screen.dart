import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../models/auth_models.dart';

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
                            boxShadow: null,
                        ),

                        child: Icon(
                            Icons.music_note_rounded,
                            size: 50,
                            color: Colors.white,
                            shadows: const [],
                            textDirection: TextDirection.ltr,
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
                        shadows: const [],
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
            final authResponse = await authService.initiateAuth();
			
            await _handleBrowserAuth(authResponse);
        }
		
		catch (e, stackTrace) {
            debugPrint('Login error: $e');
            debugPrint('Stack trace: $stackTrace');

            String errorMessage = 'Failed to connect to Spotify. Please try again.';

            if (e.toString().contains('timeout')) {
                errorMessage = 'Connection timeout. Please check your internet connection and try again.';
            }
			
			else if (e.toString().contains('network')) {
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

    Future<void> _handleBrowserAuth(AuthInitResponse authResponse) async {
        if (await canLaunchUrl(Uri.parse(authResponse.authUrl))) {
            if (!mounted) return;
            final authService = context.read<AuthService>();

            await launchUrl(
                Uri.parse(authResponse.authUrl),
                mode: LaunchMode.externalApplication,
            );
            
            try {
                await authService.completeAuth();
            }
			
			catch (e, stackTrace) {
                if (mounted) {
                    debugPrint('Browser auth error: $e');
                    debugPrint('Stack trace: $stackTrace');
                    
                    String errorMessage = 'Authentication failed or timed out.';

                    if (e.toString().contains('timeout')) {
                        errorMessage = 'Authentication timed out. Please try again.';
                    }
					
					else if (e.toString().contains('cancelled')) {
                        errorMessage = 'Authentication was cancelled.';
                    }
                    
                    _showErrorDialog(errorMessage);
                }
            }
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

}

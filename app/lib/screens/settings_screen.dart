import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/auth_service.dart';

void _showCustomSnackbarStatic(BuildContext context, String message, {bool isError = false, bool isSuccess = false}) {
    Color borderColor;
    if (isSuccess) {
        borderColor = Color(0xFF4CAF50);
    }
	
	else if (isError) {
        borderColor = Color(0xFFD32F2F);
    }
	
	else {
        borderColor = Color(0xFF666666);
    }

    final overlay = Overlay.of(context);
    late OverlayEntry overlayEntry;
    
    overlayEntry = OverlayEntry(
        builder: (context) => Positioned(
            bottom: 16,
            left: 16,
            right: 16,

            child: Material(
                elevation: 0,
                color: Colors.transparent,

                child: Container(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                        color: Color(0xFF1A1625),
                        borderRadius: BorderRadius.circular(28),
                        border: Border.all(color: borderColor, width: 1),
                    ),

                    child: Text(
                        message,
                        style: TextStyle(color: Colors.white),
                    ),
                ),
            ),
        ),
    );
    
    overlay.insert(overlayEntry);
    
    Future.delayed(Duration(seconds: 2), () {
        overlayEntry.remove();
    });
}

class SettingsScreen extends StatelessWidget {
    const SettingsScreen({super.key});

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('Settings'),
                centerTitle: true,
            ),

            body: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                    const SizedBox(height: 24),
                    const SectionHeader(title: 'Account'),

                    SettingsTile(
                        icon: Icons.account_circle,
                        title: 'Profile',
                        subtitle: 'Manage your profile settings',
                    ),

                    Consumer<AuthService>(
                        builder: (context, authService, child) {
                            return SettingsTile(
                                icon: Icons.music_note,
                                title: 'Spotify Connection',
                                subtitle: authService.isAuthenticated ? 'Connected to Spotify' : 'Not connected',
                            );
                        },
                    ),

                    const SizedBox(height: 24),
                    const SectionHeader(title: 'Preferences'),

                    SettingsTile(
                        icon: Icons.tune,
                        title: 'Music Preferences',
                        subtitle: 'Set your favorite genres and artists',
                    ),

                    SettingsTile(
                        icon: Icons.notifications,
                        title: 'Notifications',
                        subtitle: 'Manage notification settings',
                    ),

                    SizedBox(height: 24),

                    SectionHeader(title: 'About'),
                    SettingsTile(
                        icon: Icons.info,
                        title: 'About EchoTuner',
                        subtitle: 'Version 1.0.0',
                    ),

                    SettingsTile(
                        icon: Icons.help,
                        title: 'Help & Support',
                        subtitle: 'Get help and contact support',
                    ),

                    const SettingsTile(
                        icon: Icons.privacy_tip,
                        title: 'Privacy Policy',
                        subtitle: 'Read our privacy policy',
                    ),

                    const SizedBox(height: 32),
                    Consumer<AuthService>(
                        builder: (context, authService, child) {
                            if (!authService.isAuthenticated) {
                                return const SizedBox.shrink();
                            }
                            
                            return Container(
                                margin: const EdgeInsets.symmetric(horizontal: 16),
                                child: ElevatedButton(
                                    onPressed: () => _showLogoutDialog(context, authService),
                                    style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.red,
                                        foregroundColor: Colors.white,
                                        side: const BorderSide(color: Color(0xFF2A2A2A), width: 0.5),
                                        padding: const EdgeInsets.symmetric(vertical: 16),
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                    ),

                                    child: const Text(
                                        'Logout',
                                        style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                        ),
                                    ),
                                ),
                            );
                        },
                    ),

                    const SizedBox(height: 32),
                ],
            ),
        );
    }

    void _showLogoutDialog(BuildContext context, AuthService authService) {
        showDialog(
            context: context,
            builder: (context) => AlertDialog(
                backgroundColor: const Color(0xFF1A1625),
                title: const Text(
                    'Logout',
                    style: TextStyle(color: Colors.white),
                ),

                content: const Text(
                    'Are you sure you want to logout? You\'ll need to reconnect your Spotify account to use the app.',
                    style: TextStyle(color: Colors.white70),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'Cancel',
                            style: TextStyle(color: Colors.white54),
                        ),
                    ),

                    TextButton(
                        onPressed: () async {
                            final navigator = Navigator.of(context);
                            
                            navigator.pop();
                            
                            try {
                                await authService.logout();
                                
                                navigator.pushNamedAndRemoveUntil(
                                    '/', 
                                    (route) => false,
                                );
                                
                            } catch (e) {
                                _showCustomSnackbar(context, 'Logout failed: ${e.toString()}', isError: true);
                            }
                        },
						
                        child: const Text(
                            'Logout',
                            style: TextStyle(color: Colors.red),
                        ),
                    ),
                ],
            ),
        );
    }

    void _showCustomSnackbar(BuildContext context, String message, {bool isError = false, bool isSuccess = false}) {
        Color borderColor;
        if (isSuccess) {
            borderColor = Color(0xFF4CAF50);
        }
		
		else if (isError) {
            borderColor = Color(0xFFD32F2F);
        }
		
		else {
            borderColor = Color(0xFF666666);
        }

        final overlay = Overlay.of(context);
        late OverlayEntry overlayEntry;
        
        overlayEntry = OverlayEntry(
            builder: (context) => Positioned(
                bottom: 16,
                left: 16,
                right: 16,

                child: Material(
                    elevation: 0,
                    color: Colors.transparent,
                    child: Container(
                        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                            color: Color(0xFF1A1625),
                            borderRadius: BorderRadius.circular(28),
                            border: Border.all(color: borderColor, width: 1),
                        ),

                        child: Text(
                            message,
                            style: TextStyle(color: Colors.white),
                        ),
                    ),
                ),
            ),
        );
        
        overlay.insert(overlayEntry);
        
        Future.delayed(Duration(seconds: 2), () {
            overlayEntry.remove();
        });
    }
}

class SectionHeader extends StatelessWidget {
    final String title;
    const SectionHeader({super.key, required this.title});

    @override
    Widget build(BuildContext context) {
        return Padding(
            padding: const EdgeInsets.only(left: 16, bottom: 8, top: 8),
            child: Text(
                title,
				style: const TextStyle(
                    color: Color(0xFF8B5CF6),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                ),
            ),
        );
    }
}

class SettingsTile extends StatelessWidget {
    final IconData icon;
    final String title;
    final String subtitle;
    final VoidCallback? onTap;
    
    const SettingsTile({super.key, required this.icon, required this.title, required this.subtitle, this.onTap});

    @override
    Widget build(BuildContext context) {
        return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
				leading: Icon(
                    icon,
                    color: const Color(0xFF8B5CF6),
                ),

                title: Text(
                    title,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w500,
                    ),
                ),

                subtitle: Text(
                    subtitle,
                    style: const TextStyle(color: Colors.white70),
                ),

                trailing: const Icon(
                    Icons.chevron_right,
                    color: Colors.white54,
                ),
                    
                onTap: onTap ?? () {
                    _showCustomSnackbarStatic(context, 'Feature coming soon!');
                },
            ),
        );
    }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';

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
                                subtitle: authService.isAuthenticated 
                                    ? 'Connected to Spotify' 
                                    : 'Not connected',
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
                                        padding: const EdgeInsets.symmetric(vertical: 16),
                                        shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(12),
                                        ),
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
                            final messenger = ScaffoldMessenger.of(context);
                            
                            navigator.pop(); // Close dialog first
                            
                            try {
                                await authService.logout();
                                
                                // Force navigation to root and clear all routes
                                navigator.pushNamedAndRemoveUntil(
                                    '/', 
                                    (route) => false,
                                );
                                
                            } catch (e) {
                                // Handle logout error
                                messenger.showSnackBar(
                                    SnackBar(
                                        content: Text('Logout failed: ${e.toString()}'),
                                        backgroundColor: Colors.red,
                                    ),
                                );
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
                    ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text('Feature coming soon!'),
                            duration: Duration(seconds: 2),
                        ),
                    );
                },
            ),
        );
    }
}

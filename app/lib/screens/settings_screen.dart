import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import '../services/message_service.dart';
import '../services/auth_service.dart';
import '../config/app_constants.dart';
import '../config/app_colors.dart';
import '../utils/app_logger.dart';

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
                        icon: Icons.notifications,
                        title: 'Notifications',
                        subtitle: 'Manage notification settings',
                    ),

                    SizedBox(height: 24),

                    SectionHeader(title: 'About'),
                    SettingsTile(
                        icon: Icons.info,
                        title: 'About ${AppConstants.appName}',
                        subtitle: 'Version ${AppConstants.appVersion}',
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
                                        backgroundColor: Colors.red.shade600,
                                        foregroundColor: Colors.white,
                                        side: BorderSide(color: Colors.red.shade700, width: 1),
                                        padding: const EdgeInsets.symmetric(vertical: 20),
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                        elevation: 4,
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
                backgroundColor: AppColors.surface,
                title: const Text(
                    'Logout',
                    style: TextStyle(color: AppColors.textPrimary),
                ),

                content: const Text(
                    'Are you sure you want to logout? You\'ll need to reconnect your Spotify account to use the app.',
                    style: TextStyle(color: AppColors.textSecondary),
                ),

                actions: [
                    TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text(
                            'Cancel',
                            style: TextStyle(color: AppColors.textTertiary),
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
                            }

                            catch (e) {
                                AppLogger.error('Logout failed: ${e.toString()}');
                            }
                        },

                        child: const Text(
                            'Logout',
                            style: TextStyle(color: AppColors.errorIcon),
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
                    color: AppColors.primary,
                ),

                title: Text(
                    title,
                    style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w500,
                    ),
                ),

                subtitle: Text(
                    subtitle,
                    style: const TextStyle(color: AppColors.textSecondary),
                ),

                trailing: const Icon(
                    Icons.chevron_right,
                    color: AppColors.textTertiary,
                ),

                onTap: onTap ?? () {
                    MessageService.showInfo(context, 'Feature coming soon!');
                },
            ),
        );
    }
}

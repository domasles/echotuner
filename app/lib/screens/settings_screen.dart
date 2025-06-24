import 'package:flutter/material.dart';

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
                children: const [
                    SectionHeader(title: 'Account'),
                    SettingsTile(
                        icon: Icons.account_circle,
                        title: 'Profile',
                        subtitle: 'Manage your profile settings',
                    ),

                    SettingsTile(
                        icon: Icons.music_note,
                        title: 'Spotify Connection',
                        subtitle: 'Connect your Spotify account',
                    ),

                    SizedBox(height: 24),
                    SectionHeader(title: 'Preferences'),
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

                    SettingsTile(
                        icon: Icons.privacy_tip,
                        title: 'Privacy Policy',
                        subtitle: 'Read our privacy policy',
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

import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../config/app_constants.dart';
import '../config/app_colors.dart';
import '../services/message_service.dart';

class AboutScreen extends StatelessWidget {
    const AboutScreen({super.key});

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: const Text('About EchoTuner'),
                centerTitle: true,
            ),
            body: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                        const SizedBox(height: 32),
                        
                        // Logo
                        SizedBox(
                            width: 120,
                            height: 120,
                            child: SvgPicture.asset(
                                'assets/logos/EchoTunerLogo.svg',
                                fit: BoxFit.contain,
                            ),
                        ),

                        const SizedBox(height: 24),

                        // App Name
                        Text(
                            AppConstants.appName,
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                            ),
                        ),

                        const SizedBox(height: 8),

                        // Version
                        Text(
                            'Version ${AppConstants.appVersion}',
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                color: AppColors.textSecondary,
                            ),
                        ),

                        const SizedBox(height: 32),

                        // Description Card
                        Card(
                            child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                        Text(
                                            'About',
                                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                                fontWeight: FontWeight.bold,
                                            ),
                                        ),
                                        const SizedBox(height: 12),
                                        Text(
                                            AppConstants.appDescription,
                                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                                color: AppColors.textSecondary,
                                                height: 1.5,
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ),

                        const SizedBox(height: 24),

                        // Links Card
                        Card(
                            child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                        Text(
                                            'Links',
                                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                                fontWeight: FontWeight.bold,
                                            ),
                                        ),
                                        const SizedBox(height: 16),
                                        
                                        _buildLinkTile(
                                            context,
                                            'Source Code',
                                            'View on GitHub',
                                            Icons.code,
                                            AppConstants.githubRepositoryUrl,
                                        ),
                                        
                                        const Divider(height: 24),
                                        
                                        _buildLinkTile(
                                            context,
                                            'EchoTuner API',
                                            'API Documentation',
                                            Icons.api,
                                            '${AppConstants.githubRepositoryUrl}/tree/main/docs/api',
                                        ),
                                    ],
                                ),
                            ),
                        ),

                        const SizedBox(height: 24),

                        // Coming Soon Card
                        Card(
                            child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                        Row(
                                            children: [
                                                const Icon(
                                                    Icons.construction,
                                                    color: AppColors.textSecondary,
                                                ),
                                                const SizedBox(width: 8),
                                                Text(
                                                    'Coming Soon',
                                                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                                        fontWeight: FontWeight.bold,
                                                    ),
                                                ),
                                            ],
                                        ),
                                        const SizedBox(height: 12),
                                        Text(
                                            '• Privacy Policy\n'
                                            '• Help & Support\n'
                                            '• Notification Settings\n'
                                            '• Advanced User Settings',
                                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                                color: AppColors.textSecondary,
                                                height: 1.5,
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ),

                        const SizedBox(height: 32),
                    ],
                ),
            ),
        );
    }

    Widget _buildLinkTile(
        BuildContext context,
        String title,
        String subtitle,
        IconData icon,
        String url,
    ) {
        return ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(
                icon,
                color: AppColors.textSecondary,
            ),
            title: Text(
                title,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                ),
            ),
            subtitle: Text(
                subtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                ),
            ),
            trailing: const Icon(
                Icons.open_in_new,
                color: AppColors.textSecondary,
            ),
            onTap: () => _launchUrl(context, url),
        );
    }

    Future<void> _launchUrl(BuildContext context, String url) async {
        try {
            final uri = Uri.parse(url);
            if (await canLaunchUrl(uri)) {
                await launchUrl(uri, mode: LaunchMode.externalApplication);
            } else {
                if (context.mounted) {
                    MessageService.showError(context, 'Could not open URL');
                }
            }
        } catch (e) {
            if (context.mounted) {
                MessageService.showError(context, 'Could not open URL');
            }
        }
    }
}

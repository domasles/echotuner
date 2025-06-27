import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/material.dart';

import '../models/info_message.dart';
import '../config/app_colors.dart';

class InfoMessageWidget extends StatelessWidget {
  final InfoMessage message;
  final VoidCallback? onDismiss;

  const InfoMessageWidget({
    super.key,
    required this.message,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
        return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            
            decoration: BoxDecoration(
                color: _getBackgroundColor(),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                color: _getBorderColor(),
                width: 1,
            ),
        ),

        child: Row(
            children: [
                Icon(
                    _getIcon(),
                    color: _getIconColor(),
                    size: 20,
                ),

                const SizedBox(width: 12),
                Expanded(
                    child: Text(
                        message.message,
                        style: TextStyle(
                            color: _getTextColor(),
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                        ),
                    ),
                ),

                if (message.actionLabel != null && (message.onAction != null || message.actionUrl != null)) ...[
                    const SizedBox(width: 8),
                    TextButton(
                        onPressed: () async {
                            if (message.onAction != null) {
                                message.onAction!();
                            }
                            
                            else if (message.actionUrl != null) {
                                final uri = Uri.parse(message.actionUrl!);
                                
                                if (await canLaunchUrl(uri)) {
                                    await launchUrl(uri, mode: LaunchMode.externalApplication);
                                }
                            }
                        },
                        
                        style: TextButton.styleFrom(
                            foregroundColor: _getActionColor(),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            minimumSize: Size.zero,
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),

                        child: Text(
                            message.actionLabel!,
                            style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                            ),
                        ),
                    ),
                ],

                if (onDismiss != null) ...[
                    const SizedBox(width: 4),
                    IconButton(
                        onPressed: onDismiss,
                        icon: const Icon(Icons.close),
                        iconSize: 16,
                        color: _getTextColor().withValues(alpha: 128),
                        padding: EdgeInsets.zero,
                        
                        constraints: const BoxConstraints(
                            minWidth: 24,
                            minHeight: 24,
                        ),
                    ),
                ],
            ],
        ),
        );
    }

    Color _getBackgroundColor() {
        switch (message.type) {
            case InfoMessageType.success:
                return AppColors.successBackground;

            case InfoMessageType.info:
                return AppColors.infoBackground;

            case InfoMessageType.warning:
                return AppColors.warningBackground;

            case InfoMessageType.error:
                return AppColors.errorBackground;
        }
    }

    Color _getBorderColor() {
        switch (message.type) {
            case InfoMessageType.success:
                return AppColors.successIcon;

            case InfoMessageType.info:
                return AppColors.infoIcon;

            case InfoMessageType.warning:
                return AppColors.warningIcon;

            case InfoMessageType.error:
                return AppColors.errorIcon;
        }
    }

    Color _getTextColor() {
        switch (message.type) {
            case InfoMessageType.success:
                return AppColors.successTextBackground;

            case InfoMessageType.info:
                return AppColors.infoTextBackground;

            case InfoMessageType.warning:
                return AppColors.warningTextBackground;

            case InfoMessageType.error:
                return AppColors.errorTextBackground;
        }
    }

    Color _getIconColor() {
        return _getBorderColor();
    }

    Color _getActionColor() {
        return _getBorderColor();
    }

    IconData _getIcon() {
        switch (message.type) {
            case InfoMessageType.success:
                return Icons.check_circle_outline;
                
            case InfoMessageType.info:
                return Icons.info_outline;

            case InfoMessageType.warning:
                return Icons.warning_outlined;

            case InfoMessageType.error:
                return Icons.error_outline;
        }
    }
}

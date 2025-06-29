import 'package:flutter/material.dart';

import '../config/app_constants.dart';
import '../config/app_colors.dart';

class MessageService {
    static void showSuccess(BuildContext context, String message) {
        _showMessage(context, message, MessageType.success);
    }

    static void showError(BuildContext context, String message) {
        _showMessage(context, message, MessageType.error);
    }

    static void showInfo(BuildContext context, String message) {
        _showMessage(context, message, MessageType.info);
    }

    static void showWarning(BuildContext context, String message) {
        _showMessage(context, message, MessageType.warning);
    }

    static void _showMessage(BuildContext context, String message, MessageType type) {
        final overlay = Overlay.of(context);
        late OverlayEntry overlayEntry;

        overlayEntry = OverlayEntry(
            builder: (context) => Stack(
                children: [
                    Positioned(
                        left: 0,
                        right: 0,
                        bottom: AppConstants.messageBottomPosition,

                        child: Center(
                            child: Material(
                                color: Colors.transparent,
                                child: Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: AppConstants.messageHorizontalPadding,
                                        vertical: AppConstants.messageVerticalPadding,
                                    ),

                                    decoration: BoxDecoration(
                                        color: AppColors.surface,
                                        borderRadius: BorderRadius.circular(AppConstants.messageRadius),
                                        border: Border.all(
                                            color: type.color, 
                                            width: AppConstants.messageBorderWidth,
                                        ),
                                    ),

                                    child: _FixedText(message),
                                ),
                            ),
                        ),
                    ),
                ]
            )
        );

        overlay.insert(overlayEntry);

        Future.delayed(AppConstants.messageDisplayDuration, () {
            overlayEntry.remove();
        });
    }
}

class _FixedText extends StatelessWidget {
    final String message;
    const _FixedText(this.message);

    @override
    Widget build(BuildContext context) {
        return MediaQuery(
            data: MediaQuery.of(context).copyWith(textScaler: const TextScaler.linear(1.0)),
            child: Text(
                message,
                textAlign: TextAlign.center,

                style: const TextStyle(
                    fontSize: AppConstants.messageFontSize,
                    fontWeight: FontWeight.w500,
                    color: Colors.white,
                    height: 1.2,
                ),
            ),
        );
    }
}

enum MessageType {
    success(AppColors.success),
    error(AppColors.error),
    info(AppColors.info),
    warning(AppColors.warning);

    const MessageType(this.color);
    final Color color;
}

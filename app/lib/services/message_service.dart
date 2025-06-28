import 'package:flutter/material.dart';

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

    static void _showMessage(BuildContext context, String message, MessageType type) {
        final overlay = Overlay.of(context);
        late OverlayEntry overlayEntry;

        overlayEntry = OverlayEntry(
        builder: (context) => Stack(
            children: [
            Positioned(
                bottom: 90,
                left: 20,
                right: 20,
                child: IgnorePointer(
                child: Center(
                    child: Material(
                    color: Colors.transparent,
                    child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                        color: const Color(0xFF1A1625),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: type.color, width: 1),
                        ),
                        child: _FixedText(message),
                    ),
                    ),
                ),
                ),
            ),
            ],
        ),
        );

        overlay.insert(overlayEntry);

        Future.delayed(const Duration(seconds: 2), () {
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
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: Colors.white,
            height: 1.2,
            ),
        ),
        );
    }
}

enum MessageType {
    success(Color(0xFF4CAF50)),
    error(Color(0xFFD32F2F)),
    info(Color(0xFF666666));

    const MessageType(this.color);
    final Color color;
}

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
            builder: (context) => Positioned(
                bottom: 102,
                left: 16,
                right: 16,
                
                child: Material(
                    elevation: 0,
                    color: Colors.transparent,
                    
                    child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        decoration: BoxDecoration(
                            color: const Color(0xFF1A1625),
                            borderRadius: BorderRadius.circular(28),
                            border: Border.all(color: type.color, width: 1),
                        ),
                        child: Text(
                            message,
                            style: const TextStyle(color: Colors.white),
                        ),
                    ),
                ),
            ),
        );
        
        overlay.insert(overlayEntry);

        Future.delayed(const Duration(seconds: 2), () {
            overlayEntry.remove();
        });
    }
}

enum MessageType {
    success(Color(0xFF4CAF50)),
    error(Color(0xFFD32F2F)),
    info(Color(0xFF666666));

    const MessageType(this.color);
    final Color color;
}

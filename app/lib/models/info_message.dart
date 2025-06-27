import 'package:flutter/material.dart';

class InfoMessage {
    final String id;
    final String message;
    final InfoMessageType type;
    final DateTime timestamp;
    final Duration? duration;
    final String? actionLabel;
    final VoidCallback? onAction;
    final String? actionUrl;

    InfoMessage({
        required this.id,
        required this.message,
        required this.type,
        DateTime? timestamp,
        this.duration = const Duration(seconds: 5),
        this.actionLabel,
        this.onAction,
        this.actionUrl,
    }) : timestamp = timestamp ?? DateTime.now();

    bool get isExpired {
        if (duration == null) return false;
        return DateTime.now().difference(timestamp) > duration!;
    }
}

enum InfoMessageType {
    success,
    info,
    warning,
    error,
}

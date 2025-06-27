import 'package:flutter/foundation.dart';
import 'dart:developer' as developer;

import '../config/app_constants.dart';

class AppLogger {
    static const String _appName = AppConstants.appName;
    
    static void debug(String message, {String? name, Object? error, StackTrace? stackTrace}) {
        if (kDebugMode) {
            developer.log(
                message,
                name: name ?? _appName,
                error: error,
                stackTrace: stackTrace,
                level: 500,
            );
        }
    }

    static void info(String message, {String? name}) {
        developer.log(
            message,
            name: name ?? _appName,
            level: 800,
        );
    }

    static void warning(String message, {String? name, Object? error, StackTrace? stackTrace}) {
        developer.log(
            message,
            name: name ?? _appName,
            error: error,
            stackTrace: stackTrace,
            level: 900,
        );
    }

    static void error(String message, {String? name, Object? error, StackTrace? stackTrace}) {
        developer.log(
            message,
            name: name ?? _appName,
            error: error,
            stackTrace: stackTrace,
            level: 1000,
        );
    }

    static void auth(String message, {Object? error, StackTrace? stackTrace}) {
        debug(message, name: 'Auth', error: error, stackTrace: stackTrace);
    }

    static void playlist(String message, {Object? error, StackTrace? stackTrace}) {
        debug(message, name: 'Playlist', error: error, stackTrace: stackTrace);
    }

    static void api(String message, {Object? error, StackTrace? stackTrace}) {
        debug(message, name: 'API', error: error, stackTrace: stackTrace);
    }
}

import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:io';

class DeviceService {
    static const String _deviceIdKey = 'device_id';

    static Future<String> getDeviceId() async {
        final prefs = await SharedPreferences.getInstance();
        String? deviceId = prefs.getString(_deviceIdKey);

        if (deviceId == null) {
            deviceId = await _generateDeviceId();
            await prefs.setString(_deviceIdKey, deviceId);
        }

        return deviceId;
    }

    static Future<String> _generateDeviceId() async {
        final deviceInfo = DeviceInfoPlugin();

        try {
            if (Platform.isAndroid) {
                final androidInfo = await deviceInfo.androidInfo;
                return 'android_${androidInfo.id}_${androidInfo.model}_${DateTime.now().millisecondsSinceEpoch}';
            }

            else if (Platform.isIOS) {
                final iosInfo = await deviceInfo.iosInfo;
                return 'ios_${iosInfo.identifierForVendor}_${iosInfo.model}_${DateTime.now().millisecondsSinceEpoch}';
            }

            else {
                return 'unknown_${DateTime.now().millisecondsSinceEpoch}';
            }
        }

        catch (e) {
            return 'fallback_${DateTime.now().millisecondsSinceEpoch}';
        }
    }
}

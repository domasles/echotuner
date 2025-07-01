import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';

class DiscoverySystem {
    static const String _discoveryKey = 'discover_new_music';

    bool _discoverNewMusic = true;
    bool get discoverNewMusic => _discoverNewMusic;

    Future<void> initialize() async {
        final prefs = await SharedPreferences.getInstance();
        _discoverNewMusic = prefs.getBool(_discoveryKey) ?? true;
    }

    Future<void> setDiscoveryPreference(bool value) async {
        _discoverNewMusic = value;

        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool(_discoveryKey, value);
    }

    String getGenerationStrategy() {
        return _discoverNewMusic ? 'new_music' : 'existing_music';
    }
}

mixin DiscoveryMixin<T extends StatefulWidget> on State<T> {
    final DiscoverySystem _discoverySystem = DiscoverySystem();
    bool get discoverNewMusic => _discoverySystem.discoverNewMusic;

    Future<void> initializeDiscovery() async {
        await _discoverySystem.initialize();

        if (mounted) {
            setState(() {});
        }
    }

    Future<void> setDiscoveryPreference(bool value) async {
        await _discoverySystem.setDiscoveryPreference(value);

        if (mounted) {
            setState(() {});
        }
    }

    String getGenerationStrategy() {
        return _discoverySystem.getGenerationStrategy();
    }

    Widget buildDiscoverySwitch({required String label, VoidCallback? onChanged}) {
        return Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
                Expanded(
                    child: Text(
                        label,
                        style: Theme.of(context).textTheme.bodyMedium,
                    ),
                ),

                Switch(
                    value: discoverNewMusic,
                    onChanged: (value) async {
                        await setDiscoveryPreference(value);
                        onChanged?.call();
                    },
                ),
            ],
        );
    }
}

import "env_interface.dart";
import 'dart:js' as js;

class WebEnvironment implements Environment {
    @override
    String? getEnvVar(String key) {
        try {
            if (js.context.hasProperty('_env_')) {
                final env = js.context['_env_'];

                if (env != null && env.hasProperty(key)) {
                    return env[key] as String?;
                }
            }
        }
		
		catch (_) {
            // Ignore errors silently
        }

        return null;
    }
}

Environment getEnvironment() => WebEnvironment();

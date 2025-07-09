import 'web_env.dart' if (dart.library.io) 'non_web_env.dart';
import 'env_interface.dart';

Environment env = getEnvironment();
String? getEnvVar(String key) => env.getEnvVar(key);

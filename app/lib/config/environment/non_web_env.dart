import "env_interface.dart";

class NonWebEnvironment implements Environment {
    @override
    String? getEnvVar(String key) => null;
}

Environment getEnvironment() => NonWebEnvironment();

import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import 'providers/playlist_provider.dart';
import 'services/api_service.dart';
import 'screens/home_screen.dart';
import 'config/app_config.dart';

Future<void> main() async {
    await dotenv.load(fileName: ".env");
    AppConfig.printConfig();
    runApp(const EchoTunerApp());
}

class EchoTunerApp extends StatelessWidget {
    const EchoTunerApp({super.key});

    @override
    Widget build(BuildContext context) {
        return MultiProvider(
            providers: [
                Provider<ApiService>(
                    create: (context) => ApiService(),
                ),

                ChangeNotifierProvider<PlaylistProvider>(
                    create: (context) => PlaylistProvider(
                        apiService: context.read<ApiService>(),
                    ),
                ),
            ],

            child: MaterialApp(
                title: 'EchoTuner',
                debugShowCheckedModeBanner: false,

                theme: ThemeData(
                    primarySwatch: Colors.green,
                    scaffoldBackgroundColor: const Color(0xFF121212),

                    appBarTheme: const AppBarTheme(
                        backgroundColor: Color(0xFF121212),
                        foregroundColor: Colors.white,
                        elevation: 0,
                    ),
                    
                    textTheme: const TextTheme(
                        bodyLarge: TextStyle(color: Colors.white),
                        bodyMedium: TextStyle(color: Colors.white70),
                        titleLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                    
                    cardTheme: const CardThemeData(
                        color: Color(0xFF1E1E1E),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.all(Radius.circular(12)),
                        ),
                    ),

                    elevatedButtonTheme: ElevatedButtonThemeData(
                        style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF1DB954),
                            foregroundColor: Colors.white,

                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(25),
                            ),

                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                        ),
                    ),
                    
                    inputDecorationTheme: InputDecorationTheme(
                        filled: true,
                        fillColor: const Color(0xFF2A2A2A),

                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide.none,
                        ),

                        hintStyle: const TextStyle(color: Colors.white54),
                        labelStyle: const TextStyle(color: Colors.white70),
                    ),
                ),
                
                home: const HomeScreen(),
            ),
        );
    }
}

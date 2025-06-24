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
                    useMaterial3: true,
                    brightness: Brightness.dark,

                    colorScheme: ColorScheme.fromSeed(
                        seedColor: const Color(0xFF8B5CF6),
                        brightness: Brightness.dark,
                        surface: const Color(0xFF0F0A1A),
                        onSurface: Colors.white,
                        primary: const Color(0xFF8B5CF6),
                        secondary: const Color(0xFFA78BFA),
                    ),
                    
                    scaffoldBackgroundColor: const Color(0xFF0F0A1A),
					appBarTheme: const AppBarTheme(
                        backgroundColor: Color(0xFF0F0A1A),
                        foregroundColor: Colors.white,
                        elevation: 0,
                        centerTitle: true,
                    ),
                    
                    textTheme: const TextTheme(
                        displayLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                        displayMedium: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                        titleLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                        titleMedium: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                        bodyLarge: TextStyle(color: Colors.white),
                        bodyMedium: TextStyle(color: Colors.white70),
                        bodySmall: TextStyle(color: Colors.white54),
                    ),

					cardTheme: const CardThemeData(
                        color: Color(0xFF1A1625),
                        elevation: 2,

                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.all(Radius.circular(16)),
                        ),
                    ),

                    elevatedButtonTheme: ElevatedButtonThemeData(
                        style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF8B5CF6),
                            foregroundColor: Colors.white,
                            elevation: 3,

                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                            ),

                            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                            textStyle: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                            ),
                        ),
                    ),
                    
                    inputDecorationTheme: InputDecorationTheme(
                        filled: true,
                        fillColor: const Color(0xFF1A1625),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(25),
                            borderSide: BorderSide.none,
                        ),
                        
                        focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(25),
                            borderSide: const BorderSide(color: Color(0xFF8B5CF6), width: 2),
                        ),

                        hintStyle: const TextStyle(color: Colors.white54),
                        labelStyle: const TextStyle(color: Colors.white70),
                    ),
                    
                    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
                        backgroundColor: Color(0xFF1A1625),
                        selectedItemColor: Color(0xFF8B5CF6),
                        unselectedItemColor: Colors.white54,
                        type: BottomNavigationBarType.fixed,
                        elevation: 8,
                    ),
                ),
                
                home: const HomeScreen(),
            ),
        );
    }
}

import 'package:responsive_framework/responsive_framework.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

import 'services/personality_service.dart';
import 'providers/playlist_provider.dart';
import 'services/config_service.dart';
import 'services/auth_service.dart';
import 'config/app_constants.dart';
import 'screens/login_screen.dart';
import 'services/api_service.dart';
import 'screens/home_screen.dart';
import 'config/app_colors.dart';
import 'config/settings.dart';

class _NoGlowScrollBehavior extends ScrollBehavior {
    const _NoGlowScrollBehavior();

    @override
    Widget buildOverscrollIndicator(BuildContext context, Widget child, ScrollableDetails details) {
        return child;
    }
}

Future<void> main() async {
    WidgetsFlutterBinding.ensureInitialized();

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
                ChangeNotifierProvider<AuthService>(
                    create: (context) => AuthService(),
                ),

                Provider<ApiService>(
                    create: (context) {
                        final apiService = ApiService();
                        // Set AuthService reference after both services are created
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                            apiService.setAuthService(context.read<AuthService>());
                        });
                        return apiService;
                    },
                ),

                Provider<ConfigService>(
                    create: (context) => ConfigService(
                        context.read<ApiService>(),
                    ),
                ),

                Provider<PersonalityService>(
                    create: (context) => PersonalityService(
                        apiService: context.read<ApiService>(),
                        authService: context.read<AuthService>(),
                        configService: context.read<ConfigService>(),
                    ),
                ),

                ChangeNotifierProvider<PlaylistProvider>(
                    create: (context) => PlaylistProvider(
                        context.read<ApiService>(),
                        context.read<AuthService>(),
                    ),
                ),
            ],

            child: ScreenUtilInit(
                designSize: const Size(375, 812),
                minTextAdapt: true,
                splitScreenMode: true,

                builder: (context, child) {
                    return MaterialApp(
                        title: AppConstants.appName,
                        debugShowCheckedModeBanner: false,

                        builder: (context, child) {
                            return ResponsiveBreakpoints.builder(
                                child: ScrollConfiguration(
                                    behavior: const _NoGlowScrollBehavior(),
                                    child: child!,
                                ),
                                breakpoints: [
                                    const Breakpoint(start: 0, end: 450, name: MOBILE),
                                    const Breakpoint(start: 451, end: 800, name: TABLET),
                                    const Breakpoint(start: 801, end: 1920, name: DESKTOP),
                                    const Breakpoint(start: 1921, end: double.infinity, name: '4K'),
                                ],
                            );
                        },

                        theme: ThemeData(
                            useMaterial3: true,
                            brightness: Brightness.dark,

                            colorScheme: ColorScheme.fromSeed(
                                seedColor: AppColors.primary,
                                brightness: Brightness.dark,
                                surface: AppColors.background,
                                onSurface: Colors.white,
                                primary: AppColors.primary,
                                secondary: AppColors.primaryLight,
                                surfaceContainerHighest: AppColors.surface,
                                onSurfaceVariant: AppColors.textSecondary,
                                outline: const Color(0xFF3A3A3A),
                                outlineVariant: AppColors.surfaceVariant,
                            ),

                            scaffoldBackgroundColor: AppColors.background,
                            appBarTheme: AppBarTheme(
                                backgroundColor: AppColors.background,
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

                            cardTheme: CardThemeData(
                                color: const Color(0xFF1A1625),
                                elevation: 0,
                                surfaceTintColor: const Color(0xFF8B5CF6),

                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.cardRadius),
                                    side: BorderSide(
                                        color: const Color(0xFF2A2A2A),
                                        width: 0.5,
                                    ),
                                ),
                            ),

                            filledButtonTheme: FilledButtonThemeData(
                                style: ButtonStyle(
                                    backgroundColor: WidgetStateProperty.resolveWith((states) {
                                        if (states.contains(WidgetState.disabled)) {
                                            return const Color(0xFF1A1625);
                                        }

                                        return const Color(0xFF8B5CF6);
                                    }),

                                    foregroundColor: WidgetStateProperty.resolveWith((states) {
                                        if (states.contains(WidgetState.disabled)) {
                                            return Colors.white54;
                                        }

                                        return Colors.white;
                                    }),

                                    side: WidgetStateProperty.all(
                                        const BorderSide(color: Color(0xFF2A2A2A), width: 0.5),
                                    ),

                                    shape: WidgetStateProperty.all(
                                        RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(AppConstants.buttonRadius),
                                        ),
                                    ),

                                    padding: WidgetStateProperty.all(
                                        const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                                    ),

                                    textStyle: WidgetStateProperty.all(
                                        const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            letterSpacing: 0.1,
                                        ),
                                    ),
                                ),
                            ),

                            elevatedButtonTheme: ElevatedButtonThemeData(
                                style: ElevatedButton.styleFrom(
                                    backgroundColor: const Color(0xFF8B5CF6),
                                    foregroundColor: Colors.white,
                                    disabledBackgroundColor: const Color(0xFF1A1625),
                                    disabledForegroundColor: Colors.white54,
                                    elevation: 0,
                                    shadowColor: Colors.transparent,
                                    surfaceTintColor: Colors.transparent,
                                    side: const BorderSide(color: Color(0xFF2A2A2A), width: 0.5),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),

                                    textStyle: const TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                        letterSpacing: 0.1,
                                    ),
                                ),
                            ),

                            outlinedButtonTheme: OutlinedButtonThemeData(
                                style: ButtonStyle(
                                    foregroundColor: WidgetStateProperty.resolveWith((states) {
                                        if (states.contains(WidgetState.disabled)) return Colors.white54;
                                        return const Color(0xFF8B5CF6);
                                    }),

                                    side: WidgetStateProperty.resolveWith((states) {
                                        if (states.contains(WidgetState.disabled)) return const BorderSide(color: Color(0xFF2A2A2A), width: 1);
                                        return const BorderSide(color: Color(0xFF8B5CF6), width: 1);
                                    }),

                                    shape: WidgetStateProperty.all(
                                        RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(24),
                                        ),
                                    ),

                                    padding: WidgetStateProperty.all(
                                        const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                                    ),

                                    textStyle: WidgetStateProperty.all(
                                        const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            letterSpacing: 0.1,
                                        ),
                                    ),
                                ),
                            ),

                            textButtonTheme: TextButtonThemeData(
                                style: TextButton.styleFrom(
                                    foregroundColor: const Color(0xFF8B5CF6),
                                    disabledForegroundColor: Colors.white54,
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppConstants.buttonRadius)),
                                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),

                                    textStyle: const TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w600,
                                        letterSpacing: 0.1,
                                    ),
                                ),
                            ),

                            inputDecorationTheme: InputDecorationTheme(
                                filled: true,
                                fillColor: const Color(0xFF1A1625),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),

                                border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.inputRadius),
                                    borderSide: const BorderSide(color: Color(0xFF2A2A2A), width: 1),
                                ),

                                enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.inputRadius),
                                    borderSide: const BorderSide(color: Color(0xFF2A2A2A), width: 1),
                                ),

                                focusedBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.inputRadius),
                                    borderSide: const BorderSide(color: Color(0xFF8B5CF6), width: 2),
                                ),

                                errorBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.inputRadius),
                                    borderSide: const BorderSide(color: Colors.red, width: 1),
                                ),

                                focusedErrorBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(AppConstants.inputRadius),
                                    borderSide: const BorderSide(color: Colors.red, width: 2),
                                ),

                                hintStyle: const TextStyle(color: Colors.white54),
                                labelStyle: const TextStyle(color: Colors.white70),
                                errorStyle: const TextStyle(color: Colors.red),
                            ),

                            bottomNavigationBarTheme: const BottomNavigationBarThemeData(
                                backgroundColor: Color(0xFF1A1625),
                                selectedItemColor: Color(0xFF8B5CF6),
                                unselectedItemColor: Colors.white54,
                                type: BottomNavigationBarType.fixed,
                                elevation: 0,
                            ),

                            navigationBarTheme: const NavigationBarThemeData(
                                backgroundColor: Color(0xFF1A1625),
                                indicatorColor: Color(0xFF8B5CF6),
                                surfaceTintColor: Colors.transparent,
                                elevation: 0,
                                height: 80,
                            ),

                            chipTheme: ChipThemeData(
                                backgroundColor: const Color(0xFF1A1625),
                                selectedColor: const Color(0xFF8B5CF6),
                                disabledColor: const Color(0xFF1A1625),
                                labelStyle: const TextStyle(color: Colors.white),
                                secondaryLabelStyle: const TextStyle(color: Colors.white54),
                                brightness: Brightness.dark,
                                elevation: 0,
                                shadowColor: Colors.transparent,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppConstants.chipRadius)),
                                side: const BorderSide(color: Color(0xFF8B5CF6), width: 1),
                            ),

                            listTileTheme: const ListTileThemeData(
                                tileColor: Color(0xFF1A1625),
                                selectedTileColor: Color(0xFF8B5CF6),
                                iconColor: Colors.white70,
                                textColor: Colors.white,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
                            ),

                            dividerTheme: const DividerThemeData(
                                color: Color(0xFF2A2A2A),
                                thickness: 1,
                                space: 1,
                            ),

                            floatingActionButtonTheme: const FloatingActionButtonThemeData(
                                backgroundColor: Color(0xFF8B5CF6),
                                foregroundColor: Colors.white,
                                elevation: 0,
                                focusElevation: 0,
                                hoverElevation: 0,
                                highlightElevation: 0,
                                shape: CircleBorder(),
                            ),

                            dialogTheme: const DialogThemeData(
                                backgroundColor: Color(0xFF1A1625),
                                surfaceTintColor: Colors.transparent,
                                elevation: 0,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(AppConstants.dialogRadius))),

                                titleTextStyle: TextStyle(
                                    color: Colors.white,
                                    fontSize: 20,
                                    fontWeight: FontWeight.w600,
                                ),

                                contentTextStyle: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 16,
                                ),
                            ),

                            snackBarTheme: SnackBarThemeData(
                                backgroundColor: const Color(0xFF1A1625),
                                contentTextStyle: const TextStyle(color: Colors.white),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppConstants.messageRadius)),
                                behavior: SnackBarBehavior.fixed,
                                elevation: 0,
                                actionTextColor: const Color(0xFF8B5CF6),
                            ),

                            switchTheme: SwitchThemeData(
                                thumbColor: WidgetStateProperty.resolveWith((states) {
                                    if (states.contains(WidgetState.selected)) return Colors.white;
                                    return Colors.white54;
                                }),

                                trackColor: WidgetStateProperty.resolveWith((states) {
                                    if (states.contains(WidgetState.selected)) return const Color(0xFF8B5CF6);
                                    return const Color(0xFF2A2A2A);
                                }),
                            ),

                            checkboxTheme: CheckboxThemeData(
                                fillColor: WidgetStateProperty.resolveWith((states) {
                                    if (states.contains(WidgetState.selected)) return const Color(0xFF8B5CF6);
                                    return Colors.transparent;
                                }),

                                checkColor: WidgetStateProperty.all(Colors.white),
                                side: const BorderSide(color: Color(0xFF2A2A2A), width: 2),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                            ),

                            radioTheme: RadioThemeData(
                                fillColor: WidgetStateProperty.resolveWith((states) {
                                    if (states.contains(WidgetState.selected)) return const Color(0xFF8B5CF6);
                                    return const Color(0xFF2A2A2A);
                                }),
                            ),

                            progressIndicatorTheme: const ProgressIndicatorThemeData(
                                color: Color(0xFF8B5CF6),
                                linearTrackColor: Color(0xFF2A2A2A),
                                circularTrackColor: Color(0xFF2A2A2A),
                            ),
                        ),

                        home: const AuthWrapper(),
                    );
                },
            ),
        );
    }
}

class AuthWrapper extends StatefulWidget {
    const AuthWrapper({super.key});

    @override
    State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
    bool _configLoaded = false;

    @override
    void initState() {
        super.initState();

        WidgetsBinding.instance.addPostFrameCallback((_) async {
            await context.read<AuthService>().initialize();

            if (mounted) {
                final playlistProvider = context.read<PlaylistProvider>();
                await playlistProvider.loadConfigBlocking();
                
                if (mounted) {
                    setState(() {
                        _configLoaded = true;
                    });
                }
            }
        });
    }

    @override
    Widget build(BuildContext context) {
        return Consumer<AuthService>(
            builder: (context, authService, child) {
                if (authService.isLoading || !_configLoaded) {
                    return const Scaffold(
                        backgroundColor: Color(0xFF0F0A1A),
                        body: Center(
                            child: CircularProgressIndicator(color: Color(0xFF8B5CF6)),
                        ),
                    );
                }

                if (authService.isAuthenticated) {
                    return const HomeScreen();
                }

                else {
                    return const LoginScreen();
                }
            },
        );
    }
}

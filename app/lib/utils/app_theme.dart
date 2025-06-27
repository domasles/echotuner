import 'package:flutter/material.dart';
import '../config/app_colors.dart';

class AppTheme {
    static const double borderRadius = 16.0;
    static const double borderRadiusSmall = 12.0;
    static const double borderRadiusLarge = 24.0;
    static const double borderRadiusXLarge = 28.0;
    
    static const double spacing = 16.0;
    static const double spacingSmall = 8.0;
    static const double spacingLarge = 24.0;
    static const double spacingXLarge = 32.0;
    
    static const double elevationNone = 0.0;
    static const double elevationLow = 2.0;
    static const double elevationMedium = 4.0;
    static const double elevationHigh = 8.0;

    static BorderSide get defaultBorder => const BorderSide(
            color: AppColors.surfaceVariant,
            width: 0.5,
        );
    
    static BorderSide get primaryBorder => const BorderSide(
            color: AppColors.primary,
            width: 1.0,
        );
    
    static BorderSide get errorBorder => const BorderSide(
            color: AppColors.error,
            width: 1.0,
        );

    static BoxDecoration get surfaceDecoration => BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.fromBorderSide(defaultBorder),
        );
    
    static BoxDecoration get primaryDecoration => BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(borderRadius),
        );

    static const TextStyle headingStyle = TextStyle(
        color: AppColors.textPrimary,
        fontSize: 28,
        fontWeight: FontWeight.w600,
    );
    
    static const TextStyle subheadingStyle = TextStyle(
        color: AppColors.textSecondary,
        fontSize: 16,
        fontWeight: FontWeight.w500,
    );
    
    static const TextStyle bodyStyle = TextStyle(
        color: AppColors.textPrimary,
        fontSize: 16,
    );
    
    static const TextStyle captionStyle = TextStyle(
        color: AppColors.textTertiary,
        fontSize: 12,
    );

    static ButtonStyle get primaryButtonStyle => ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: AppColors.textPrimary,
            elevation: elevationNone,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadiusLarge)),
            padding: const EdgeInsets.symmetric(
            horizontal: spacingLarge,
            vertical: spacing,
            ),
        );
    
    static ButtonStyle get spotifyButtonStyle => ElevatedButton.styleFrom(
            backgroundColor: AppColors.spotify,
            foregroundColor: AppColors.textPrimary,
            elevation: elevationNone,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(borderRadius)),
            side: defaultBorder,
        );
    
    static Widget get loadingIndicator => const CircularProgressIndicator(
            color: AppColors.primary,
            strokeWidth: 2.5,
        );
    
    static Color getProgressColor(double progress) {
        if (progress <= 0.5) return AppColors.progressGreen;
        if (progress <= 0.8) return AppColors.progressOrange;

        return AppColors.progressRed;
    }
}

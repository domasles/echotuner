import 'package:flutter/material.dart';

/// Responsive layout utility class for handling different screen sizes
class ResponsiveLayout {
  static const double mobileBreakpoint = 600;
  static const double tabletBreakpoint = 1024;
  static const double desktopBreakpoint = 1440;

  /// Get the current device type based on screen width
  static DeviceType getDeviceType(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    
    if (width < mobileBreakpoint) {
      return DeviceType.mobile;
    } else if (width < tabletBreakpoint) {
      return DeviceType.tablet;
    } else {
      return DeviceType.desktop;
    }
  }

  /// Get responsive padding based on device type
  static EdgeInsets getResponsivePadding(BuildContext context) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.mobile:
        return const EdgeInsets.all(16.0);
      case DeviceType.tablet:
        return const EdgeInsets.all(24.0);
      case DeviceType.desktop:
        return const EdgeInsets.all(32.0);
    }
  }

  /// Get responsive content width with maximum constraints
  static double getContentWidth(BuildContext context, {double maxWidth = 1200}) {
    final screenWidth = MediaQuery.of(context).size.width;
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.mobile:
        return screenWidth - 32; // Account for padding
      case DeviceType.tablet:
        return (screenWidth * 0.85).clamp(0, maxWidth);
      case DeviceType.desktop:
        return (screenWidth * 0.75).clamp(0, maxWidth);
    }
  }

  /// Get responsive spacing based on device type
  static double getResponsiveSpacing(BuildContext context, SpacingSize size) {
    final deviceType = getDeviceType(context);
    final scale = deviceType == DeviceType.mobile ? 1.0 : 
                  deviceType == DeviceType.tablet ? 1.2 : 1.4;
    
    switch (size) {
      case SpacingSize.small:
        return 8.0 * scale;
      case SpacingSize.medium:
        return 16.0 * scale;
      case SpacingSize.large:
        return 24.0 * scale;
      case SpacingSize.extraLarge:
        return 32.0 * scale;
    }
  }

  /// Get responsive font size based on device type
  static double getResponsiveFontSize(BuildContext context, FontSizeType type) {
    final deviceType = getDeviceType(context);
    final scale = deviceType == DeviceType.mobile ? 1.0 : 
                  deviceType == DeviceType.tablet ? 1.1 : 1.2;
    
    switch (type) {
      case FontSizeType.small:
        return 12.0 * scale;
      case FontSizeType.medium:
        return 14.0 * scale;
      case FontSizeType.large:
        return 16.0 * scale;
      case FontSizeType.extraLarge:
        return 18.0 * scale;
      case FontSizeType.title:
        return 20.0 * scale;
      case FontSizeType.heading:
        return 24.0 * scale;
    }
  }

  /// Get responsive icon size based on device type
  static double getResponsiveIconSize(BuildContext context, IconSizeType type) {
    final deviceType = getDeviceType(context);
    final scale = deviceType == DeviceType.mobile ? 1.0 : 
                  deviceType == DeviceType.tablet ? 1.1 : 1.2;
    
    switch (type) {
      case IconSizeType.small:
        return 16.0 * scale;
      case IconSizeType.medium:
        return 20.0 * scale;
      case IconSizeType.large:
        return 24.0 * scale;
      case IconSizeType.extraLarge:
        return 28.0 * scale;
    }
  }

  /// Get responsive grid column count
  static int getGridColumnCount(BuildContext context, {int maxColumns = 4}) {
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.mobile:
        return (maxColumns / 2).ceil().clamp(1, 2);
      case DeviceType.tablet:
        return (maxColumns * 0.75).ceil().clamp(2, maxColumns);
      case DeviceType.desktop:
        return maxColumns;
    }
  }

  /// Get responsive dialog width
  static double getDialogWidth(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final deviceType = getDeviceType(context);
    
    switch (deviceType) {
      case DeviceType.mobile:
        return screenWidth * 0.9;
      case DeviceType.tablet:
        return (screenWidth * 0.7).clamp(400, 600);
      case DeviceType.desktop:
        return (screenWidth * 0.5).clamp(500, 800);
    }
  }

  /// Check if the device is considered compact (mobile/small tablet)
  static bool isCompact(BuildContext context) {
    return getDeviceType(context) == DeviceType.mobile;
  }

  /// Check if the device has enough space for side-by-side layout
  static bool canShowSideBySide(BuildContext context) {
    return getDeviceType(context) != DeviceType.mobile;
  }
}

/// Widget that builds different layouts based on device type
class ResponsiveBuilder extends StatelessWidget {
  final Widget Function(BuildContext context, DeviceType deviceType) builder;

  const ResponsiveBuilder({
    super.key,
    required this.builder,
  });

  @override
  Widget build(BuildContext context) {
    final deviceType = ResponsiveLayout.getDeviceType(context);
    return builder(context, deviceType);
  }
}

/// Device type enumeration
enum DeviceType {
  mobile,
  tablet,
  desktop,
}

/// Spacing size enumeration
enum SpacingSize {
  small,
  medium,
  large,
  extraLarge,
}

/// Font size type enumeration
enum FontSizeType {
  small,
  medium,
  large,
  extraLarge,
  title,
  heading,
}

/// Icon size type enumeration
enum IconSizeType {
  small,
  medium,
  large,
  extraLarge,
}

import 'package:flutter/material.dart';

import '../../config/app_constants.dart';

class ReusableCard extends StatelessWidget {
    final Widget child;

    final EdgeInsetsGeometry? padding;
    final EdgeInsetsGeometry? margin;

    final Color? backgroundColor;
    final double? elevation;

    const ReusableCard({
        super.key,

        required this.child,

        this.padding,
        this.margin,
        this.backgroundColor,
        this.elevation,
    });

    @override
    Widget build(BuildContext context) {
        return Card(
            margin: margin,
            elevation: elevation,
            color: backgroundColor,

            child: Padding(
                padding: padding ?? const EdgeInsets.all(AppConstants.mediumPadding),
                child: child,
            ),
        );
    }
}

class SectionHeader extends StatelessWidget {
    final String title;
    final String subtitle;

    const SectionHeader({
        super.key,
        required this.title,
        required this.subtitle,
    });

    @override
    Widget build(BuildContext context) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                    ),
                ),

                const SizedBox(height: AppConstants.smallSpacing),
                Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                    ),
                ),
            ],
        );
    }
}

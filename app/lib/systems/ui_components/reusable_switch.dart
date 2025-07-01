import 'package:flutter/material.dart';

import '../../config/app_constants.dart';

class ReusableSwitch extends StatelessWidget {
    final String title;
    final String? subtitle;

    final bool value;

    final ValueChanged<bool> onChanged;
    final IconData? icon;

    const ReusableSwitch({
        super.key,

        required this.title,

        this.subtitle,

        required this.value,
        required this.onChanged,

        this.icon,
    });

    @override
    Widget build(BuildContext context) {
        return Card(
            child: Padding(
                padding: const EdgeInsets.all(AppConstants.mediumPadding),
                child: Row(
                    children: [
                        if (icon != null) ...[
                            Icon(icon),
                            const SizedBox(width: AppConstants.mediumSpacing),
                        ],

                        Expanded(
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    Text(
                                        title,
                                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                            fontWeight: FontWeight.bold,
                                        ),
                                    ),

                                    if (subtitle != null) ...[
                                        const SizedBox(height: AppConstants.smallSpacing),
                                        Text(
                                            subtitle!,
                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                                color: Colors.white70,
                                            ),
                                        ),
                                    ],
                                ],
                            ),
                        ),

                        Switch(
                            value: value,
                            onChanged: onChanged,
                        ),
                    ],
                ),
            ),
        );
    }
}

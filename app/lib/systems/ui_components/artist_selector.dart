import 'package:flutter/material.dart';

import '../../config/app_constants.dart';

class ArtistSelector extends StatelessWidget {
    final List<String> selectedArtists;
    final int maxArtists;

    final String label;
    final bool isDisliked;

    final Function(String) onRemove;

    final VoidCallback onAdd;

    const ArtistSelector({
        super.key,

        required this.selectedArtists,
        required this.maxArtists,
        required this.label,
        required this.onRemove,
        required this.onAdd,

        this.isDisliked = false,
    });

    @override
    Widget build(BuildContext context) {
        return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                const SizedBox(height: AppConstants.smallSpacing),
                if (selectedArtists.isNotEmpty) ...[
                    Wrap(
                        spacing: AppConstants.smallSpacing,
                        runSpacing: AppConstants.smallSpacing,

                        children: selectedArtists.map((artist) {
                            return Chip(
                                label: Text(artist),
                                onDeleted: () => onRemove(artist),
                                deleteIcon: const Icon(Icons.close_rounded, size: AppConstants.smallIconSize),
                                backgroundColor: isDisliked ? Colors.red.withValues(alpha: 0.1) : const Color(0xFF8B5CF6),

                                labelStyle: TextStyle(
                                    color: isDisliked ? Colors.red : Colors.white,
                                    fontWeight: FontWeight.w500,
                                ),

                                deleteIconColor: isDisliked ? Colors.red : Colors.white,
                                elevation: isDisliked ? 1 : 2,
                                shadowColor: isDisliked ? Colors.red.withValues(alpha: 0.2) : Colors.black26,

                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(20),
                                    side: isDisliked ? BorderSide(color: Colors.red.withValues(alpha: 0.3), width: 1) : BorderSide.none,
                                ),

                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            );
                        }).toList(),
                    ),

                    const SizedBox(height: AppConstants.smallSpacing),
                ],

                OutlinedButton.icon(
                    onPressed: selectedArtists.length < maxArtists ? onAdd : null,
                    icon: const Icon(Icons.add_rounded),
                    label: Text(isDisliked ? 'Add Disliked Artist' : 'Add Custom Artist'),

                    style: OutlinedButton.styleFrom(
                        foregroundColor: isDisliked ? Colors.red : null,
                        side: BorderSide(color: isDisliked ? Colors.red : Colors.grey),

                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppConstants.buttonRadius),
                        ),
                    ),
                ),
            ],
        );
    }
}

import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../config/app_theme.dart';

class StampBadge extends StatelessWidget {
  final String category;
  final bool isAnomaly;
  final String status; // 'AI-assigned' | 'user-corrected'
  final bool compact;

  const StampBadge({
    Key? key,
    required this.category,
    this.isAnomaly = false,
    this.status = 'AI-assigned',
    this.compact = false,
  }) : super(key: key);

  Color _getCategoryColor() {
    if (isAnomaly) return AppColors.danger;
    switch (category.toLowerCase()) {
      case 'salary':
      case 'income':
        return AppColors.success;
      case 'investment':
        return const Color(0xFF14B8A6);
      case 'housing':
        return AppColors.primary;
      case 'food':
        return AppColors.warning;
      case 'utilities':
        return const Color(0xFFF97316);
      case 'transport':
        return const Color(0xFF06B6D4);
      case 'shopping':
        return const Color(0xFFA855F7);
      case 'entertainment':
        return const Color(0xFFEC4899);
      default:
        return AppColors.textMuted;
    }
  }

  IconData _getCategoryIcon() {
    if (isAnomaly) return Icons.warning_amber_rounded;
    switch (category.toLowerCase()) {
      case 'salary':
      case 'income':
        return Icons.work_outline;
      case 'investment':
        return Icons.trending_up;
      case 'housing':
        return Icons.home_outlined;
      case 'food':
        return Icons.restaurant_outlined;
      case 'utilities':
        return Icons.bolt_outlined;
      case 'transport':
        return Icons.directions_car_outlined;
      case 'shopping':
        return Icons.shopping_bag_outlined;
      case 'entertainment':
        return Icons.movie_outlined;
      default:
        return Icons.local_offer_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getCategoryColor();

    if (compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.withOpacity(0.3), width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(_getCategoryIcon(), size: 12, color: color),
            const SizedBox(width: 4),
            Text(
              category,
              style: TextStyle(
                color: color,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      );
    }

    // Indian Banking Stamp style
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withOpacity(0.35), width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(_getCategoryIcon(), size: 13, color: color),
              const SizedBox(width: 5),
              Text(
                category,
                style: TextStyle(
                  color: color,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
        if (isAnomaly) ...[
          const SizedBox(width: 6),
          Transform.rotate(
            angle: -3 * math.pi / 180,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.danger.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: AppColors.danger, width: 1.2),
              ),
              child: const Text(
                'FLAGGED',
                style: TextStyle(
                  color: AppColors.danger,
                  fontSize: 9,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.8,
                ),
              ),
            ),
          ),
        ] else if (status == 'user-corrected') ...[
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.06),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.white24, width: 0.8),
            ),
            child: const Text(
              'CORRECTED',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 9,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/fin_theme.dart';

enum StampType { gold, coral, sage, neutral }

class StampBadge extends StatelessWidget {
  final String text;
  final StampType type;
  final IconData? icon;

  const StampBadge({
    super.key,
    required this.text,
    this.type = StampType.gold,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    Color borderColor;
    Color textColor;
    Color bgColor;

    switch (type) {
      case StampType.coral:
        borderColor = (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.5);
        textColor = isDark ? FinColors.darkCoral : FinColors.lightCoral;
        bgColor = (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.08);
        break;
      case StampType.sage:
        borderColor = (isDark ? FinColors.darkSage : FinColors.lightSage).withOpacity(0.5);
        textColor = isDark ? FinColors.darkSage : FinColors.lightSage;
        bgColor = (isDark ? FinColors.darkSage : FinColors.lightSage).withOpacity(0.08);
        break;
      case StampType.neutral:
        borderColor = (isDark ? FinColors.darkMist : FinColors.lightMist).withOpacity(0.3);
        textColor = isDark ? FinColors.darkMist : FinColors.lightMist;
        bgColor = Colors.transparent;
        break;
      case StampType.gold:
      default:
        borderColor = (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.4);
        textColor = isDark ? FinColors.darkGold : FinColors.lightGold;
        bgColor = (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.05);
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: borderColor, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 10, color: textColor),
            const SizedBox(width: 4),
          ],
          Text(
            text.toUpperCase(),
            style: GoogleFonts.ibmPlexMono(
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
              color: textColor,
            ),
          ),
        ],
      ),
    );
  }
}

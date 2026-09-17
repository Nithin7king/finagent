import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FinColors {
  // Dark Palette
  static const Color darkInk = Color(0xFF0B1220);
  static const Color darkInkRaised = Color(0xFF121B2E);
  static const Color darkPaper = Color(0xFFF4F0E6);
  static const Color darkGold = Color(0xFFC9A24B);
  static const Color darkSage = Color(0xFF5FAE7C);
  static const Color darkCoral = Color(0xFFE15B4F);
  static const Color darkMist = Color(0xFF8A93A6);

  // Light Palette
  static const Color lightInk = Color(0xFFFAF8F2);
  static const Color lightInkRaised = Color(0xFFFFFFFF);
  static const Color lightPaper = Color(0xFFEFE9D3);
  static const Color lightGold = Color(0xFFAC7A1A);
  static const Color lightSage = Color(0xFF2C7849);
  static const Color lightCoral = Color(0xFFCD3527);
  static const Color lightMist = Color(0xFF53627A);
  static const Color lightInkText = Color(0xFF101826);
}

class FinTheme {
  static ThemeData darkTheme() {
    final baseTextTheme = ThemeData.dark().textTheme;
    final textTheme = GoogleFonts.interTextTheme(baseTextTheme).copyWith(
      displayLarge: GoogleFonts.fraunces(
        fontSize: 32,
        fontWeight: FontWeight.bold,
        color: Colors.white,
        letterSpacing: -0.5,
      ),
      displayMedium: GoogleFonts.fraunces(
        fontSize: 26,
        fontWeight: FontWeight.w600,
        color: Colors.white,
        fontStyle: FontStyle.italic,
      ),
      titleLarge: GoogleFonts.fraunces(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: Colors.white,
      ),
      titleMedium: GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: Colors.white,
      ),
      bodyLarge: GoogleFonts.inter(
        fontSize: 14,
        color: Colors.white.withOpacity(0.9),
      ),
      bodyMedium: GoogleFonts.inter(
        fontSize: 13,
        color: FinColors.darkMist,
      ),
      labelLarge: GoogleFonts.ibmPlexMono(
        fontSize: 12,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
      ),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: FinColors.darkInk,
      colorScheme: const ColorScheme.dark(
        primary: FinColors.darkGold,
        secondary: FinColors.darkSage,
        error: FinColors.darkCoral,
        surface: FinColors.darkInkRaised,
        onSurface: Colors.white,
        background: FinColors.darkInk,
      ),
      cardTheme: CardTheme(
        color: FinColors.darkInkRaised,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(4),
          side: BorderSide(color: FinColors.darkGold.withOpacity(0.15)),
        ),
      ),
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: FinColors.darkInk,
        elevation: 0,
        titleTextStyle: GoogleFonts.fraunces(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
      dividerColor: FinColors.darkGold.withOpacity(0.12),
    );
  }

  static ThemeData lightTheme() {
    final baseTextTheme = ThemeData.light().textTheme;
    final textTheme = GoogleFonts.interTextTheme(baseTextTheme).copyWith(
      displayLarge: GoogleFonts.fraunces(
        fontSize: 32,
        fontWeight: FontWeight.bold,
        color: FinColors.lightInkText,
        letterSpacing: -0.5,
      ),
      displayMedium: GoogleFonts.fraunces(
        fontSize: 26,
        fontWeight: FontWeight.w600,
        color: FinColors.lightInkText,
        fontStyle: FontStyle.italic,
      ),
      titleLarge: GoogleFonts.fraunces(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: FinColors.lightInkText,
      ),
      titleMedium: GoogleFonts.inter(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: FinColors.lightInkText,
      ),
      bodyLarge: GoogleFonts.inter(
        fontSize: 14,
        color: FinColors.lightInkText,
      ),
      bodyMedium: GoogleFonts.inter(
        fontSize: 13,
        color: FinColors.lightMist,
      ),
      labelLarge: GoogleFonts.ibmPlexMono(
        fontSize: 12,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
      ),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: FinColors.lightInk,
      colorScheme: const ColorScheme.light(
        primary: FinColors.lightGold,
        secondary: FinColors.lightSage,
        error: FinColors.lightCoral,
        surface: FinColors.lightInkRaised,
        onSurface: FinColors.lightInkText,
        background: FinColors.lightInk,
      ),
      cardTheme: CardTheme(
        color: FinColors.lightInkRaised,
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(4),
          side: BorderSide(color: FinColors.lightGold.withOpacity(0.2)),
        ),
      ),
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: FinColors.lightInk,
        elevation: 0,
        titleTextStyle: GoogleFonts.fraunces(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: FinColors.lightInkText,
        ),
      ),
      dividerColor: FinColors.lightGold.withOpacity(0.18),
    );
  }
}

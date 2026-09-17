import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'providers/fin_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/ledger_screen.dart';
import 'screens/analytics_screen.dart';
import 'screens/goals_screen.dart';
import 'screens/chat_screen.dart';
import 'theme/fin_theme.dart';
import 'widgets/passbook_app_bar.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ChangeNotifierProvider(
      create: (_) => FinProvider()..init(),
      child: const FinAgentApp(),
    ),
  );
}

class FinAgentApp extends StatelessWidget {
  const FinAgentApp({super.key});

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();

    return MaterialApp(
      title: 'MYFY.AI — Autonomous Personal Ledger',
      debugShowCheckedModeBanner: false,
      theme: FinTheme.lightTheme(),
      darkTheme: FinTheme.darkTheme(),
      themeMode: fin.themeMode,
      home: const MainGatekeeper(),
    );
  }
}

class MainGatekeeper extends StatelessWidget {
  const MainGatekeeper({super.key});

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Loading skeleton
    if (fin.isLoading) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.4),
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text('💎', style: TextStyle(fontSize: 32)),
              ),
              const SizedBox(height: 16),
              Text(
                'INITIALIZING LEDGER',
                style: GoogleFonts.ibmPlexMono(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                  color: isDark ? FinColors.darkGold : FinColors.lightGold,
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: 140,
                child: LinearProgressIndicator(
                  backgroundColor: Colors.white10,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    isDark ? FinColors.darkGold : FinColors.lightGold,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Auth Wall
    if (fin.user == null) {
      return const AuthScreen();
    }

    // Main App Shell
    final isMobile = MediaQuery.of(context).size.width < 700;

    final screens = const [
      DashboardScreen(),
      LedgerScreen(),
      AnalyticsScreen(),
      GoalsScreen(),
      ChatScreen(),
    ];

    return Scaffold(
      appBar: const PassbookAppBar(),
      body: screens[fin.currentNavIndex],
      bottomNavigationBar: isMobile
          ? BottomNavigationBar(
              currentIndex: fin.currentNavIndex,
              onTap: (idx) => fin.setNavIndex(idx),
              type: BottomNavigationBarType.fixed,
              backgroundColor: isDark ? FinColors.darkInk : FinColors.lightInk,
              selectedItemColor: isDark ? FinColors.darkGold : FinColors.lightGold,
              unselectedItemColor: isDark ? FinColors.darkMist : FinColors.lightMist,
              selectedLabelStyle: GoogleFonts.ibmPlexMono(fontSize: 9, fontWeight: FontWeight.bold),
              unselectedLabelStyle: GoogleFonts.inter(fontSize: 9),
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.dashboard_outlined),
                  activeIcon: Icon(Icons.dashboard),
                  label: 'Dashboard',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.receipt_long_outlined),
                  activeIcon: Icon(Icons.receipt_long),
                  label: 'Ledger',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.trending_up_outlined),
                  activeIcon: Icon(Icons.trending_up),
                  label: 'Analytics',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.track_changes_outlined),
                  activeIcon: Icon(Icons.track_changes),
                  label: 'Goals',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.chat_bubble_outline),
                  activeIcon: Icon(Icons.chat_bubble),
                  label: 'AI Agent',
                ),
              ],
            )
          : null,
    );
  }
}

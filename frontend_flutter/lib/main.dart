import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/app_theme.dart';
import 'providers/fin_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/main_navigation_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyFyApp());
}

class MyFyApp extends StatelessWidget {
  const MyFyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => FinProvider()),
      ],
      child: MaterialApp(
        title: 'MYFY.AI',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const AppRoot(),
      ),
    );
  }
}

class AppRoot extends StatelessWidget {
  const AppRoot({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();

    if (!fin.isInitialized) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.secondary],
                  ),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.account_balance_wallet, size: 48, color: Colors.white),
              ),
              const SizedBox(height: 24),
              const Text(
                'MYFY.AI',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, letterSpacing: -0.5),
              ),
              const SizedBox(height: 20),
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
              ),
            ],
          ),
        ),
      );
    }

    if (fin.isAuthenticated) {
      return const MainNavigationScreen();
    }

    return const AuthScreen();
  }
}

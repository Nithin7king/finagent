import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/fin_provider.dart';
import '../theme/fin_theme.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;

  final _emailCtrl = TextEditingController(text: 'demo@finagent.ai');
  final _passwordCtrl = TextEditingController(text: 'Demo@123');
  final _nameCtrl = TextEditingController(text: 'Arjun Sharma');
  final _incomeCtrl = TextEditingController(text: '85000');

  String? errorMessage;
  bool isSubmitting = false;

  void handleSubmit() async {
    setState(() {
      errorMessage = null;
      isSubmitting = true;
    });

    final fin = context.read<FinProvider>();
    bool ok = false;

    if (isLogin) {
      ok = await fin.login(_emailCtrl.text.trim(), _passwordCtrl.text);
      if (!ok) {
        setState(() {
          errorMessage = 'Invalid email or password. Try Demo credentials.';
        });
      }
    } else {
      final income = double.tryParse(_incomeCtrl.text) ?? 0.0;
      ok = await fin.register(
        name: _nameCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        password: _passwordCtrl.text,
        monthlyIncome: income,
      );
      if (!ok) {
        setState(() {
          errorMessage = 'Registration failed. Email might already exist.';
        });
      }
    }

    if (mounted) {
      setState(() {
        isSubmitting = false;
      });
    }
  }

  void fillDemo() {
    setState(() {
      isLogin = true;
      _emailCtrl.text = 'demo@finagent.ai';
      _passwordCtrl.text = 'Demo@123';
      errorMessage = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Container(
            constraints: const BoxConstraints(maxWidth: 440),
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.25),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.25),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.4),
                      ),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Text('💎', style: TextStyle(fontSize: 28)),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'MYFY.AI',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.fraunces(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : FinColors.lightInkText,
                  ),
                ),
                Text(
                  'AUTONOMOUS PERSONAL FINANCE LEDGER',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.ibmPlexMono(
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.5,
                    color: isDark ? FinColors.darkGold : FinColors.lightGold,
                  ),
                ),
                const SizedBox(height: 24),

                // Toggle tabs
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () => setState(() => isLogin = true),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(
                                color: isLogin
                                    ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                    : Colors.transparent,
                                width: 2,
                              ),
                            ),
                          ),
                          child: Text(
                            'SIGN IN',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: isLogin
                                  ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                  : (isDark ? FinColors.darkMist : FinColors.lightMist),
                            ),
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: InkWell(
                        onTap: () => setState(() => isLogin = false),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          decoration: BoxDecoration(
                            border: Border(
                              bottom: BorderSide(
                                color: !isLogin
                                    ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                    : Colors.transparent,
                                width: 2,
                              ),
                            ),
                          ),
                          child: Text(
                            'CREATE ACCOUNT',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: !isLogin
                                  ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                  : (isDark ? FinColors.darkMist : FinColors.lightMist),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                if (!isLogin) ...[
                  TextField(
                    controller: _nameCtrl,
                    decoration: InputDecoration(
                      labelText: 'Full Name',
                      labelStyle: GoogleFonts.inter(fontSize: 12),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                      prefixIcon: const Icon(Icons.person_outline, size: 18),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                TextField(
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    labelText: 'Email Address',
                    labelStyle: GoogleFonts.inter(fontSize: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                    prefixIcon: const Icon(Icons.email_outlined, size: 18),
                  ),
                ),
                const SizedBox(height: 16),

                TextField(
                  controller: _passwordCtrl,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    labelStyle: GoogleFonts.inter(fontSize: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                    prefixIcon: const Icon(Icons.lock_outline, size: 18),
                  ),
                ),
                const SizedBox(height: 16),

                if (!isLogin) ...[
                  TextField(
                    controller: _incomeCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Monthly Income (₹)',
                      labelStyle: GoogleFonts.inter(fontSize: 12),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                      prefixIcon: const Icon(Icons.currency_rupee, size: 18),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                if (errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.1),
                      border: Border.all(
                        color: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.3),
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      errorMessage!,
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Submit button
                ElevatedButton(
                  onPressed: isSubmitting ? null : handleSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                  ),
                  child: isSubmitting
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                        )
                      : Text(
                          isLogin ? 'ACCESS LEDGER' : 'REGISTER PROFILE',
                          style: GoogleFonts.ibmPlexMono(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                        ),
                ),
                const SizedBox(height: 16),

                // Quick Demo button
                OutlinedButton.icon(
                  onPressed: fillDemo,
                  icon: const Icon(Icons.bolt, size: 16),
                  label: Text(
                    'USE DEMO CREDENTIALS',
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                    side: BorderSide(
                      color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

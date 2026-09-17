import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/fin_provider.dart';
import '../theme/fin_theme.dart';

class PassbookAppBar extends StatelessWidget implements PreferredSizeWidget {
  const PassbookAppBar({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(64);

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final navItems = [
      {'label': 'Dashboard', 'icon': Icons.dashboard_outlined},
      {'label': 'Ledger', 'icon': Icons.receipt_long_outlined},
      {'label': 'Analytics', 'icon': Icons.trending_up_outlined},
      {'label': 'Goals', 'icon': Icons.track_changes_outlined},
      {'label': 'AI Assistant', 'icon': Icons.chat_bubble_outline},
    ];

    return Container(
      height: preferredSize.height,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
        color: isDark ? FinColors.darkInk : FinColors.lightInk,
        border: Border(
          bottom: BorderSide(
            color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.15),
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Brand logo
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                  ),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text('💎', style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(width: 10),
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'MYFY.AI',
                    style: GoogleFonts.fraunces(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.5,
                      color: isDark ? Colors.white : FinColors.lightInkText,
                    ),
                  ),
                  Text(
                    'AUTONOMOUS PERSONAL LEDGER',
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 8,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                      color: isDark ? FinColors.darkGold : FinColors.lightGold,
                    ),
                  ),
                ],
              ),
            ],
          ),

          // Desktop/Web Center Nav Tabs
          if (MediaQuery.of(context).size.width > 700)
            Row(
              children: navItems.asMap().entries.map((entry) {
                final idx = entry.key;
                final item = entry.value;
                final isSelected = fin.currentNavIndex == idx;

                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: InkWell(
                    onTap: () => fin.setNavIndex(idx),
                    borderRadius: BorderRadius.circular(4),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.12)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(4),
                        border: isSelected
                            ? Border.all(
                                color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.35),
                              )
                            : null,
                      ),
                      child: Row(
                        children: [
                          Icon(
                            item['icon'] as IconData,
                            size: 14,
                            color: isSelected
                                ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                : (isDark ? FinColors.darkMist : FinColors.lightMist),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            item['label'] as String,
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                              color: isSelected
                                  ? (isDark ? FinColors.darkGold : FinColors.lightGold)
                                  : (isDark ? FinColors.darkMist : FinColors.lightMist),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),

          // Right Controls: Theme Toggle + User Info + Logout
          Row(
            children: [
              IconButton(
                icon: Icon(
                  fin.isDarkMode ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                  size: 18,
                  color: isDark ? FinColors.darkGold : FinColors.lightGold,
                ),
                tooltip: 'Toggle Theme',
                onPressed: () => fin.toggleTheme(),
              ),
              if (fin.user != null) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.08),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.2),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.account_circle_outlined, size: 14),
                      const SizedBox(width: 6),
                      Text(
                        fin.user!.name.split(' ').first,
                        style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.logout_outlined, size: 18),
                  tooltip: 'Logout',
                  onPressed: () => fin.logout(),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

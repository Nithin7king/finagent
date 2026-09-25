import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';
import 'kyc_dialog.dart';

class PassbookAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool showKycStatus;

  const PassbookAppBar({
    Key? key,
    this.title = 'MYFY.AI',
    this.showKycStatus = true,
  }) : super(key: key);

  @override
  Size get preferredSize => const Size.fromHeight(60);

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final user = fin.user;
    final kycData = fin.kycData;
    final isVerified = kycData?.kycStatus == 'verified';

    return AppBar(
      backgroundColor: AppColors.background,
      elevation: 0,
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(7),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppColors.primary, AppColors.secondary],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.account_balance_wallet, size: 18, color: Colors.white),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.5,
                color: AppColors.textPrimary,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
      actions: [
        if (showKycStatus) ...[
          Center(
            child: InkWell(
              onTap: () {
                showDialog(
                  context: context,
                  builder: (ctx) => const KycDialog(),
                );
              },
              borderRadius: BorderRadius.circular(20),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: isVerified ? AppColors.success.withOpacity(0.15) : AppColors.warning.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isVerified ? AppColors.success.withOpacity(0.4) : AppColors.warning.withOpacity(0.4),
                    width: 1,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isVerified ? Icons.verified : Icons.shield_outlined,
                      size: 13,
                      color: isVerified ? AppColors.success : AppColors.warning,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      isVerified ? 'KYC Verified' : 'Complete KYC',
                      style: TextStyle(
                        color: isVerified ? AppColors.success : AppColors.warning,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
        ],
        // User Profile Initials Avatar
        Padding(
          padding: const EdgeInsets.only(right: 16),
          child: Center(
            child: InkWell(
              onTap: () {
                _showProfileSheet(context, fin);
              },
              borderRadius: BorderRadius.circular(20),
              child: CircleAvatar(
                radius: 17,
                backgroundColor: AppColors.cardSurfaceRaised,
                child: Text(
                  user?.name.isNotEmpty == true ? user!.name[0].toUpperCase() : 'U',
                  style: const TextStyle(
                    color: AppColors.primary,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showProfileSheet(BuildContext context, FinProvider fin) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.cardSurfaceRaised,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        final user = fin.user;
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 26,
                    backgroundColor: AppColors.primary.withOpacity(0.2),
                    child: Text(
                      user?.name.isNotEmpty == true ? user!.name[0].toUpperCase() : 'U',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.name ?? 'User Profile',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        Text(
                          user?.email ?? '',
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const Divider(color: AppColors.border, height: 32),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.verified_user_outlined, color: AppColors.primary),
                title: const Text('Identity & KYC Status'),
                subtitle: Text(
                  fin.kycData?.kycStatus == 'verified' ? 'Fully verified via DigiLocker' : 'Action Required',
                  style: const TextStyle(fontSize: 12),
                ),
                trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                onTap: () {
                  Navigator.pop(ctx);
                  showDialog(context: context, builder: (_) => const KycDialog());
                },
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.logout, color: AppColors.danger),
                title: const Text('Log Out', style: TextStyle(color: AppColors.danger)),
                onTap: () async {
                  Navigator.pop(ctx);
                  await fin.logout();
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

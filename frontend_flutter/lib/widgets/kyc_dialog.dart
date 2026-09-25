import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';

class KycDialog extends StatefulWidget {
  const KycDialog({Key? key}) : super(key: key);

  @override
  State<KycDialog> createState() => _KycDialogState();
}

class _KycDialogState extends State<KycDialog> {
  int _currentStep = 0; // 0: PAN, 1: Aadhaar, 2: OTP, 3: Success

  final _panController = TextEditingController();
  final _aadhaarController = TextEditingController();
  final _otpController = TextEditingController();

  String? _sessionId;
  String? _maskedAadhaar;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _panController.dispose();
    _aadhaarController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  Future<void> _handleVerifyPan(FinProvider fin) async {
    final pan = _panController.text.trim().toUpperCase();
    if (pan.length != 10) {
      setState(() => _errorMessage = 'Please enter a valid 10-digit PAN (e.g. ABCDE1234F)');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await fin.verifyPan(pan);
    setState(() => _isLoading = false);

    if (res['success'] == true) {
      setState(() {
        _currentStep = 1; // Move to Aadhaar DigiLocker step
      });
    } else {
      setState(() => _errorMessage = res['error'] ?? 'PAN verification failed');
    }
  }

  Future<void> _handleInitiateDigiLocker(FinProvider fin) async {
    final aadhaar = _aadhaarController.text.trim();
    if (aadhaar.length != 12) {
      setState(() => _errorMessage = 'Please enter a valid 12-digit Aadhaar number');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await fin.initiateDigiLocker(aadhaar);
    setState(() => _isLoading = false);

    if (res['success'] == true) {
      setState(() {
        _sessionId = res['session_id'];
        _maskedAadhaar = res['masked_aadhaar'] ?? 'XXXX-XXXX-XXXX';
        _currentStep = 2; // Move to OTP step
      });
    } else {
      setState(() => _errorMessage = res['error'] ?? 'DigiLocker initiation failed');
    }
  }

  Future<void> _handleVerifyOtp(FinProvider fin) async {
    final otp = _otpController.text.trim();
    if (otp.length != 6) {
      setState(() => _errorMessage = 'Please enter the 6-digit OTP (sandbox: 123456)');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await fin.verifyDigiLockerOtp(_sessionId ?? '', otp);
    setState(() => _isLoading = false);

    if (res['success'] == true) {
      setState(() {
        _currentStep = 3; // Success
      });
    } else {
      setState(() => _errorMessage = res['error'] ?? 'OTP verification failed');
    }
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isAlreadyVerified = fin.kycData?.kycStatus == 'verified';

    return Dialog(
      backgroundColor: AppColors.cardSurfaceRaised,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.verified_user, color: AppColors.primary, size: 20),
                    ),
                    const SizedBox(width: 12),
                    const Text(
                      'KYC Verification',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20, color: AppColors.textMuted),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const Divider(color: AppColors.border, height: 28),
            if (isAlreadyVerified || _currentStep == 3) ...[
              _buildSuccessState(),
            ] else ...[
              _buildStepIndicator(),
              const SizedBox(height: 20),
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.danger.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.danger.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, size: 16, color: AppColors.danger),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(color: AppColors.danger, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              if (_currentStep == 0) _buildPanStep(fin),
              if (_currentStep == 1) _buildAadhaarStep(fin),
              if (_currentStep == 2) _buildOtpStep(fin),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStepIndicator() {
    return Row(
      children: [
        _buildStepBadge(0, 'PAN'),
        Expanded(child: Container(height: 1, color: AppColors.border)),
        _buildStepBadge(1, 'Aadhaar'),
        Expanded(child: Container(height: 1, color: AppColors.border)),
        _buildStepBadge(2, 'OTP'),
      ],
    );
  }

  Widget _buildStepBadge(int stepIndex, String label) {
    final isActive = _currentStep == stepIndex;
    final isDone = _currentStep > stepIndex;

    Color bg = AppColors.backgroundSecondary;
    Color fg = AppColors.textMuted;
    if (isDone) {
      bg = AppColors.success.withOpacity(0.2);
      fg = AppColors.success;
    } else if (isActive) {
      bg = AppColors.primary;
      fg = Colors.white;
    }

    return Column(
      children: [
        CircleAvatar(
          radius: 12,
          backgroundColor: bg,
          child: isDone
              ? const Icon(Icons.check, size: 12, color: AppColors.success)
              : Text(
                  '${stepIndex + 1}',
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: fg),
                ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: isActive ? AppColors.textPrimary : AppColors.textMuted,
            fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }

  Widget _buildPanStep(FinProvider fin) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Step 1: Permanent Account Number (PAN)',
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _panController,
          textCapitalization: TextCapitalization.characters,
          decoration: const InputDecoration(
            hintText: 'e.g. ABCDE1234F',
            prefixIcon: Icon(Icons.credit_card, size: 18),
          ),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: ElevatedButton(
            onPressed: _isLoading ? null : () => _handleVerifyPan(fin),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
            child: _isLoading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Verify PAN'),
          ),
        ),
      ],
    );
  }

  Widget _buildAadhaarStep(FinProvider fin) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Step 2: DigiLocker Aadhaar Verification',
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _aadhaarController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            hintText: '12-digit Aadhaar number',
            prefixIcon: Icon(Icons.fingerprint, size: 18),
          ),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: ElevatedButton(
            onPressed: _isLoading ? null : () => _handleInitiateDigiLocker(fin),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
            child: _isLoading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Send Aadhaar OTP'),
          ),
        ),
      ],
    );
  }

  Widget _buildOtpStep(FinProvider fin) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Step 3: Enter OTP sent to ${_maskedAadhaar ?? 'Registered Mobile'}',
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _otpController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            hintText: '6-digit OTP (demo: 123456)',
            prefixIcon: Icon(Icons.lock_clock, size: 18),
          ),
        ),
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: ElevatedButton(
            onPressed: _isLoading ? null : () => _handleVerifyOtp(fin),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.success),
            child: _isLoading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Complete Verification'),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessState() {
    return Center(
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.success.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.verified, size: 48, color: AppColors.success),
          ),
          const SizedBox(height: 16),
          const Text(
            'KYC Successfully Verified!',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 6),
          const Text(
            'Your identity has been authenticated via Government DigiLocker and Income Tax databases.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
              child: const Text('Done'),
            ),
          ),
        ],
      ),
    );
  }
}

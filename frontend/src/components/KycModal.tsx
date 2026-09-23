/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useFin } from '../FinContext';
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  X, 
  CreditCard, 
  Fingerprint, 
  KeyRound, 
  Lock, 
  Sparkles,
  ExternalLink
} from 'lucide-react';

export const KycModal: React.FC = () => {
  const { 
    user, 
    kycData, 
    isKycModalOpen, 
    setIsKycModalOpen, 
    verifyPan, 
    initiateDigiLocker, 
    verifyDigiLockerOtp 
  } = useFin();

  const [step, setStep] = useState<'pan' | 'aadhaar' | 'otp' | 'success'>('pan');
  const [panNumber, setPanNumber] = useState('');
  const [aadhaarNumber, setAadhaarNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [maskedAadhaar, setMaskedAadhaar] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isKycModalOpen) return null;

  const isAlreadyVerified = kycData?.kyc_status === 'verified';

  const handleVerifyPan = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    const res = await verifyPan(panNumber.trim().toUpperCase());
    setLoading(false);

    if (res.success) {
      setSuccessMsg(res.message || 'PAN verified successfully!');
      setTimeout(() => {
        setSuccessMsg(null);
        setStep('aadhaar');
      }, 1000);
    } else {
      setErrorMsg(res.error || 'PAN verification failed.');
    }
  };

  const handleInitiateDigiLocker = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    const res = await initiateDigiLocker(aadhaarNumber.trim());
    setLoading(false);

    if (res.success && res.session_id) {
      setSessionId(res.session_id);
      setMaskedAadhaar(res.masked_aadhaar || 'XXXX-XXXX-XXXX');
      setStep('otp');
    } else {
      setErrorMsg(res.error || 'Failed to initiate DigiLocker session.');
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    const res = await verifyDigiLockerOtp(sessionId, otp.trim());
    setLoading(false);

    if (res.success) {
      setStep('success');
    } else {
      setErrorMsg(res.error || 'Invalid OTP code.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-[fadeIn_0.15s_ease-out]">
      <div className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl shadow-2xl relative overflow-hidden text-white">

        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 bg-blue-500/10 border border-blue-500/20 flex items-center justify-center rounded-xl text-blue-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">
                KYC & DigiLocker Verification
              </h3>
              <p className="text-xs text-slate-400">
                Government of India • Paperless e-KYC
              </p>
            </div>
          </div>
          <button 
            onClick={() => setIsKycModalOpen(false)}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Tracker */}
        <div className="px-6 py-3 flex items-center justify-between text-xs border-b border-white/5 bg-slate-950/40">
          <div className={`flex items-center space-x-1.5 ${step === 'pan' ? 'text-blue-400 font-semibold' : kycData?.pan_verified ? 'text-emerald-400' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-[11px] font-medium">
              {kycData?.pan_verified ? '✓' : '1'}
            </span>
            <span>PAN Card</span>
          </div>
          <div className="w-10 h-0.5 bg-white/10" />
          <div className={`flex items-center space-x-1.5 ${step === 'aadhaar' || step === 'otp' ? 'text-blue-400 font-semibold' : kycData?.digilocker_verified ? 'text-emerald-400' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-[11px] font-medium">
              {kycData?.digilocker_verified ? '✓' : '2'}
            </span>
            <span>DigiLocker Aadhaar</span>
          </div>
          <div className="w-10 h-0.5 bg-white/10" />
          <div className={`flex items-center space-x-1.5 ${step === 'success' || isAlreadyVerified ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full border border-current flex items-center justify-center text-[11px] font-medium">3</span>
            <span>Verified</span>
          </div>
        </div>

        {/* Error / Success Alerts */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2 rounded-xl">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mx-6 mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2 rounded-xl">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-6">

          {/* STEP 1: PAN VERIFICATION */}
          {step === 'pan' && !isAlreadyVerified && (
            <div>
              <div className="flex items-start space-x-3 mb-4">
                <CreditCard className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-white">Permanent Account Number (PAN)</h4>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                    Used to verify your tax identity and ensure accurate analysis of bank transactions and deductions.
                  </p>
                </div>
              </div>

              {kycData?.pan_verified ? (
                <div className="p-4 bg-slate-950 border border-emerald-500/30 rounded-xl mb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-400 block">Registered PAN</span>
                      <span className="text-sm font-semibold text-emerald-400 font-mono">{kycData.pan_number || 'VERIFIED'}</span>
                    </div>
                    <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-lg border border-emerald-500/20 flex items-center space-x-1 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Verified</span>
                    </span>
                  </div>
                  <button
                    onClick={() => setStep('aadhaar')}
                    className="w-full mt-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl text-xs transition-colors flex items-center justify-center space-x-2 cursor-pointer shadow-md shadow-blue-600/20"
                  >
                    <span>Proceed to DigiLocker Aadhaar</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <form onSubmit={handleVerifyPan} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      10-Digit PAN Number (e.g. ABCDE1234F)
                    </label>
                    <input
                      type="text"
                      maxLength={10}
                      placeholder="ABCDE1234F"
                      value={panNumber}
                      onChange={(e) => setPanNumber(e.target.value.toUpperCase())}
                      required
                      className="w-full bg-slate-950 border border-white/10 text-white text-sm font-mono tracking-widest py-2.5 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-600 uppercase"
                    />
                  </div>
                  <div className="text-xs text-slate-400 flex items-center space-x-1.5">
                    <Lock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>Validated securely against Income Tax Department (ITD) records.</span>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || panNumber.length !== 10}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all flex items-center justify-center space-x-2 rounded-xl disabled:opacity-50 cursor-pointer shadow-lg shadow-blue-600/25"
                  >
                    <span>{loading ? 'Verifying with NSDL...' : 'Verify PAN Card'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>
              )}
            </div>
          )}

          {/* STEP 2: DIGILOCKER INITIATE */}
          {step === 'aadhaar' && !isAlreadyVerified && (
            <div>
              {/* DigiLocker Official Brand Banner */}
              <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl mb-5 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-400/40 flex items-center justify-center text-blue-400">
                    <Fingerprint className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-blue-300 block">DigiLocker Aadhaar e-KYC</span>
                    <span className="text-[11px] text-slate-400">Digital India Initiative • Paperless Verification</span>
                  </div>
                </div>
                <span className="text-[11px] border border-blue-400/30 text-blue-400 px-2 py-0.5 rounded-md font-medium">
                  UIDAI Certified
                </span>
              </div>

              <form onSubmit={handleInitiateDigiLocker} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    12-Digit Aadhaar Number
                  </label>
                  <input
                    type="text"
                    maxLength={14}
                    placeholder="1234 5678 9012"
                    value={aadhaarNumber}
                    onChange={(e) => {
                      const digits = e.target.value.replace(/\D/g, '').slice(0, 12);
                      const formatted = digits.replace(/(\d{4})(?=\d)/g, '$1 ');
                      setAadhaarNumber(formatted);
                    }}
                    required
                    className="w-full bg-slate-950 border border-white/10 text-white text-sm font-mono tracking-widest py-2.5 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
                  />
                </div>

                <div className="text-xs text-slate-400 flex items-center space-x-1.5">
                  <Lock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Only the last 4 digits are masked and kept. Raw Aadhaar numbers are never stored.</span>
                </div>

                <button
                  type="submit"
                  disabled={loading || aadhaarNumber.replace(/\s/g, '').length !== 12}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all flex items-center justify-center space-x-2 rounded-xl disabled:opacity-50 cursor-pointer shadow-lg shadow-blue-600/25"
                >
                  <span>{loading ? 'Requesting DigiLocker OTP...' : 'Get DigiLocker OTP'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            </div>
          )}

          {/* STEP 3: OTP VERIFICATION */}
          {step === 'otp' && !isAlreadyVerified && (
            <div>
              <div className="flex items-start space-x-3 mb-4">
                <KeyRound className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-white">Enter Aadhaar Security OTP</h4>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                    A 6-digit code has been dispatched via DigiLocker to the mobile number registered with your Aadhaar ({maskedAadhaar}).
                  </p>
                </div>
              </div>

              {/* Demo hint */}
              <div className="mb-4 p-2.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs rounded-xl flex items-center justify-between">
                <span>Demo mode OTP: <strong className="font-mono text-white">123456</strong></span>
                <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Quick Test</span>
              </div>

              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    6-Digit DigiLocker OTP
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    required
                    className="w-full bg-slate-950 border border-white/10 text-white text-center text-lg tracking-[0.5em] py-2 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all flex items-center justify-center space-x-2 rounded-xl disabled:opacity-50 cursor-pointer shadow-lg shadow-blue-600/25"
                >
                  <span>{loading ? 'Authenticating with DigiLocker...' : 'Verify & Complete Profile'}</span>
                  <CheckCircle2 className="w-4 h-4" />
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => setStep('aadhaar')}
                    className="text-xs text-blue-400 hover:text-blue-300 transition-colors underline"
                  >
                    Change Aadhaar Number
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* STEP 4 / VERIFIED STATE */}
          {(step === 'success' || isAlreadyVerified) && (
            <div className="text-center py-4">
              <div className="w-14 h-14 bg-emerald-500/10 border-2 border-emerald-500 mx-auto flex items-center justify-center rounded-2xl text-emerald-400 mb-3 animate-[bounce_0.6s_ease-out]">
                <ShieldCheck className="w-7 h-7" />
              </div>

              <h4 className="text-base font-semibold text-white mb-1">
                Profile Verified with DigiLocker
              </h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mb-5 leading-relaxed">
                Your PAN and Aadhaar identity have been authenticated securely via Government of India DigiLocker.
              </p>

              <div className="bg-slate-950 border border-white/10 p-4 rounded-xl text-left text-xs space-y-2 mb-5">
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Account Holder:</span>
                  <span className="text-white font-medium">{user?.name}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">PAN Status:</span>
                  <span className="text-emerald-400 font-mono font-medium flex items-center space-x-1">
                    <span>{kycData?.pan_number || 'VERIFIED'}</span>
                    <span>✓</span>
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-white/5">
                  <span className="text-slate-400">Aadhaar (DigiLocker):</span>
                  <span className="text-emerald-400 font-mono font-medium flex items-center space-x-1">
                    <span>{kycData?.aadhaar_masked || 'XXXX-XXXX-VERIFIED'}</span>
                    <span>✓</span>
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-400">Monthly Income Baseline:</span>
                  <span className="text-emerald-400 font-mono font-semibold">
                    ₹{Number(user?.monthly_income || kycData?.monthly_income || 0).toLocaleString('en-IN')} / mo
                  </span>
                </div>
              </div>

              <button
                onClick={() => setIsKycModalOpen(false)}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all rounded-xl cursor-pointer shadow-lg shadow-blue-600/25"
              >
                Continue to Dashboard
              </button>
            </div>
          )}

        </div>

        {/* Footer info */}
        <div className="px-6 py-3 bg-slate-950/60 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-500">
          <span>Protected under IT Act, 2000</span>
          <span className="flex items-center space-x-1">
            <Lock className="w-3 h-3 text-slate-400" />
            <span>256-bit Bank Encryption</span>
          </span>
        </div>

      </div>
    </div>
  );
};

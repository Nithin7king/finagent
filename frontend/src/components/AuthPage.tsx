/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useFin } from '../FinContext';
import { Landmark, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { login, register, currentPage, setPage } = useFin();
  const isRegister = currentPage === '/register';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [monthlyIncome, setMonthlyIncome] = useState('85000');
  const [err, setErr] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setIsSubmitting(true);

    if (isRegister) {
      if (!name) {
        setErr('Please enter your full name.');
        setIsSubmitting(false);
        return;
      }
      const incomeVal = parseFloat(monthlyIncome);
      if (isNaN(incomeVal) || incomeVal <= 0) {
        setErr('Please provide a valid average monthly income.');
        setIsSubmitting(false);
        return;
      }
      const res = await register(name, email, password, incomeVal);
      if (!res.success) setErr(res.error || 'Registration failed. Email might already exist.');
    } else {
      const res = await login(email, password);
      if (!res.success) setErr(res.error || 'Invalid email or password.');
    }
    setIsSubmitting(false);
  };

  const handleDemoMode = async () => {
    setErr(null);
    setIsSubmitting(true);
    const res = await login('demo@finagent.ai', 'Demo@123');
    if (!res.success) setErr(res.error || 'Demo login failed. Please retry.');
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 md:p-8 select-none">
      
      {/* Brand Header */}
      <div className="mb-6 text-center flex flex-col items-center">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center text-white mb-3 shadow-lg shadow-blue-600/25">
          <Sparkles className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          MYFI.AI
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          India's Smart Personal Finance & Bank Assistant
        </p>
      </div>

      {/* Card Form */}
      <div className="w-full max-w-md bg-slate-900/90 border border-white/10 p-8 rounded-2xl shadow-2xl relative">
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold text-white tracking-tight">
            {isRegister ? 'Create Your Account' : 'Welcome Back'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {isRegister ? 'Start tracking your expenses and savings effortlessly' : 'Sign in to access your financial dashboard'}
          </p>
        </div>

        {err && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl mb-4 text-center leading-relaxed">
            {err}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          {isRegister && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Siva Sudhamsh"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-white/10 text-white py-2.5 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-500 text-sm"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-medium text-slate-300">
                    Average Monthly Income (₹)
                  </label>
                  <span className="text-[11px] text-blue-400">Baseline for budget</span>
                </div>
                <div className="relative">
                  <span className="absolute left-3.5 top-2.5 text-slate-400 font-medium">₹</span>
                  <input
                    type="number"
                    min="1000"
                    step="1000"
                    placeholder="85000"
                    value={monthlyIncome}
                    onChange={(e) => setMonthlyIncome(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-white/10 text-white py-2.5 pl-8 pr-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-500 font-mono text-sm"
                  />
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Used to calculate your savings rate and detect unusual spending spikes.</p>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-slate-950 border border-white/10 text-white py-2.5 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Password
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-slate-950 border border-white/10 text-white py-2.5 px-3.5 rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-slate-500 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/25 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            <span>{isSubmitting ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-white/10 flex flex-col space-y-3">
          {/* Quick Demo Selector */}
          <button
            onClick={handleDemoMode}
            disabled={isSubmitting}
            className="w-full py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 border border-blue-500/20 text-xs font-medium transition-all rounded-xl flex items-center justify-center space-x-2 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Explore Demo Account (Instant Login)</span>
          </button>

          <div className="text-center">
            <button
              onClick={() => setPage(isRegister ? '/login' : '/register')}
              className="text-slate-400 hover:text-white transition-all text-xs"
            >
              {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
            </button>
          </div>
        </div>
      </div>

      {/* Trust & Security Footnote */}
      <div className="mt-6 text-xs text-slate-500 text-center flex items-center space-x-1.5">
        <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
        <span>Bank-grade 256-bit encryption. Your financial data stays private.</span>
      </div>
    </div>
  );
};

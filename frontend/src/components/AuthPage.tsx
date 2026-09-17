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
  const [err, setErr] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setIsSubmitting(true);

    if (isRegister) {
      if (!name) {
        setErr('Please provide your name.');
        setIsSubmitting(false);
        return;
      }
      const success = await register(name, email, password);
      if (!success) setErr('Registration failed. Email might already exist.');
    } else {
      const success = await login(email, password);
      if (!success) setErr('Invalid email or password credentials.');
    }
    setIsSubmitting(false);
  };

  const handleDemoMode = async () => {
    setErr(null);
    setIsSubmitting(true);
    const success = await login('demo@finagent.ai', 'Demo@123');
    if (!success) setErr('Demo login failed. Please retry.');
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-ink flex flex-col items-center justify-center p-4 md:p-8 select-none">
      
      {/* Upper Logo Stamp */}
      <div className="mb-8 text-center flex flex-col items-center">
        <div className="w-12 h-12 border border-gold/40 flex items-center justify-center text-gold mb-3 bg-ink-raised rounded-sm">
          <Landmark className="w-6 h-6" />
        </div>
        <h1 className="text-3xl font-display font-medium tracking-tight text-white italic">
          MYFY.AI
        </h1>
        <p className="text-xs font-mono text-gold/60 uppercase tracking-widest mt-1.5">
          AI Personal Finance Ledger
        </p>
      </div>

      {/* Card Form */}
      <div className="w-full max-w-md bg-ink-raised border border-gold/15 p-8 rounded-sm shadow-2xl relative overflow-hidden">
        
        {/* Passbook security seal watermark */}
        <div className="absolute -right-12 -bottom-12 opacity-5 pointer-events-none">
          <ShieldCheck className="w-48 h-48 text-gold" />
        </div>

        <div className="text-center mb-6">
          <h2 className="text-xl font-display text-white tracking-wide font-medium">
            {isRegister ? 'Open Your Savings Ledger' : 'Access Your Passbook'}
          </h2>
          <p className="text-xs text-mist/60 mt-1">
            {isRegister ? 'Register your private credentials to start tracking' : 'Enter your registered credentials'}
          </p>
        </div>

        {err && (
          <div className="p-3 bg-coral/5 border border-coral/20 text-coral text-xs font-mono rounded-sm mb-5 text-center leading-relaxed">
            {err}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 font-mono text-xs">
          {isRegister && (
            <div>
              <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Account Holder Name</label>
              <input
                type="text"
                placeholder="Siva Sudhamsh"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/20"
              />
            </div>
          )}

          <div>
            <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Email Address</label>
            <input
              type="email"
              placeholder="siva@finagent.ai"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/20"
            />
          </div>

          <div>
            <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Secret Pin / Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/20"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-6 py-3 bg-gold text-ink font-bold font-sans text-xs uppercase tracking-wider hover:brightness-110 active:brightness-95 transition-all flex items-center justify-center space-x-2 rounded-sm cursor-pointer"
          >
            <span>{isSubmitting ? 'Verifying...' : isRegister ? 'Establish Account' : 'Authenticate Passbook'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-gold/10 flex flex-col space-y-4">
          {/* Quick Demo Selector */}
          <button
            onClick={handleDemoMode}
            disabled={isSubmitting}
            className="w-full py-2.5 bg-gold/10 hover:bg-gold/20 text-gold text-xs font-mono border border-gold/25 font-bold transition-all rounded-sm flex items-center justify-center space-x-2 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Examine Demo Account (Instant Access)</span>
          </button>

          <div className="text-center">
            <button
              onClick={() => setPage(isRegister ? '/login' : '/register')}
              className="text-mist hover:text-white hover:underline transition-all font-mono text-[10px] uppercase tracking-wider"
            >
              {isRegister ? 'Already have a passbook? Login' : 'Open a new savings ledger'}
            </button>
          </div>
        </div>
      </div>

      {/* Institutional Note */}
      <div className="mt-8 text-[9px] font-mono text-mist/30 text-center max-w-xs leading-relaxed select-none">
        SECURE CHANNELS ESTABLISHED UNDER AES-256 BANKING CONVENTIONS. FINAGENT NEVER EXPOSES PRIVATE LEDGERS.
      </div>
    </div>
  );
};

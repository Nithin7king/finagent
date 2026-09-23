/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useFin } from '../FinContext';
import { 
  Home, 
  ArrowUpDown, 
  BarChart3, 
  MessageSquare, 
  Target, 
  LogOut, 
  Sun, 
  Moon, 
  Menu, 
  X, 
  Landmark, 
  Wallet,
  User,
  ShieldCheck
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, kycData, setIsKycModalOpen, summary, currentPage, setPage, logout, theme, toggleTheme } = useFin();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  if (!user) return null;

  const navItems = [
    { name: 'Dashboard', icon: Home, path: '/' },
    { name: 'Transactions', icon: ArrowUpDown, path: '/transactions' },
    { name: 'Analytics', icon: BarChart3, path: '/analytics' },
    { name: 'Chat Assistant', icon: MessageSquare, path: '/chat' },
    { name: 'Goals', icon: Target, path: '/goals' },
  ];

  // Formatting utility for INR
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <nav id="app-navbar" className="sticky top-0 z-50 w-full bg-ink/90 backdrop-blur-lg border-b border-white/5 select-none text-white transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-18">
          
          {/* Left: Brand Identity */}
          <div className="flex items-center space-x-3 cursor-pointer shrink-0" onClick={() => { setPage('/'); setIsMobileMenuOpen(false); }}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 transition-transform hover:scale-105">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-lg font-bold tracking-tight text-white">
                  MYFI<span className="text-emerald-400">.AI</span>
                </span>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 uppercase tracking-wider">
                  India
                </span>
              </div>
              <span className="text-[10px] text-mist block font-normal">
                Personal Finance & Bank Assistant
              </span>
            </div>
          </div>

          {/* Center: Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1 bg-ink-tertiary p-1 rounded-xl border border-white/5">
            {navItems.map((item) => {
              const isActive = currentPage === item.path;
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  id={`nav-item-${item.path.replace('/', 'home')}`}
                  onClick={() => setPage(item.path)}
                  className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium transition-all rounded-lg ${
                    isActive 
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-semibold' 
                      : 'text-mist hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-mist'}`} />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </div>

          {/* Right: Balance & Settings Profile Controls */}
          <div className="hidden md:flex items-center space-x-3">
            {/* Live Balance Pill */}
            <div className="flex items-center space-x-2.5 px-3 py-1.5 bg-ink-raised border border-white/10 rounded-xl shadow-inner">
              <Wallet className="w-4 h-4 text-emerald-400" />
              <div className="flex flex-col text-left">
                <span className="text-[9px] uppercase text-mist font-medium">Net Balance</span>
                <span className="text-xs font-bold text-white tracking-tight">
                  {formatCurrency(summary.totalBalance)}
                </span>
              </div>
            </div>

            {/* KYC Status Badge */}
            <button
              onClick={() => setIsKycModalOpen(true)}
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-xl border transition-all cursor-pointer ${
                kycData?.kyc_status === 'verified'
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'
                  : 'border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 animate-pulse'
              }`}
              title="Click to view KYC & DigiLocker verification details"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>
                {kycData?.kyc_status === 'verified' ? 'DigiLocker Verified' : 'Complete KYC'}
              </span>
            </button>

            {/* Profile pill */}
            <div className="flex items-center space-x-2 px-2.5 py-1.5 border border-white/5 bg-ink-tertiary rounded-xl">
              <div className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center font-bold text-xs">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="text-left shrink-0">
                <div className="text-xs font-medium text-white leading-tight truncate max-w-[90px]">
                  {user.name}
                </div>
              </div>
            </div>

            {/* Theme & Logout Buttons */}
            <div className="flex items-center space-x-1 border-l border-white/10 pl-3">
              <button
                id="btn-theme-toggle"
                onClick={toggleTheme}
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                className="text-mist hover:text-white transition-colors p-2 rounded-lg hover:bg-white/5"
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button 
                id="btn-logout"
                onClick={logout} 
                title="Logout session"
                className="text-mist hover:text-rose-400 transition-colors p-2 rounded-lg hover:bg-rose-500/10"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Mobile Layout Controls (shown under lg) */}
          <div className="flex lg:hidden items-center space-x-2">
            {/* Theme toggle (visible directly on mobile) */}
            <button
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              className="text-mist hover:text-gold transition-colors p-2 rounded-sm"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Mobile menu trigger */}
            <button
              id="mobile-menu-trigger"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-mist hover:text-white p-2 focus:outline-none focus:ring-1 focus:ring-gold"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Drawer Dropdown Menu (shown when open) */}
      {isMobileMenuOpen && (
        <div id="mobile-menu-dropdown" className="lg:hidden bg-ink-raised border-t border-white/10 px-4 pt-4 pb-6 space-y-4 shadow-2xl">
          {/* User profile & balance info */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-ink/70 border border-white/5 rounded-xl">
            <div className="flex flex-col">
              <span className="text-[10px] text-mist font-medium">Account</span>
              <span className="text-xs font-semibold text-white truncate mt-0.5">{user.name}</span>
              <span className="text-[10px] text-mist truncate">{user.email}</span>
            </div>
            <div className="flex flex-col border-l border-white/10 pl-3">
              <span className="text-[10px] text-mist font-medium">Net Balance</span>
              <span className="text-sm font-bold text-emerald-400 mt-0.5">
                {formatCurrency(summary.totalBalance)}
              </span>
            </div>
          </div>

          {/* Mobile KYC Badge Button */}
          <div>
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                setIsKycModalOpen(true);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 text-xs rounded-xl border transition-all ${
                kycData?.kyc_status === 'verified'
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                  : 'border-amber-500/40 bg-amber-500/10 text-amber-300 animate-pulse font-semibold'
              }`}
            >
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4" />
                <span>{kycData?.kyc_status === 'verified' ? 'DigiLocker Verified Profile' : 'Complete DigiLocker KYC'}</span>
              </div>
              <span className="text-[10px] uppercase font-bold">
                {kycData?.kyc_status === 'verified' ? 'Verified ✓' : 'Action Required →'}
              </span>
            </button>
          </div>

          {/* Navigation Links */}
          <div className="space-y-1">
            {navItems.map((item) => {
              const isActive = currentPage === item.path;
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  onClick={() => {
                    setPage(item.path);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3.5 py-2.5 text-xs font-medium rounded-xl transition-all ${
                    isActive 
                      ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/30' 
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </div>

          {/* Actions */}
          <div className="pt-3 border-t border-white/10 flex justify-between items-center">
            <span className="text-[10px] text-mist">Signed in securely</span>
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                logout();
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg text-xs font-medium transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

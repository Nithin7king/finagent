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
  User
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, summary, currentPage, setPage, logout, theme, toggleTheme } = useFin();
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
    <nav id="app-navbar" className="sticky top-0 z-50 w-full bg-ink-raised/95 backdrop-blur-md border-b border-gold/15 select-none text-white transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          
          {/* Left: Brand Identity */}
          <div className="flex items-center space-x-3 cursor-pointer shrink-0" onClick={() => { setPage('/'); setIsMobileMenuOpen(false); }}>
            <div className="w-9 h-9 border border-gold/30 flex items-center justify-center text-gold bg-ink rounded-sm transition-all hover:border-gold">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xl font-display font-medium tracking-tight text-white italic">
                MYFY.AI
              </span>
              <span className="hidden sm:inline-block text-[9px] font-mono text-gold/60 uppercase tracking-widest block ml-2">
                Passbook
              </span>
            </div>
          </div>

          {/* Center: Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const isActive = currentPage === item.path;
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  id={`nav-item-${item.path.replace('/', 'home')}`}
                  onClick={() => setPage(item.path)}
                  className={`flex items-center space-x-2 px-4 py-2 text-xs font-mono uppercase tracking-wider transition-all relative rounded-sm ${
                    isActive 
                      ? 'text-gold font-bold' 
                      : 'text-mist hover:text-white'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 transition-colors duration-200 ${
                    isActive ? 'text-gold' : 'text-mist'
                  }`} />
                  <span>{item.name}</span>
                  
                  {/* Subtle golden underlying accent line */}
                  {isActive && (
                    <span className="absolute bottom-0 left-4 right-4 h-[1.5px] bg-gold rounded-full" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Right: Balance & Settings Profile Controls */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Live Balance Ledger Stamp */}
            <div className="flex items-center space-x-2.5 px-3 py-1.5 bg-ink border border-gold/15 rounded-sm">
              <Wallet className="w-3.5 h-3.5 text-gold/60" />
              <div className="flex flex-col text-left">
                <span className="text-[8px] font-mono uppercase text-mist/60 leading-none">Available Balance</span>
                <span className="text-sm font-mono font-bold text-gold leading-normal tracking-tight">
                  {formatCurrency(summary.totalBalance)}
                </span>
              </div>
            </div>

            {/* Profile pill */}
            <div className="flex items-center space-x-2 px-3 py-1.5 border border-gold/10 bg-ink/40 rounded-sm">
              <div className="w-5 h-5 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center">
                <User className="w-3 h-3 text-gold" />
              </div>
              <div className="text-left shrink-0">
                <div className="text-xs font-semibold text-white leading-tight truncate max-w-[100px]">
                  {user.name}
                </div>
              </div>
            </div>

            {/* Theme & Logout Buttons */}
            <div className="flex items-center space-x-1 border-l border-gold/15 pl-4">
              <button
                id="btn-theme-toggle"
                onClick={toggleTheme}
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                className="text-mist hover:text-gold transition-colors p-2 rounded-sm hover:bg-gold/5"
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button 
                id="btn-logout"
                onClick={logout} 
                title="Logout session"
                className="text-mist hover:text-coral transition-colors p-2 rounded-sm hover:bg-coral/5"
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
        <div id="mobile-menu-dropdown" className="lg:hidden bg-ink-raised border-t border-gold/15 px-4 pt-4 pb-6 space-y-4 shadow-xl">
          {/* User profile & balance info */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-ink/50 border border-gold/10 rounded-sm">
            <div className="flex flex-col">
              <span className="text-[9px] font-mono text-mist/60 uppercase">Account Holder</span>
              <span className="text-xs font-semibold text-white truncate mt-1">{user.name}</span>
              <span className="text-[9px] font-mono text-gold/60 truncate">{user.email}</span>
            </div>
            <div className="flex flex-col border-l border-gold/10 pl-3">
              <span className="text-[9px] font-mono text-mist/60 uppercase">Available Balance</span>
              <span className="text-sm font-mono font-bold text-gold mt-1">
                {formatCurrency(summary.totalBalance)}
              </span>
            </div>
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
                  className={`w-full flex items-center space-x-3 px-4 py-3 text-xs font-mono uppercase tracking-wider rounded-sm transition-all ${
                    isActive 
                      ? 'bg-gold/10 text-gold border-l-2 border-gold font-bold' 
                      : 'text-mist hover:text-white hover:bg-gold/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </div>

          {/* Actions */}
          <div className="pt-3 border-t border-gold/10 flex justify-between items-center">
            <span className="text-[9px] font-mono text-mist/40 uppercase">Secure Session Layer</span>
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                logout();
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-coral/10 hover:bg-coral/20 border border-coral/25 text-coral rounded-sm text-xs font-mono uppercase tracking-wider transition-colors"
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

/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { FinProvider, useFin } from './FinContext';
import { Navbar } from './components/Navbar';
import { AuthPage } from './components/AuthPage';
import { DashboardPage } from './components/DashboardPage';
import { TransactionsPage } from './components/TransactionsPage';
import { AnalyticsPage } from './components/AnalyticsPage';
import { ChatPage } from './components/ChatPage';
import { GoalsPage } from './components/GoalsPage';
import { ShieldCheck, Loader2 } from 'lucide-react';

// Custom Skeleton Loader mimicking actual ledger structures
const LedgerSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-ink flex flex-col p-6 md:p-12 space-y-8 select-none">
      <div className="space-y-2">
        <div className="h-3 w-40 bg-gold/10 rounded-sm animate-pulse" />
        <div className="h-8 w-60 bg-gold/15 rounded-sm animate-pulse font-display" />
      </div>
      
      <div className="bg-paper text-ink-text border border-gold/10 rounded-sm p-8 space-y-6 shadow-2xl">
        <div className="flex justify-between items-center border-b border-ink/15 pb-5">
          <div className="h-5 w-32 bg-ink/15 rounded-sm animate-pulse" />
          <div className="h-4 w-44 bg-ink/5 rounded-sm animate-pulse" />
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex justify-between items-center py-4.5 border-b border-ink/10">
              <div className="h-4 w-16 bg-ink/10 rounded-sm animate-pulse font-mono" />
              <div className="h-4 w-48 bg-ink/5 rounded-sm animate-pulse" />
              <div className="h-5 w-20 bg-ink/10 rounded-sm animate-pulse" />
              <div className="h-4 w-24 bg-ink/15 rounded-sm animate-pulse text-right" />
              <div className="h-4 w-28 bg-ink/10 rounded-sm animate-pulse text-right" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const MainAppContent: React.FC = () => {
  const { user, currentPage, isLoading } = useFin();

  if (isLoading) {
    return <LedgerSkeleton />;
  }

  // Handle Authentication wall
  if (!user) {
    return <AuthPage />;
  }

  // Active view router resolver
  const renderPage = () => {
    switch (currentPage) {
      case '/':
        return <DashboardPage />;
      case '/transactions':
        return <TransactionsPage />;
      case '/analytics':
        return <AnalyticsPage />;
      case '/chat':
        return <ChatPage />;
      case '/goals':
        return <GoalsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-ink text-white flex flex-col relative transition-colors duration-300">
      {/* Premium Top Navigation Bar */}
      <Navbar />

      {/* Main ledger viewing content panel */}
      <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full">
        <div className="page-fade-enter page-fade-enter-active">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};

export default function App() {
  return (
    <FinProvider>
      <MainAppContent />
    </FinProvider>
  );
}

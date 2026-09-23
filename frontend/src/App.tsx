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
import { KycModal } from './components/KycModal';
import { ShieldCheck, Loader2 } from 'lucide-react';

// Modern Skeleton Loader
const LedgerSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col p-6 md:p-12 space-y-8 select-none">
      <div className="space-y-2">
        <div className="h-4 w-32 bg-white/5 rounded-lg animate-pulse" />
        <div className="h-8 w-56 bg-white/10 rounded-xl animate-pulse" />
      </div>
      
      <div className="bg-slate-900 border border-white/10 rounded-2xl p-8 space-y-6 shadow-2xl">
        <div className="flex justify-between items-center border-b border-white/10 pb-5">
          <div className="h-5 w-32 bg-white/10 rounded-lg animate-pulse" />
          <div className="h-4 w-44 bg-white/5 rounded-lg animate-pulse" />
        </div>
        
        <div className="space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex justify-between items-center py-4 border-b border-white/5">
              <div className="h-4 w-20 bg-white/5 rounded-lg animate-pulse" />
              <div className="h-4 w-48 bg-white/10 rounded-lg animate-pulse" />
              <div className="h-6 w-24 bg-white/5 rounded-full animate-pulse" />
              <div className="h-4 w-24 bg-white/10 rounded-lg animate-pulse text-right" />
              <div className="h-4 w-28 bg-white/5 rounded-lg animate-pulse text-right" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallbackKey?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Component render error:", error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    if (prevProps.fallbackKey !== this.props.fallbackKey && this.state.hasError) {
      this.setState({ hasError: false, error: null });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-slate-900/80 border border-rose-500/30 rounded-2xl text-center space-y-4 max-w-lg mx-auto mt-12 shadow-2xl">
          <div className="w-12 h-12 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl flex items-center justify-center mx-auto">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Something went wrong loading this view</h3>
            <p className="text-xs text-slate-400 mt-1">{this.state.error?.message || 'An unexpected rendering error occurred.'}</p>
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md shadow-blue-600/25 cursor-pointer"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

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
          <ErrorBoundary fallbackKey={currentPage}>
            {renderPage()}
          </ErrorBoundary>
        </div>
      </main>

      {/* Interactive KYC & DigiLocker Onboarding Modal */}
      <KycModal />
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

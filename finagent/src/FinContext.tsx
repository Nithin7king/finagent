/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Transaction, Goal, Subscription, ForecastPoint, ChatMessage, DashboardSummary, Anomaly, Category } from './types';

interface FinContextType {
  user: { name: string; email: string } | null;
  transactions: Transaction[];
  goals: Goal[];
  subscriptions: Subscription[];
  chatHistory: ChatMessage[];
  summary: DashboardSummary;
  forecast: ForecastPoint[];
  activeAnomalies: Anomaly[];
  currentPage: string;
  isLoading: boolean;
  isChatLoading: boolean;
  theme: 'dark' | 'light';
  setPage: (page: string) => void;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  addTransaction: (tx: Omit<Transaction, 'id' | 'status' | 'balanceAfter' | 'isAnomaly'>) => Promise<void>;
  correctCategory: (txId: string, category: Category) => Promise<void>;
  uploadCSV: (csvText: string) => Promise<Transaction[]>;
  commitCSV: (txs: Transaction[]) => Promise<void>;
  createGoal: (goal: Omit<Goal, 'id' | 'currentAmount'>) => Promise<void>;
  contributeToGoal: (goalId: string, amount: number) => Promise<void>;
  sendChatMessage: (text: string) => Promise<void>;
  getWeeklyDigest: () => Promise<string>;
  refreshAllData: () => Promise<void>;
  toggleTheme: () => void;
}

const FinContext = createContext<FinContextType | undefined>(undefined);

export const useFin = () => {
  const context = useContext(FinContext);
  if (!context) {
    throw new Error('useFin must be used within a FinProvider');
  }
  return context;
};

export const FinProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [activeAnomalies, setActiveAnomalies] = useState<Anomaly[]>([]);
  const [summary, setSummary] = useState<DashboardSummary>({
    totalBalance: 250000,
    thisMonthSpend: 0,
    savingsRate: 0,
    anomaliesCount: 0,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState('/');

  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || saved === 'light') return saved;
    }
    return 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('dark', 'light');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  // Setup simple history-synchronized routing
  useEffect(() => {
    const handleLocationChange = () => {
      const path = window.location.pathname;
      if (path === '/login' || path === '/register' || path === '/transactions' || path === '/analytics' || path === '/chat' || path === '/goals') {
        setCurrentPage(path);
      } else {
        setCurrentPage('/');
      }
    };

    window.addEventListener('popstate', handleLocationChange);
    handleLocationChange(); // Initial page resolve

    return () => {
      window.removeEventListener('popstate', handleLocationChange);
    };
  }, []);

  const setPage = (page: string) => {
    if (window.location.pathname !== page) {
      window.history.pushState(null, '', page);
      setCurrentPage(page);
    }
  };

  // Fetch all current financial state from backend
  const refreshAllData = async () => {
    try {
      const txRes = await fetch('/api/transactions');
      if (txRes.ok) {
        const data = await txRes.json();
        setTransactions(data.transactions);
      }

      const summaryRes = await fetch('/api/analytics/summary');
      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setSummary(data);
      }

      const anomaliesRes = await fetch('/api/analytics/anomalies');
      if (anomaliesRes.ok) {
        const data = await anomaliesRes.json();
        setActiveAnomalies(data.anomalies);
      }

      const subsRes = await fetch('/api/analytics/subscriptions');
      if (subsRes.ok) {
        const data = await subsRes.json();
        setSubscriptions(data.subscriptions);
      }

      const goalsRes = await fetch('/api/goals');
      if (goalsRes.ok) {
        const data = await goalsRes.json();
        setGoals(data.goals);
      }

      const forecastRes = await fetch('/api/analytics/forecast');
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecast(data.forecast);
      }

      const chatRes = await fetch('/api/chat');
      if (chatRes.ok) {
        const data = await chatRes.json();
        setChatHistory(data.chatHistory);
      }
    } catch (err) {
      console.error("Failed to load initial FinAgent state", err);
    }
  };

  // Verify auth session on boot
  useEffect(() => {
    const verifyUser = async () => {
      try {
        const res = await fetch('/api/auth/me');
        if (res.ok) {
          const data = await res.json();
          setUser(data.user);
          await refreshAllData();
        } else {
          // If not authenticated, redirect to login
          setUser(null);
          if (window.location.pathname !== '/register') {
            setPage('/login');
          }
        }
      } catch (err) {
        console.error("Authentication check failed", err);
      } finally {
        setIsLoading(false);
      }
    };
    verifyUser();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        await refreshAllData();
        setPage('/');
        return true;
      }
      return false;
    } catch (err) {
      console.error(err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
        await refreshAllData();
        setPage('/');
        return true;
      }
      return false;
    } catch (err) {
      console.error(err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      setUser(null);
      setPage('/login');
    } catch (err) {
      console.error(err);
    }
  };

  const addTransaction = async (tx: Omit<Transaction, 'id' | 'status' | 'balanceAfter' | 'isAnomaly'>) => {
    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tx),
      });
      if (res.ok) {
        await refreshAllData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const correctCategory = async (txId: string, category: Category) => {
    try {
      const res = await fetch(`/api/transactions/${txId}/category`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category }),
      });
      if (res.ok) {
        // Optimistic local state update to prevent UI flickers
        setTransactions(prev => prev.map(t => t.id === txId ? { ...t, category, status: 'user-corrected' } : t));
        await refreshAllData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const uploadCSV = async (csvText: string): Promise<Transaction[]> => {
    const res = await fetch('/api/transactions/upload-csv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csvText }),
    });
    if (res.ok) {
      const data = await res.json();
      return data.preview;
    }
    throw new Error('Could not parse CSV');
  };

  const commitCSV = async (txs: Transaction[]) => {
    const res = await fetch('/api/transactions/commit-upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions: txs }),
    });
    if (res.ok) {
      await refreshAllData();
    } else {
      throw new Error('Could not commit uploaded ledger');
    }
  };

  const createGoal = async (goal: Omit<Goal, 'id' | 'currentAmount'>) => {
    try {
      const res = await fetch('/api/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(goal),
      });
      if (res.ok) {
        await refreshAllData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const contributeToGoal = async (goalId: string, amount: number) => {
    try {
      const res = await fetch(`/api/goals/${goalId}/contribute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
      });
      if (res.ok) {
        await refreshAllData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const sendChatMessage = async (text: string) => {
    try {
      setIsChatLoading(true);
      
      // Add optimistic user message
      const tempUserMsg: ChatMessage = {
        id: `msg-temp-user-${Date.now()}`,
        sender: 'user',
        text,
        timestamp: new Date().toISOString(),
      };
      setChatHistory(prev => [...prev, tempUserMsg]);

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatHistory(data.chatHistory);
        await refreshAllData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsChatLoading(false);
    }
  };

  const getWeeklyDigest = async (): Promise<string> => {
    try {
      const res = await fetch('/api/chat/digest');
      if (res.ok) {
        const data = await res.json();
        return data.digest;
      }
      return 'Digest unavailable. Please connect passbook.';
    } catch (err) {
      console.error(err);
      return 'Error retrieving digest.';
    }
  };

  return (
    <FinContext.Provider value={{
      user,
      transactions,
      goals,
      subscriptions,
      chatHistory,
      summary,
      forecast,
      activeAnomalies,
      currentPage,
      isLoading,
      isChatLoading,
      theme,
      setPage,
      login,
      register,
      logout,
      addTransaction,
      correctCategory,
      uploadCSV,
      commitCSV,
      createGoal,
      contributeToGoal,
      sendChatMessage,
      getWeeklyDigest,
      refreshAllData,
      toggleTheme,
    }}>
      {children}
    </FinContext.Provider>
  );
};

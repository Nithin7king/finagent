import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiFetch, clearToken, getToken, setToken } from './api';
import { Anomaly, Category, ChatMessage, DashboardSummary, ForecastPoint, Goal, Subscription, Transaction } from './types';

interface FinContextType {
  user: { name: string; email: string } | null;
  transactions: Transaction[]; goals: Goal[]; subscriptions: Subscription[];
  chatHistory: ChatMessage[]; summary: DashboardSummary; forecast: ForecastPoint[];
  activeAnomalies: Anomaly[]; currentPage: string; isLoading: boolean;
  isChatLoading: boolean; theme: 'dark' | 'light';
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
  refreshAllData: () => Promise<void>; toggleTheme: () => void;
}

const FinContext = createContext<FinContextType | undefined>(undefined);
export const useFin = () => {
  const context = useContext(FinContext);
  if (!context) throw new Error('useFin must be used within a FinProvider');
  return context;
};

const category = (value?: string): Category => {
  const map: Record<string, Category> = { Income: 'Salary', Investments: 'Investment', Other: 'Others' };
  return (map[value || ''] || value || 'Others') as Category;
};

const mapTransactions = (rows: any[]): Transaction[] => {
  let balance = 0;
  return [...rows].reverse().map(row => {
    balance += Number(row.amount);
    return {
      id: String(row.id), date: String(row.date).slice(0, 10), description: row.description,
      amount: Number(row.amount), category: category(row.category),
      status: (row.source === 'manual' || row.category !== row.ml_category ? 'user-corrected' : 'AI-assigned') as Transaction['status'],
      isAnomaly: Boolean(row.anomaly_label), balanceAfter: balance,
    };
  }).reverse();
};

export const FinProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [activeAnomalies, setActiveAnomalies] = useState<Anomaly[]>([]);
  const [summary, setSummary] = useState<DashboardSummary>({ totalBalance: 0, thisMonthSpend: 0, savingsRate: 0, anomaliesCount: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState('/');
  const [theme, setTheme] = useState<'dark' | 'light'>(() => (localStorage.getItem('theme') as 'dark' | 'light') || 'dark');
  const [sessionId, setSessionId] = useState<string>();

  useEffect(() => {
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    const syncRoute = () => setCurrentPage(['/login', '/register', '/transactions', '/analytics', '/chat', '/goals'].includes(location.pathname) ? location.pathname : '/');
    addEventListener('popstate', syncRoute); syncRoute();
    return () => removeEventListener('popstate', syncRoute);
  }, []);

  const setPage = (page: string) => { if (location.pathname !== page) history.pushState(null, '', page); setCurrentPage(page); };

  const refreshAllData = async () => {
    const [txRes, summaryRes, anomaliesRes, subsRes, goalsRes] = await Promise.all([
      apiFetch('/transactions?per_page=200'), apiFetch('/analytics/summary'), apiFetch('/analytics/anomalies'),
      apiFetch('/analytics/subscriptions'), apiFetch('/goals'),
    ]);
    if ([txRes, summaryRes, anomaliesRes, subsRes, goalsRes].some(res => res.status === 401)) throw new Error('Unauthorized');
    const [txData, summaryData, anomalyData, subData, goalData] = await Promise.all([
      txRes.json(), summaryRes.json(), anomaliesRes.json(), subsRes.json(), goalsRes.json(),
    ]);
    const mappedTransactions = mapTransactions(txData.transactions || []);
    setTransactions(mappedTransactions);
    setSummary({
      totalBalance: mappedTransactions.reduce((sum, tx) => sum + tx.amount, 0),
      thisMonthSpend: Number(summaryData.total_expenses || 0), savingsRate: Number(summaryData.savings_rate || 0),
      anomaliesCount: Number(anomalyData.count || 0),
    });
    setActiveAnomalies((anomalyData.anomalies || []).map((item: any) => ({
      id: String(item.id), transactionId: String(item.id), date: item.date, merchant: item.description,
      amount: Number(item.amount), severity: `${item.severity[0].toUpperCase()}${item.severity.slice(1)}`,
      explanation: item.explanation,
    })));
    const creep = Math.min(100, Math.round(Number(subData.creep_analysis?.income_pct || 0) * 5));
    setSubscriptions((subData.subscriptions || []).map((item: any, index: number) => ({
      id: `${item.merchant}-${index}`, merchant: item.merchant, amount: Number(item.amount),
      cadence: `${item.interval_days} days`, nextChargeDate: item.next_expected || '—', creepScore: creep,
    })));
    setGoals((goalData || []).map((item: any) => ({
      id: String(item.id), name: item.name, targetAmount: Number(item.target_amount),
      currentAmount: Number(item.current_amount), targetDate: item.target_date?.slice(0, 10) || '',
      category: item.description || 'Savings',
    })));

    const forecastResponses = await Promise.all([30, 60, 90].map(days => apiFetch(`/analytics/forecast?horizon_days=${days}`)));
    const forecastData = await Promise.all(forecastResponses.map(res => res.json()));
    setForecast(forecastData.map((item: any) => {
      const projected = Number(item.predicted_total_expense || 0);
      return { date: `${item.period_days} Days Forecast`, projected, confidenceMin: projected * .85, confidenceMax: projected * 1.15 };
    }));
  };

  useEffect(() => {
    (async () => {
      if (!getToken()) { if (location.pathname !== '/register') setPage('/login'); setIsLoading(false); return; }
      try {
        const res = await apiFetch('/auth/me');
        if (!res.ok) throw new Error('Unauthorized');
        const data = await res.json(); setUser({ name: data.name, email: data.email }); await refreshAllData();
      } catch { clearToken(); setUser(null); setPage('/login'); }
      finally { setIsLoading(false); }
    })();
  }, []);

  const authenticate = async (path: string, body: object) => {
    setIsLoading(true);
    try {
      const res = await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
      if (!res.ok) return false;
      const data = await res.json(); setToken(data.access_token); setUser({ name: data.name, email: data.email });
      await refreshAllData(); setPage('/'); return true;
    } finally { setIsLoading(false); }
  };

  const login = (email: string, password: string) => authenticate('/auth/login', { email, password });
  const register = (name: string, email: string, password: string) => authenticate('/auth/register', { name, email, password });
  const logout = async () => { clearToken(); setUser(null); setTransactions([]); setPage('/login'); };

  const addTransaction = async (tx: any) => {
    const res = await apiFetch('/transactions', { method: 'POST', body: JSON.stringify({ date: tx.date, description: tx.description, amount: tx.amount, category: tx.category }) });
    if (!res.ok) throw new Error('Could not create transaction'); await refreshAllData();
  };
  const correctCategory = async (txId: string, value: Category) => {
    const res = await apiFetch(`/transactions/${txId}`, { method: 'PUT', body: JSON.stringify({ category: value === 'Others' ? 'Other' : value }) });
    if (!res.ok) throw new Error('Could not update category'); await refreshAllData();
  };
  const uploadCSV = async (csvText: string) => {
    const lines = csvText.trim().split(/\r?\n/); const headers = lines.shift()?.split(',').map(x => x.trim().toLowerCase()) || [];
    return lines.map((line, index) => {
      const values = line.split(',').map(x => x.trim().replace(/^"|"$/g, '')); const row = Object.fromEntries(headers.map((h, i) => [h, values[i]]));
      return { id: `preview-${index}`, date: row.date, description: row.description || row.merchant || 'Imported transaction', amount: Number(row.amount), category: category(row.category), status: 'AI-assigned', isAnomaly: false, balanceAfter: 0 } as Transaction;
    }).filter(tx => tx.date && Number.isFinite(tx.amount));
  };
  const commitCSV = async (txs: Transaction[]) => {
    for (const tx of txs) await addTransaction(tx);
    await refreshAllData();
  };
  const createGoal = async (goal: any) => {
    const res = await apiFetch('/goals', { method: 'POST', body: JSON.stringify({ name: goal.name, description: goal.category, target_amount: goal.targetAmount, current_amount: goal.currentAmount, target_date: goal.targetDate }) });
    if (!res.ok) throw new Error('Could not create goal'); await refreshAllData();
  };
  const contributeToGoal = async (goalId: string, amount: number) => {
    const res = await apiFetch(`/goals/${goalId}/contribute`, { method: 'POST', body: JSON.stringify({ amount }) });
    if (!res.ok) throw new Error('Could not add contribution'); await refreshAllData();
  };
  const sendChatMessage = async (text: string) => {
    setIsChatLoading(true);
    const userMessage: ChatMessage = { id: `user-${Date.now()}`, sender: 'user', text, timestamp: new Date().toISOString() };
    setChatHistory(items => [...items, userMessage]);
    try {
      const res = await apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message: text, session_id: sessionId }) });
      if (!res.ok) throw new Error('Chat request failed'); const data = await res.json(); setSessionId(data.session_id);
      setChatHistory(items => [...items, { id: `agent-${Date.now()}`, sender: 'agent', text: data.response, timestamp: new Date().toISOString(), toolCalls: data.tool_calls_made }]);
    } finally { setIsChatLoading(false); }
  };
  const getWeeklyDigest = async () => { const res = await apiFetch('/chat/digest'); return res.ok ? (await res.json()).digest : 'Digest unavailable.'; };

  return <FinContext.Provider value={{ user, transactions, goals, subscriptions, chatHistory, summary, forecast, activeAnomalies, currentPage, isLoading, isChatLoading, theme, setPage, login, register, logout, addTransaction, correctCategory, uploadCSV, commitCSV, createGoal, contributeToGoal, sendChatMessage, getWeeklyDigest, refreshAllData, toggleTheme: () => setTheme(value => value === 'dark' ? 'light' : 'dark') }}>{children}</FinContext.Provider>;
};

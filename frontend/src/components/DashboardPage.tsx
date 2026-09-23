import React from 'react';
import { useFin } from '../FinContext';
import { StatCard } from './StatCard';
import { StampBadge } from './StampBadge';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  Sparkles, 
  ArrowRight, 
  AlertCircle, 
  Wallet, 
  ArrowDownRight, 
  ArrowUpRight, 
  PiggyBank, 
  Upload, 
  Target, 
  MessageSquare, 
  Calendar,
  CheckCircle2
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, summary, forecast, activeAnomalies, transactions, setPage } = useFin();

  // Simple formatting helper for Indian Rupees
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Stacked Area Chart data: last 6 months category expenditures
  const spendingHistory = [
    { name: 'Feb', Housing: 45000, Investment: 20000, Food: 15400, Utilities: 8200, Shopping: 12000 },
    { name: 'Mar', Housing: 45000, Investment: 25000, Food: 14200, Utilities: 7900, Shopping: 8500 },
    { name: 'Apr', Housing: 45000, Investment: 25000, Food: 16100, Utilities: 9100, Shopping: 14000 },
    { name: 'May', Housing: 45000, Investment: 30000, Food: 13900, Utilities: 8500, Shopping: 11200 },
    { name: 'Jun', Housing: 45000, Investment: 30000, Food: 15200, Utilities: 7600, Shopping: 9500 },
    { name: 'Jul', Housing: 45000, Investment: 30000, Food: 13800, Utilities: 7399, Shopping: 15400 },
  ];

  // Friendly Tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const total = payload.reduce((acc: number, item: any) => acc + item.value, 0);
      return (
        <div className="bg-slate-900 border border-white/10 text-white p-3 text-xs shadow-2xl rounded-xl">
          <div className="font-semibold border-b border-white/10 pb-1 mb-2 text-blue-300">{label} Spending</div>
          {payload.map((item: any) => (
            <div key={item.name} className="flex justify-between space-x-6 py-0.5">
              <span className="text-slate-400">{item.name}:</span>
              <span className="font-semibold text-white">{formatCurrency(item.value)}</span>
            </div>
          ))}
          <div className="border-t border-white/10 mt-2 pt-1 flex justify-between font-bold text-blue-400">
            <span>Total Spent:</span>
            <span>{formatCurrency(total)}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  const recentTransactions = transactions.slice(0, 5);

  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      
      {/* Top Welcome & Quick Actions Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Welcome back, {user?.name?.split(' ')[0] || 'Friend'} 👋
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
            Here is your financial summary, recent spending, and savings progress.
          </p>
        </div>

        {/* Quick action shortcuts */}
        <div className="flex flex-wrap items-center gap-2">
          <button 
            onClick={() => setPage('/transactions')}
            className="flex items-center space-x-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-md shadow-blue-600/20 transition-all cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Statement</span>
          </button>
          <button 
            onClick={() => setPage('/chat')}
            className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 border border-white/10 hover:border-white/20 text-white text-xs font-medium rounded-xl transition-all cursor-pointer"
          >
            <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
            <span>Ask AI Advisor</span>
          </button>
          <button 
            onClick={() => setPage('/goals')}
            className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 border border-white/10 hover:border-white/20 text-white text-xs font-medium rounded-xl transition-all cursor-pointer"
          >
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <span>Goals</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          id="kpi-balance"
          title="Total Net Balance"
          value={summary.totalBalance}
          format="currency"
          subtitle="Across bank accounts"
          icon={Wallet}
          colorScheme="emerald"
          trend={{ type: 'positive', label: 'Healthy' }}
        />
        <StatCard 
          id="kpi-income"
          title="Monthly Income"
          value={user?.monthly_income || 120000}
          format="currency"
          subtitle="Declared earnings"
          icon={ArrowUpRight}
          colorScheme="blue"
          trend={{ type: 'positive', label: 'Primary' }}
        />
        <StatCard 
          id="kpi-spend"
          title="Spent This Month"
          value={summary.thisMonthSpend}
          format="currency"
          subtitle="Total outflows"
          icon={ArrowDownRight}
          colorScheme="rose"
          trend={{ type: 'neutral', label: 'Tracked' }}
        />
        <StatCard 
          id="kpi-savings"
          title="Monthly Savings Rate"
          value={summary.savingsRate}
          format="percentage"
          subtitle="Target 30%+"
          icon={PiggyBank}
          colorScheme="emerald"
          trend={{ type: 'positive', label: 'On Track' }}
        />
      </div>

      {/* Flagged Unusual Spends Banner (if any) */}
      {activeAnomalies.length > 0 && (
        <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg shadow-rose-950/20">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white">
                {activeAnomalies.length} Unusual {activeAnomalies.length === 1 ? 'Charge' : 'Charges'} Flagged
              </div>
              <p className="text-xs text-rose-300/80 mt-0.5">
                We spotted higher than normal charges this month. Review them to prevent unexpected deductions.
              </p>
            </div>
          </div>
          <button 
            onClick={() => setPage('/analytics')}
            className="self-start sm:self-auto px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-xl transition-all cursor-pointer flex items-center space-x-1"
          >
            <span>Review Charges</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Charts & Activity Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Monthly Spending Breakdown Chart */}
        <div className="xl:col-span-2 bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Monthly Spending Breakdown</h2>
              <p className="text-xs text-mist mt-0.5">Spending trends across your top categories (INR)</p>
            </div>
            
            {/* Friendly Legend */}
            <div className="hidden sm:flex items-center space-x-3 text-xs text-mist">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /><span>Investment</span></span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /><span>Food</span></span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500" /><span>Shopping</span></span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500" /><span>Housing</span></span>
            </div>
          </div>

          <div className="h-64 w-full text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={spendingHistory}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.4} />
                <XAxis 
                  dataKey="name" 
                  stroke="#94A3B8" 
                  tickLine={false} 
                  axisLine={false}
                  dy={10}
                />
                <YAxis 
                  stroke="#94A3B8" 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => `₹${val/1000}K`}
                  dx={-10}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="Investment" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.2} />
                <Area type="monotone" dataKey="Food" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.2} />
                <Area type="monotone" dataKey="Shopping" stackId="1" stroke="#A855F7" fill="#A855F7" fillOpacity={0.2} />
                <Area type="monotone" dataKey="Housing" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Future Expense Estimate */}
        <div className="bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col justify-between shadow-lg shadow-black/20">
          <div>
            <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-3">
              <div>
                <h2 className="text-base font-semibold text-white">Upcoming Projections</h2>
                <p className="text-xs text-mist mt-0.5">Estimated next 30 to 90 days spend</p>
              </div>
              <Calendar className="w-5 h-5 text-blue-400" />
            </div>

            <p className="text-xs text-mist leading-relaxed mb-4">
              Estimated based on your historical bills, active subscriptions, and recurring lifestyle expenses.
            </p>

            <div className="space-y-3">
              {forecast.slice(0, 3).map((pt, idx) => (
                <div key={idx} className="bg-ink/60 border border-white/5 p-3 rounded-xl">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-mist font-medium">{pt.date}</span>
                    <span className="text-sm font-bold text-white tabular-nums">
                      {formatCurrency(pt.projected)}
                    </span>
                  </div>
                  
                  <div className="mt-2 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full w-2/3" />
                  </div>
                  
                  <div className="mt-1.5 flex justify-between text-[10px] text-slate-400">
                    <span>Expected Min: {formatCurrency(pt.confidenceMin)}</span>
                    <span>Max: {formatCurrency(pt.confidenceMax)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Synced with recurring bills</span>
            </span>
            <button 
              onClick={() => setPage('/analytics')}
              className="text-blue-400 hover:underline font-medium text-xs"
            >
              Details →
            </button>
          </div>
        </div>
      </div>

      {/* Recent Transactions List */}
      <div className="bg-slate-900 border border-white/10 p-5 rounded-2xl shadow-lg shadow-black/20">
        <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-3">
          <div>
            <h2 className="text-base font-semibold text-white">Recent Activity</h2>
            <p className="text-xs text-slate-400 mt-0.5">Your latest debit and credit transactions</p>
          </div>
          <button 
            onClick={() => setPage('/transactions')}
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center space-x-1"
          >
            <span>View All ({transactions.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentTransactions.length === 0 ? (
          <div className="py-8 text-center text-xs text-mist">
            No transactions found. Upload your bank statement to get started.
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {recentTransactions.map((tx) => (
              <div key={tx.id} className="py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                    tx.amount < 0 ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                  }`}>
                    {tx.amount < 0 ? '−' : '+'}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs sm:text-sm font-medium text-white truncate">
                      {tx.description}
                    </div>
                    <div className="text-[11px] text-mist">
                      {tx.date}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  <StampBadge 
                    id={tx.id}
                    category={tx.category}
                    isAnomaly={tx.isAnomaly}
                    status={tx.status}
                  />
                  <span className={`text-xs sm:text-sm font-bold tabular-nums ${
                    tx.amount < 0 ? 'text-rose-400' : 'text-emerald-400'
                  }`}>
                    {tx.amount < 0 ? `- ${formatCurrency(Math.abs(tx.amount))}` : `+ ${formatCurrency(tx.amount)}`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

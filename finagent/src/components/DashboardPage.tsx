/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { useFin } from '../FinContext';
import { StatCard } from './StatCard';
import { StampBadge } from './StampBadge';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from 'recharts';
import { Sparkles, ArrowRight, AlertCircle, TrendingUp, Compass, CalendarRange } from 'lucide-react';

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
    { name: 'Feb 26', Housing: 45000, Investment: 20000, Food: 15400, Utilities: 8200, Shopping: 12000, Others: 5000 },
    { name: 'Mar 26', Housing: 45000, Investment: 25000, Food: 14200, Utilities: 7900, Shopping: 8500, Others: 4800 },
    { name: 'Apr 26', Housing: 45000, Investment: 25000, Food: 16100, Utilities: 9100, Shopping: 14000, Others: 6100 },
    { name: 'May 26', Housing: 45000, Investment: 30000, Food: 13900, Utilities: 8500, Shopping: 11200, Others: 5400 },
    { name: 'Jun 26', Housing: 45000, Investment: 30000, Food: 15200, Utilities: 7600, Shopping: 9500, Others: 4900 },
    { name: 'Jul 26', Housing: 45000, Investment: 30000, Food: 13800, Utilities: 7399, Shopping: 15400, Others: 14147 },
  ];

  // Colors mapping strictly to design tokens
  const colors = {
    Housing: 'var(--text-secondary)',     // mist
    Investment: 'var(--accent-sage)',  // sage
    Food: 'var(--accent-gold)',        // gold
    Utilities: 'var(--text-secondary)',   // mist
    Shopping: 'var(--accent-coral)',    // coral
    Others: 'var(--bg-secondary)',      // ink-raised
  };

  // Simple Tooltip component matching the passbook feel
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-ink border-2 border-gold text-white p-3 font-mono text-xs shadow-2xl rounded-sm">
          <div className="font-bold border-b border-gold/15 pb-1 mb-2 text-[10px] uppercase tracking-wider text-gold">{label} Ledger Summary</div>
          {payload.map((item: any) => (
            <div key={item.name} className="flex justify-between space-x-6 py-0.5">
              <span className="text-mist">{item.name}:</span>
              <span className="font-bold tabular-nums">{formatCurrency(item.value)}</span>
            </div>
          ))}
          <div className="border-t border-gold/15 mt-2 pt-1 flex justify-between font-bold text-gold">
            <span>Total:</span>
            <span className="tabular-nums">
              {formatCurrency(payload.reduce((acc: number, item: any) => acc + item.value, 0))}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8 animate-[fadeIn_0.2s_ease-out]">
      
      {/* Top Banner Greetings */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gold/10 pb-6">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-gold font-bold">
            Autonomous Personal Ledger
          </div>
          <h2 className="text-3.5xl font-display font-medium text-white tracking-tight italic mt-1">
            Welcome, {user?.name || 'Siva Sudhamsh'}
          </h2>
        </div>

        {/* Weekly Digest Action Stamp */}
        <button 
          onClick={() => setPage('/chat')}
          className="flex items-center space-x-2.5 px-4.5 py-2 border border-gold/20 text-gold hover:text-white hover:border-gold/60 transition-all font-mono text-xs font-semibold rounded-sm cursor-pointer self-start md:self-auto bg-gold/5"
        >
          <Sparkles className="w-4 h-4" />
          <span>Examine Weekly AI Digest</span>
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard 
          id="kpi-balance"
          title="Consolidated Assets"
          value={summary.totalBalance}
          format="currency"
          trend={{ type: 'positive', label: '+₹1.85L Salary' }}
        />
        <StatCard 
          id="kpi-spend"
          title="Current Billing Cycle Spend"
          value={summary.thisMonthSpend}
          format="currency"
          trend={{ type: 'negative', label: '3 Flags Active' }}
        />
        <StatCard 
          id="kpi-savings"
          title="Passbook Savings Rate"
          value={summary.savingsRate}
          format="percentage"
          trend={{ type: 'positive', label: 'Target 50%+' }}
        />
        <StatCard 
          id="kpi-anomalies"
          title="Flagged Anomalies"
          value={summary.anomaliesCount}
          format="integer"
          trend={{ type: 'neutral', label: 'Requires Dispute' }}
        />
      </div>

      {/* Chart and Forecast Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Spending Chart */}
        <div className="xl:col-span-2 bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-gold/5 pb-4 mb-6">
            <div>
              <h3 className="font-display text-lg font-medium text-white">Savings & Spending Categories</h3>
              <p className="text-[10px] font-mono text-mist uppercase tracking-wider mt-0.5">Historical Monthly Outflow Matrix (INR)</p>
            </div>
            
            {/* Minimalist Legend Indicators */}
            <div className="hidden sm:flex items-center space-x-4 text-[10px] font-mono text-mist">
              <span className="flex items-center space-x-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors.Investment }} /><span>Investments</span></span>
              <span className="flex items-center space-x-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors.Food }} /><span>Food</span></span>
              <span className="flex items-center space-x-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors.Shopping }} /><span>Shopping</span></span>
            </div>
          </div>

          <div className="h-72 w-full text-xs font-mono">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={spendingHistory}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--accent-gold)" strokeOpacity={0.08} />
                <XAxis 
                  dataKey="name" 
                  stroke="var(--text-secondary)" 
                  tickLine={false} 
                  axisLine={false}
                  dy={10}
                />
                <YAxis 
                  stroke="var(--text-secondary)" 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => `₹${val/1000}K`}
                  dx={-10}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="Investment" stackId="1" stroke="var(--accent-sage)" fill="var(--accent-sage)" fillOpacity={0.15} />
                <Area type="monotone" dataKey="Food" stackId="1" stroke="var(--accent-gold)" fill="var(--accent-gold)" fillOpacity={0.15} />
                <Area type="monotone" dataKey="Shopping" stackId="1" stroke="var(--accent-coral)" fill="var(--accent-coral)" fillOpacity={0.1} />
                <Area type="monotone" dataKey="Housing" stackId="1" stroke="var(--text-secondary)" fill="var(--text-secondary)" fillOpacity={0.05} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ML Forecast Panel */}
        <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-gold/5 pb-4 mb-5">
              <div>
                <h3 className="font-display text-lg font-medium text-white">Machine Learning Forecast</h3>
                <p className="text-[10px] font-mono text-mist uppercase tracking-wider mt-0.5">30/60/90-Day Expenditure Projection</p>
              </div>
              <CalendarRange className="w-5 h-5 text-gold/60" />
            </div>

            <p className="text-xs text-mist leading-relaxed font-sans mb-6">
              Our auto-regression models project stable baseline outlays over the next 90 days, assuming your duplicate subscription disputes clear successfully.
            </p>

            {/* Confidence Band Stat list */}
            <div className="space-y-4">
              {forecast.map((pt, idx) => (
                <div key={idx} className="bg-ink/30 border border-gold/5 p-4 rounded-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-mist font-semibold">{pt.date}</span>
                    <span className="text-sm font-mono text-gold font-bold tabular-nums">
                      {formatCurrency(pt.projected)}
                    </span>
                  </div>
                  
                  {/* Progress Line representation of confidence interval */}
                  <div className="mt-2.5 h-1 w-full bg-ink rounded-full overflow-hidden relative">
                    <div className="absolute left-[20%] right-[20%] h-full bg-gold/30 rounded-full" />
                    <div className="absolute left-[45%] w-2 h-2 -top-0.5 bg-gold rounded-full" />
                  </div>
                  
                  <div className="mt-2 flex justify-between text-[9px] font-mono text-mist/50">
                    <span>95% Confidence Low: {formatCurrency(pt.confidenceMin)}</span>
                    <span>High: {formatCurrency(pt.confidenceMax)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 text-[9px] font-mono text-gold/40 flex items-center space-x-1.5 border-t border-gold/5 pt-4">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold animate-ping" />
            <span>ARIMA FORECAST CONFIDENCE: STATISTICAL SIGMA = 94.8%</span>
          </div>
        </div>
      </div>

      {/* Flagged Anomalies & Ledger Jump Footer */}
      <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gold/5 pb-4 mb-5 gap-3">
          <div className="flex items-center space-x-2.5">
            <AlertCircle className="w-5 h-5 text-coral" />
            <div>
              <h3 className="font-display text-lg font-medium text-white">Active Anomalies Flagged</h3>
              <p className="text-[10px] font-mono text-mist uppercase tracking-wider mt-0.5">High-confidence discrepancies needing attention</p>
            </div>
          </div>
          
          <button 
            onClick={() => setPage('/analytics')}
            className="text-[11px] font-mono text-gold hover:underline flex items-center space-x-1"
          >
            <span>Review Full Anomalies Panel</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {activeAnomalies.length === 0 ? (
          <div className="py-6 text-center text-xs font-mono text-mist/60 italic">
            No pending transaction anomalies. Your passbook ledger is verified stable.
          </div>
        ) : (
          <div className="space-y-3">
            {activeAnomalies.slice(0, 2).map((anom) => (
              <div 
                key={anom.id}
                className="flex flex-col md:flex-row md:items-center justify-between p-4 bg-ink/20 border border-coral/15 rounded-sm hover:border-coral/40 transition-all duration-200 gap-3"
              >
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                  <StampBadge 
                    id={anom.transactionId}
                    category="Others" // Arbitrary placeholder category, it'll display appropriately
                    isAnomaly={true}
                    status="AI-assigned"
                    interactive={false}
                  />
                  <div className="space-y-0.5">
                    <div className="text-xs font-mono font-bold text-white uppercase tracking-wide">
                      {anom.merchant} — <span className="tabular-nums text-coral">{formatCurrency(anom.amount)}</span>
                    </div>
                    <p className="text-[11px] text-mist leading-normal max-w-2xl font-sans">
                      {anom.explanation}
                    </p>
                  </div>
                </div>

                <button 
                  onClick={() => setPage('/chat')}
                  className="px-3.5 py-1.5 border border-gold/15 hover:border-gold/50 text-gold hover:text-white font-mono text-[10px] uppercase rounded-sm cursor-pointer whitespace-nowrap self-start md:self-auto"
                >
                  Draft Dispute
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

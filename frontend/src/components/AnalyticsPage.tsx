/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { useFin } from '../FinContext';
import { StampBadge } from './StampBadge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { AlertOctagon, HelpCircle, RefreshCw, Sparkles, Sliders, Receipt } from 'lucide-react';
import { apiFetch } from '../api';

export const AnalyticsPage: React.FC = () => {
  const { activeAnomalies, subscriptions, forecast } = useFin();
  const [activeTab, setActiveTab] = useState<'anomalies' | 'subscriptions' | 'whatif'>('anomalies');

  // What-if simulator state
  const [selectedCategory, setSelectedCategory] = useState<'Food' | 'Shopping' | 'Utilities'>('Food');
  const [reductionPercent, setReductionPercent] = useState<number>(30);
  const [simulatedForecast, setSimulatedForecast] = useState<any[]>([]);
  const [savedAmount, setSavedAmount] = useState<number>(0);
  const [categorySpend, setCategorySpend] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState(false);

  // Formatting utility for INR
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Math.abs(val));
  };

  // Run What-If simulation query
  const runSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await apiFetch(`/analytics/what-if?category=${selectedCategory}&reduction_pct=${reductionPercent}`);
      if (res.ok) {
        const data = await res.json();
        const monthlySavings = Number(data.monthly_savings || 0);
        setSimulatedForecast(forecast.map(item => ({ ...item, projected: Math.max(0, item.projected - monthlySavings) })));
        setSavedAmount(monthlySavings);
        setCategorySpend(Number(data.current_monthly_spend || 0));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [selectedCategory, reductionPercent]);

  // Merge actual forecast with simulated forecast for comparisons
  const comparisonChartData = forecast.map((f, i) => {
    const sim = simulatedForecast[i] || f;
    return {
      name: f.date,
      Baseline: f.projected,
      Optimized: sim.projected,
    };
  });

  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      <div className="border-b border-gold/10 pb-5">
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-gold font-bold">
          STATISTICAL LEDGER AUDIT
        </div>
        <h2 className="text-3.5xl font-display font-medium text-white tracking-tight italic mt-1">
          Analytics & Audits
        </h2>
      </div>

      {/* Passbook style horizontal tab strip */}
      <div className="border-b border-gold/15 flex space-x-8 text-sm font-mono tracking-wide">
        <button
          onClick={() => setActiveTab('anomalies')}
          className={`pb-3 border-b-2 transition-all font-medium cursor-pointer ${
            activeTab === 'anomalies' ? 'border-gold text-gold font-bold' : 'border-transparent text-mist hover:text-white'
          }`}
        >
          Ledger Anomalies ({activeAnomalies.length})
        </button>
        <button
          onClick={() => setActiveTab('subscriptions')}
          className={`pb-3 border-b-2 transition-all font-medium cursor-pointer ${
            activeTab === 'subscriptions' ? 'border-gold text-gold font-bold' : 'border-transparent text-mist hover:text-white'
          }`}
        >
          Subscription Audits ({subscriptions.length})
        </button>
        <button
          onClick={() => setActiveTab('whatif')}
          className={`pb-3 border-b-2 transition-all font-medium cursor-pointer ${
            activeTab === 'whatif' ? 'border-gold text-gold font-bold' : 'border-transparent text-mist hover:text-white'
          }`}
        >
          What-If Forecasting
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm">
            <h3 className="font-display text-lg text-white font-medium mb-1">Discrepancy Matrix</h3>
            <p className="text-xs text-mist leading-relaxed font-sans max-w-2xl">
              Anomalies are flagged by comparing incoming ledger item values with your historical standard deviation bounds. High-severity alerts should be disputed directly.
            </p>
          </div>

          {activeAnomalies.length === 0 ? (
            <div className="p-12 border border-gold/10 rounded-sm text-center font-mono text-mist/60 bg-ink-raised italic">
              Your accounts have zero pending anomaly concerns.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {activeAnomalies.map((anom) => {
                // Color grading for severity intensity
                const severityColors = {
                  Low: 'border-gold/30 text-gold bg-gold/5',
                  Medium: 'border-gold text-gold bg-gold/10',
                  High: 'border-coral/40 text-coral bg-coral/5',
                };
                
                return (
                  <div 
                    key={anom.id}
                    className="bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col md:flex-row md:items-start justify-between gap-5 hover:border-gold/30 transition-all"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="w-9 h-9 bg-ink rounded-sm flex items-center justify-center text-coral shrink-0 border border-gold/10">
                        <AlertOctagon className="w-5 h-5 text-coral" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-3 flex-wrap gap-y-1">
                          <span className="text-sm font-mono font-bold text-white">{anom.merchant}</span>
                          <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border ${severityColors[anom.severity]}`}>
                            {anom.severity} Severity
                          </span>
                        </div>
                        <div className="text-xs font-mono text-gold/80 font-bold tabular-nums">
                          Debit Amount: {formatCurrency(anom.amount)} • Date: {anom.date}
                        </div>
                        <p className="text-xs text-mist leading-relaxed font-sans max-w-3xl pt-1">
                          {anom.explanation}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2.5 shrink-0 self-end md:self-auto">
                      <button 
                        onClick={() => window.location.pathname = '/chat'} // Jump to chat
                        className="px-4 py-2 bg-gold/10 hover:bg-gold hover:text-ink text-gold border border-gold/20 font-mono text-xs font-bold rounded-sm transition-all cursor-pointer"
                      >
                        Draft AI Dispute Mail
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'subscriptions' && (
        <div className="space-y-6">
          <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm">
            <h3 className="font-display text-lg text-white font-medium mb-1">Ongoing Subscriptions Audit</h3>
            <p className="text-xs text-mist leading-relaxed font-sans max-w-2xl">
              We track recurring ledger cycles to calculate your **Subscription Creep Score**. Scores above 60 indicate unrecognized draft items or inactive memberships that should be cancelled.
            </p>
          </div>

          <div className="bg-paper text-ink-text border border-gold/10 rounded-sm overflow-hidden shadow-xl">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-ink/15 font-mono text-[10px] tracking-wider text-ink-text/50 bg-ink/[0.02]">
                  <th className="py-3.5 px-8 font-semibold uppercase">Merchant Provider</th>
                  <th className="py-3.5 px-8 font-semibold uppercase">Billing Cycle</th>
                  <th className="py-3.5 px-8 font-semibold uppercase text-right">Outflow Amount</th>
                  <th className="py-3.5 px-8 font-semibold uppercase">Next Draft Date</th>
                  <th className="py-3.5 px-8 font-semibold uppercase text-center w-52">Creep Score</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.map((sub) => {
                  // Color graded creep bars
                  const isHighCreep = sub.creepScore >= 60;
                  const barColor = isHighCreep ? 'bg-coral' : 'bg-gold';

                  return (
                    <tr key={sub.id} className="border-b border-ink/10 text-sm hover:bg-ink/[0.015]">
                      <td className="py-4.5 px-8 font-sans font-bold text-ink-text">
                        {sub.merchant}
                      </td>
                      <td className="py-4.5 px-8 font-mono text-xs text-ink-text/60">
                        {sub.cadence}
                      </td>
                      <td className="py-4.5 px-8 text-right font-mono font-bold text-coral tabular-nums">
                        {formatCurrency(sub.amount)}
                      </td>
                      <td className="py-4.5 px-8 font-mono text-xs text-ink-text/70">
                        {sub.nextChargeDate}
                      </td>
                      <td className="py-4.5 px-8 text-center">
                        <div className="flex items-center space-x-3.5 max-w-[150px] mx-auto">
                          {/* Horizontal creep score bar */}
                          <div className="h-2 flex-1 bg-ink/10 rounded-sm overflow-hidden border border-ink/5">
                            <div 
                              className={`h-full ${barColor}`}
                              style={{ width: `${sub.creepScore}%` }}
                            />
                          </div>
                          <span className={`text-[10px] font-mono font-bold tabular-nums ${isHighCreep ? 'text-coral' : 'text-gold'}`}>
                            {sub.creepScore}/100
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'whatif' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Simulator Form panel */}
          <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2.5 border-b border-gold/5 pb-4 mb-5">
                <Sliders className="w-5 h-5 text-gold" />
                <h3 className="font-display text-lg text-white font-medium">Outflow Simulator</h3>
              </div>

              <p className="text-xs text-mist leading-relaxed font-sans mb-6">
                Adjust the sliding constraints to test what-if scenarios. Shrinking variable outlays dynamically updates our forecast projection modules.
              </p>

              <div className="space-y-6 font-mono text-xs">
                {/* Category selection */}
                <div>
                  <label className="block text-[10px] text-mist uppercase tracking-wider mb-2">Target Outflow Category</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['Food', 'Shopping', 'Utilities'] as const).map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`py-2 px-3 text-center border font-mono rounded-sm text-xs transition-all cursor-pointer ${
                          selectedCategory === cat
                            ? 'border-gold text-gold bg-gold/5 font-semibold'
                            : 'border-gold/10 text-mist hover:text-white hover:border-gold/30'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Reduction Percentage Slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-[10px] text-mist uppercase">
                    <span>Reduction Constraints</span>
                    <span className="text-gold font-bold">{reductionPercent}% Cut</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={reductionPercent}
                    onChange={(e) => setReductionPercent(Number(e.target.value))}
                    className="w-full accent-gold bg-ink rounded-sm h-1.5 focus:outline-none focus:ring-0 cursor-pointer"
                  />
                  <div className="flex justify-between text-[8px] font-mono text-mist/40 uppercase">
                    <span>0% (As Is)</span>
                    <span>50% (Trimmed)</span>
                    <span>100% (Absolute Zero)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Impact details */}
            <div className="mt-8 pt-5 border-t border-gold/10 space-y-4">
              <div className="bg-ink/35 border border-gold/5 p-4 rounded-sm space-y-2 font-mono">
                <div className="flex justify-between text-xs text-mist">
                  <span>Current {selectedCategory} Outflow:</span>
                  <span className="text-white font-bold tabular-nums">{formatCurrency(categorySpend)}</span>
                </div>
                <div className="flex justify-between text-xs text-mist">
                  <span>Simulated Savings Rate:</span>
                  <span className="text-sage font-bold tabular-nums">+{formatCurrency(savedAmount)} / mo</span>
                </div>
                <div className="border-t border-gold/5 pt-2 flex justify-between text-xs">
                  <span className="text-gold font-bold">Optimized Monthly Surplus:</span>
                  <span className="text-gold font-bold tabular-nums">₹{savedAmount.toLocaleString('en-IN')}</span>
                </div>
              </div>

              <div className="text-[9px] font-mono text-mist/40 text-center leading-normal">
                SIMULATION CODES RUN DIRECTLY AGAINST MEMORY LEDGER REGISTER FOR TRIAL ESTIMATES.
              </div>
            </div>
          </div>

          {/* Shifting Line Chart visualization */}
          <div className="lg:col-span-2 bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-gold/5 pb-4 mb-6">
              <div>
                <h3 className="font-display text-lg font-medium text-white">Impact Analysis Matrix</h3>
                <p className="text-[10px] font-mono text-mist uppercase tracking-wider mt-0.5">Optimized vs Baseline Outflow Forecasting</p>
              </div>
              
              {/* Chart Legend */}
              <div className="flex items-center space-x-4 text-[10px] font-mono text-mist">
                <span className="flex items-center space-x-1"><span className="w-2.5 h-[1.5px] bg-mist" /><span>Baseline</span></span>
                <span className="flex items-center space-x-1"><span className="w-2.5 h-[1.5px] bg-gold" /><span>Simulated</span></span>
              </div>
            </div>

            <div className="h-72 w-full text-xs font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={comparisonChartData}
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
                  <Tooltip 
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-ink border border-gold text-white p-3 font-mono text-xs shadow-2xl rounded-sm">
                            <div className="font-bold text-gold border-b border-gold/15 pb-1 mb-2 text-[10px] uppercase tracking-wider">Forecast Delta</div>
                            <div className="flex justify-between space-x-4 py-0.5">
                              <span className="text-mist">Baseline:</span>
                              <span className="font-bold tabular-nums">{formatCurrency(payload[0].value)}</span>
                            </div>
                            <div className="flex justify-between space-x-4 py-0.5 text-gold">
                              <span>Optimized:</span>
                              <span className="font-bold tabular-nums">{formatCurrency(payload[1].value)}</span>
                            </div>
                            <div className="border-t border-gold/15 mt-2 pt-1 flex justify-between text-sage font-bold text-[10px] uppercase">
                              <span>Saved Surplus:</span>
                              <span className="tabular-nums">₹{(payload[0].value - payload[1].value).toLocaleString('en-IN')}</span>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="Baseline" 
                    stroke="var(--text-secondary)" 
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="Optimized" 
                    stroke="var(--accent-gold)" 
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: 'var(--accent-gold)' }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-5 text-[9px] font-mono text-mist/50 italic border-t border-gold/5 pt-4">
              * SIMULATION RUNS HYPOTHETICAL CODES — BASE BALANCES AND PAST MONTH TRANSACTIONS IN THE LEDGER REMAIN UNTOUCHED.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

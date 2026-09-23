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
      {/* Header */}
      <div className="border-b border-white/5 pb-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          Spending Insights & Analytics
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Detect unusual expenses, manage monthly recurring bills, and simulate how much you can save.
        </p>
      </div>

      {/* Modern navigation pill tabs */}
      <div className="flex space-x-2 border-b border-white/10 pb-3">
        <button
          onClick={() => setActiveTab('anomalies')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
            activeTab === 'anomalies'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <AlertOctagon className="w-4 h-4" />
          <span>Unusual Charges</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${activeTab === 'anomalies' ? 'bg-blue-700 text-white' : 'bg-slate-800 text-slate-300'}`}>
            {activeAnomalies.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('subscriptions')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
            activeTab === 'subscriptions'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Receipt className="w-4 h-4" />
          <span>Recurring Subscriptions</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${activeTab === 'subscriptions' ? 'bg-blue-700 text-white' : 'bg-slate-800 text-slate-300'}`}>
            {subscriptions.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('whatif')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
            activeTab === 'whatif'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Savings Simulator</span>
        </button>
      </div>

      {/* Tab 1: Unusual Charges */}
      {activeTab === 'anomalies' && (
        <div className="space-y-4">
          <div className="bg-ink-raised border border-white/10 p-5 rounded-2xl flex items-start justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">Smart Anomaly Detection</h3>
              <p className="text-sm text-mist mt-1 max-w-2xl leading-relaxed">
                MYFI monitors your usual spending patterns. If a transaction is unexpectedly high or out of the ordinary, it's flagged here so you can review or dispute it.
              </p>
            </div>
          </div>

          {activeAnomalies.length === 0 ? (
            <div className="p-12 border border-white/10 rounded-2xl text-center text-mist bg-ink-raised">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="text-white font-medium">All Clear! No unusual expenses found</div>
              <p className="text-xs text-mist mt-1">All your recent transactions align with your normal spending patterns.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3.5">
              {activeAnomalies.map((anom) => {
                const severityBadge = {
                  Low: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                  Medium: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
                  High: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
                };
                
                return (
                  <div 
                    key={anom.id}
                    className="bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col md:flex-row md:items-start justify-between gap-4 hover:border-white/20 transition-all"
                  >
                    <div className="flex items-start space-x-3.5">
                      <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertOctagon className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2.5 flex-wrap">
                          <span className="text-sm font-semibold text-white">{anom.merchant}</span>
                          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${severityBadge[anom.severity] || severityBadge.Medium}`}>
                            {anom.severity} Alert
                          </span>
                        </div>
                        <div className="text-xs text-mist flex items-center space-x-3">
                          <span className="font-mono font-medium text-rose-400">{formatCurrency(anom.amount)}</span>
                          <span>•</span>
                          <span>Date: {anom.date}</span>
                        </div>
                        <p className="text-xs text-mist leading-relaxed pt-1">
                          {anom.explanation}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0 self-end md:self-center">
                      <button 
                        onClick={() => window.location.pathname = '/chat'}
                        className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-xl transition-all cursor-pointer flex items-center space-x-1.5 shadow-md shadow-blue-600/20"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Ask AI Assistant</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Recurring Subscriptions */}
      {activeTab === 'subscriptions' && (
        <div className="space-y-4">
          <div className="bg-ink-raised border border-white/10 p-5 rounded-2xl">
            <h3 className="text-base font-semibold text-white">Active Subscriptions & Recurring Bills</h3>
            <p className="text-sm text-mist mt-1 max-w-2xl leading-relaxed">
              These recurring charges were automatically identified from your bank statements (e.g. Netflix, Prime, gym memberships, SIPs). Review them regularly to cancel unused services.
            </p>
          </div>

          <div className="bg-ink-raised border border-white/10 rounded-2xl overflow-hidden shadow-xl">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-xs font-semibold uppercase tracking-wider text-mist bg-ink/30">
                  <th className="py-3 px-5">Service / Provider</th>
                  <th className="py-3 px-5">Frequency</th>
                  <th className="py-3 px-5 text-right">Amount</th>
                  <th className="py-3 px-5">Next Expected Charge</th>
                  <th className="py-3 px-5 text-center">Renewal Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {subscriptions.map((sub) => {
                  const isHighCreep = sub.creepScore >= 60;

                  return (
                    <tr key={sub.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-5 font-medium text-white flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
                          {sub.merchant.charAt(0)}
                        </div>
                        <span>{sub.merchant}</span>
                      </td>
                      <td className="py-3.5 px-5 text-mist text-xs capitalize">
                        {sub.cadence}
                      </td>
                      <td className="py-3.5 px-5 text-right font-mono font-medium text-rose-400">
                        {formatCurrency(sub.amount)}
                      </td>
                      <td className="py-3.5 px-5 text-mist text-xs">
                        {sub.nextChargeDate}
                      </td>
                      <td className="py-3.5 px-5 text-center">
                        <div className="flex items-center space-x-2 max-w-[130px] mx-auto">
                          <div className="h-1.5 flex-1 bg-ink rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${isHighCreep ? 'bg-rose-500' : 'bg-emerald-500'}`}
                              style={{ width: `${sub.creepScore}%` }}
                            />
                          </div>
                          <span className={`text-xs font-mono font-medium ${isHighCreep ? 'text-rose-400' : 'text-mist'}`}>
                            {sub.creepScore}%
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

      {/* Tab 3: What-If Savings Simulator */}
      {activeTab === 'whatif' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          
          {/* Controls Panel */}
          <div className="bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2.5 pb-4 border-b border-white/10 mb-5">
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Sliders className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Savings Simulator</h3>
                  <p className="text-xs text-mist">Test how much you can save</p>
                </div>
              </div>

              <p className="text-xs text-mist leading-relaxed mb-5">
                Choose an expense category and slide to adjust how much you'd like to cut. See the instant impact on your monthly savings!
              </p>

              <div className="space-y-5 text-sm">
                {/* Category selection */}
                <div>
                  <label className="block text-xs font-medium text-mist mb-2">Select Category</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['Food', 'Shopping', 'Utilities'] as const).map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`py-2 px-3 text-center rounded-xl text-xs font-medium transition-all cursor-pointer ${
                          selectedCategory === cat
                            ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25'
                            : 'border border-white/10 text-mist hover:text-white hover:bg-white/5'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Reduction Percentage Slider */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-mist font-medium">Reduction Target:</span>
                    <span className="text-blue-400 font-bold">{reductionPercent}% Less</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={reductionPercent}
                    onChange={(e) => setReductionPercent(Number(e.target.value))}
                    className="w-full accent-blue-500 bg-ink rounded-lg h-2 cursor-pointer"
                  />
                  <div className="flex justify-between text-[11px] text-mist/70">
                    <span>0% (No change)</span>
                    <span>50% (Moderate)</span>
                    <span>100% (Strict)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Impact Summary Box */}
            <div className="mt-6 pt-4 border-t border-white/10 space-y-3">
              <div className="bg-ink border border-white/10 p-4 rounded-xl space-y-2.5 text-xs">
                <div className="flex justify-between text-mist">
                  <span>Current {selectedCategory} Spending:</span>
                  <span className="text-white font-mono font-medium">{formatCurrency(categorySpend)}/mo</span>
                </div>
                <div className="flex justify-between text-emerald-400 font-medium">
                  <span>Potential Monthly Savings:</span>
                  <span className="font-mono font-bold">+{formatCurrency(savedAmount)}</span>
                </div>
                <div className="border-t border-white/5 pt-2 flex justify-between text-blue-300 font-semibold">
                  <span>Estimated Annual Savings:</span>
                  <span className="font-mono font-bold">₹{(savedAmount * 12).toLocaleString('en-IN')}</span>
                </div>
              </div>

              <p className="text-[11px] text-mist/70 text-center">
                This is a simulation to help your financial planning. Your actual accounts are untouched.
              </p>
            </div>
          </div>

          {/* Forecast Comparison Chart */}
          <div className="lg:col-span-2 bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Projected Outflow Comparison</h3>
                <p className="text-xs text-mist mt-0.5">Current trajectory vs. after your simulated savings</p>
              </div>
              
              {/* Chart Legend */}
              <div className="flex items-center space-x-4 text-xs">
                <span className="flex items-center space-x-1.5 text-mist">
                  <span className="w-2.5 h-0.5 bg-slate-500" />
                  <span>Current Path</span>
                </span>
                <span className="flex items-center space-x-1.5 text-emerald-400 font-medium">
                  <span className="w-2.5 h-0.5 bg-emerald-500" />
                  <span>With Savings</span>
                </span>
              </div>
            </div>

            <div className="h-72 w-full text-xs font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={comparisonChartData}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.4} />
                  <XAxis 
                    dataKey="name" 
                    stroke="#94a3b8" 
                    tickLine={false} 
                    axisLine={false}
                    dy={10}
                  />
                  <YAxis 
                    stroke="#94a3b8" 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(val) => `₹${val/1000}K`}
                    dx={-10}
                  />
                  <Tooltip 
                    content={({ active, payload }: any) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-ink-raised border border-white/10 text-white p-3 rounded-xl shadow-xl text-xs space-y-1">
                            <div className="font-semibold text-mist border-b border-white/10 pb-1 mb-1">
                              Forecast Comparison
                            </div>
                            <div className="flex justify-between space-x-4 text-mist">
                              <span>Current:</span>
                              <span className="font-mono font-medium text-white">{formatCurrency(payload[0].value)}</span>
                            </div>
                            <div className="flex justify-between space-x-4 text-emerald-400">
                              <span>Optimized:</span>
                              <span className="font-mono font-medium">{formatCurrency(payload[1].value)}</span>
                            </div>
                            <div className="border-t border-white/10 pt-1 flex justify-between text-emerald-400 font-semibold">
                              <span>Monthly Saved:</span>
                              <span className="font-mono">₹{(payload[0].value - payload[1].value).toLocaleString('en-IN')}</span>
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
                    stroke="#64748b" 
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="Optimized" 
                    stroke="#10b981" 
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#10b981' }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 text-xs text-mist border-t border-white/10 pt-3">
              Projections update dynamically as you adjust the slider above.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

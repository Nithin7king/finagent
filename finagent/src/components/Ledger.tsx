/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef } from 'react';
import { useFin } from '../FinContext';
import { Transaction, Category } from '../types';
import { StampBadge } from './StampBadge';
import { Search, Upload, CheckCircle2, AlertCircle, Sparkles, Filter, X } from 'lucide-react';

export const Ledger: React.FC = () => {
  const { transactions, uploadCSV, commitCSV, currentPage, setPage } = useFin();
  
  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  
  // CSV Import State
  const [csvFileContent, setCsvFileContent] = useState<string>('');
  const [csvPreview, setCsvPreview] = useState<Transaction[] | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Formatting utility for INR
  const formatCurrency = (val: number) => {
    const formatted = new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Math.abs(val));
    return val < 0 ? `- ${formatted}` : `+ ${formatted}`;
  };

  const formatBalance = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Run filtering logic
  const filteredTransactions = transactions.filter(t => {
    const matchesSearch = t.description.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          t.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || t.category === selectedCategory;
    const matchesMin = minAmount === '' || Math.abs(t.amount) >= Number(minAmount);
    const matchesMax = maxAmount === '' || Math.abs(t.amount) <= Number(maxAmount);
    
    return matchesSearch && matchesCategory && matchesMin && matchesMax;
  }).sort((a, b) => b.date.localeCompare(a.date)); // descending dates

  // CSV file drag & drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setImportError(null);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setImportError(null);
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const processFile = (file: File) => {
    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
      setImportError('Please upload a standard .csv statement file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = await uploadCSV(text);
        setCsvPreview(parsed);
      } catch (err: any) {
        setImportError(err.message || 'Failed to parse CSV statement.');
      }
    };
    reader.readAsText(file);
  };

  // Adjust preview transaction category
  const handlePreviewCategoryChange = (tempId: string, newCat: Category) => {
    if (!csvPreview) return;
    setCsvPreview(prev => 
      prev ? prev.map(t => t.id === tempId ? { ...t, category: newCat, status: 'user-corrected' } : t) : null
    );
  };

  const handleCommitUpload = async () => {
    if (!csvPreview) return;
    try {
      await commitCSV(csvPreview);
      setCsvPreview(null);
    } catch (err: any) {
      setImportError(err.message || 'Commit failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* CSV Pre-commit Preview Modal */}
      {csvPreview && (
        <div className="fixed inset-0 bg-ink/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-paper border-2 border-gold text-ink-text w-full max-w-4xl max-h-[85vh] flex flex-col rounded-sm shadow-2xl overflow-hidden animate-[fadeIn_0.2s_ease-out]">
            {/* Header */}
            <div className="p-6 bg-ink-raised border-b border-gold/20 text-white flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Sparkles className="w-5 h-5 text-gold" />
                <h3 className="text-lg font-display tracking-tight text-white font-medium">Verify AI-Categorized Entry Points</h3>
              </div>
              <button 
                onClick={() => setCsvPreview(null)}
                className="text-mist hover:text-white p-1 rounded-sm"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Preview List */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <p className="text-xs text-ink-text/70 leading-relaxed max-w-2xl font-sans">
                Below are the transactions parsed from your statement. Our ML engine has pre-classified each merchant. Review categories or click on any stamp badge to override assignments before locking them.
              </p>

              <div className="border border-ink/10 rounded-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-ink/5 border-b border-ink/10 font-mono text-[10px] tracking-wider text-ink-text/60">
                      <th className="py-2.5 px-4 font-semibold uppercase">Date</th>
                      <th className="py-2.5 px-4 font-semibold uppercase">Description / Merchant</th>
                      <th className="py-2.5 px-4 font-semibold uppercase text-right">Amount</th>
                      <th className="py-2.5 px-4 font-semibold uppercase text-center">Engine Stamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {csvPreview.map((tx) => (
                      <tr key={tx.id} className="border-b border-ink/5 hover:bg-ink/5 text-xs">
                        <td className="py-3 px-4 font-mono text-ink-text/80">{tx.date}</td>
                        <td className="py-3 px-4 font-medium">{tx.description}</td>
                        <td className={`py-3 px-4 text-right font-mono font-bold tabular-nums ${
                          tx.amount < 0 ? 'text-coral' : 'text-sage'
                        }`}>
                          {formatCurrency(tx.amount)}
                        </td>
                        <td className="py-2 px-4 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <StampBadge 
                              id={tx.id} 
                              category={tx.category} 
                              isAnomaly={tx.isAnomaly} 
                              status={tx.status} 
                              interactive={false} // Disable global context save, use local adjustment below
                            />
                            {/* Simple Selector for pre-commit overrides */}
                            <select 
                              value={tx.category}
                              onChange={(e) => handlePreviewCategoryChange(tx.id, e.target.value as Category)}
                              className="text-[10px] bg-white border border-ink/10 text-ink-text rounded-sm px-1.5 py-0.5 font-mono focus:ring-1 focus:ring-gold"
                            >
                              {['Salary', 'Investment', 'Housing', 'Food', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Others'].map(c => (
                                <option key={c} value={c}>{c}</option>
                              ))}
                            </select>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer actions */}
            <div className="p-4 bg-ink/5 border-t border-ink/10 flex items-center justify-end space-x-3">
              <button 
                onClick={() => setCsvPreview(null)}
                className="px-4 py-2 text-xs font-mono border border-ink/20 text-ink-text/80 hover:bg-ink/10 transition-colors font-medium rounded-sm"
              >
                Discard Import
              </button>
              <button 
                onClick={handleCommitUpload}
                className="px-5 py-2 text-xs font-mono bg-gold text-ink font-bold hover:brightness-110 transition-all flex items-center space-x-2 rounded-sm"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Lock into Ledger ({csvPreview.length} Entries)</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Slim Toolbar */}
      <div className="bg-ink-raised border border-gold/10 p-4 rounded-sm flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Filter inputs */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search bar */}
          <div className="relative w-full sm:w-60">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-mist" />
            <input
              type="text"
              placeholder="Search merchant or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-ink border border-gold/15 text-white pl-9 pr-4 py-1.5 text-xs rounded-sm focus:border-gold placeholder:text-mist/50 font-mono"
            />
          </div>

          {/* Category Dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono text-mist uppercase">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-ink border border-gold/15 text-white text-xs font-mono rounded-sm px-2.5 py-1.5 focus:border-gold"
            >
              <option value="ALL">All Entries</option>
              {['Salary', 'Investment', 'Housing', 'Food', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Others'].map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Amount Filters */}
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono text-mist uppercase">Min:</span>
            <input
              type="number"
              placeholder="₹0"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              className="w-16 bg-ink border border-gold/15 text-white py-1 px-2 text-xs font-mono rounded-sm focus:border-gold placeholder:text-mist/30"
            />
            <span className="text-[10px] font-mono text-mist uppercase">Max:</span>
            <input
              type="number"
              placeholder="₹"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              className="w-20 bg-ink border border-gold/15 text-white py-1 px-2 text-xs font-mono rounded-sm focus:border-gold placeholder:text-mist/30"
            />
          </div>

          {(searchTerm || selectedCategory !== 'ALL' || minAmount || maxAmount) && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedCategory('ALL');
                setMinAmount('');
                setMaxAmount('');
              }}
              className="text-coral hover:underline text-[10px] font-mono flex items-center space-x-1"
            >
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Drag-and-drop CSV box */}
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed p-3 rounded-sm flex items-center space-x-3 cursor-pointer text-left transition-all ${
            isDragging 
              ? 'border-gold bg-gold/5 text-gold' 
              : 'border-gold/15 bg-ink/20 text-mist hover:border-gold/30 hover:text-white'
          }`}
        >
          <Upload className="w-5 h-5 text-gold flex-shrink-0" />
          <div>
            <div className="text-[10px] font-mono font-semibold uppercase tracking-wide">
              Import Statement (CSV)
            </div>
            <div className="text-[9px] font-sans text-mist/70 mt-0.5">
              Drag-and-drop or click to browse
            </div>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv"
            className="hidden"
          />
        </div>
      </div>

      {/* Import Error Message */}
      {importError && (
        <div className="p-3.5 bg-coral/5 border border-coral/20 rounded-sm text-coral text-xs font-mono flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 text-coral" />
          <span>{importError}</span>
        </div>
      )}

      {/* The Signature Passbook Page */}
      <div className="bg-paper text-ink-text border border-gold/10 rounded-sm overflow-hidden shadow-xl animate-[fadeIn_0.3s_ease-out]">
        
        {/* Passbook Header Stamp */}
        <div className="px-8 py-6 border-b border-ink/15 bg-ink/[0.01] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono tracking-[0.25em] text-gold font-bold uppercase">
              FINANCIAL LEDGER
            </div>
            <h2 className="text-xl font-display text-ink-text mt-1 font-semibold italic">
              Savings Passbook
            </h2>
          </div>
          
          {/* Stamps ledger descriptor */}
          <div className="flex items-center space-x-6 text-[10px] font-mono text-ink-text/50">
            <div>
              <span className="text-ink-text/70 uppercase">MIME TYPE:</span> <span className="text-gold font-bold">LEDGER/INR</span>
            </div>
            <div>
              <span className="text-ink-text/70 uppercase">ENTRIES:</span> <span className="font-bold">{filteredTransactions.length}</span>
            </div>
          </div>
        </div>

        {/* Ledger table */}
        {filteredTransactions.length === 0 ? (
          <div className="p-16 text-center space-y-4">
            <div className="text-ink-text/40 text-4xl font-display italic">No records written</div>
            <p className="text-xs text-ink-text/60 max-w-sm mx-auto leading-relaxed">
              No transactions yet — upload a statement or connect an account to get started. Use the CSV portal above to populate entries instantly.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-ink/15 font-mono text-[10px] tracking-wider text-ink-text/50 bg-ink/[0.02]">
                  <th className="py-3.5 px-8 font-semibold uppercase">Booking Date</th>
                  <th className="py-3.5 px-8 font-semibold uppercase">Particulars / Details</th>
                  <th className="py-3.5 px-8 font-semibold uppercase">Classification Stamp</th>
                  <th className="py-3.5 px-8 font-semibold uppercase text-right">Debit / Credit</th>
                  <th className="py-3.5 px-8 font-semibold uppercase text-right">Running Balance</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((tx) => (
                  <tr 
                    key={tx.id} 
                    className="border-b border-ink/10 hover:bg-ink/[0.015] transition-colors group text-sm"
                  >
                    {/* Booking Date */}
                    <td className="py-4.5 px-8 font-mono text-xs text-ink-text/80 whitespace-nowrap">
                      {tx.date}
                    </td>
                    
                    {/* Particulars */}
                    <td className="py-4.5 px-8 font-medium font-sans">
                      <div className="flex flex-col">
                        <span>{tx.description}</span>
                        {tx.isAnomaly && (
                          <span className="text-[10px] font-mono text-coral font-semibold uppercase mt-0.5 tracking-wider animate-pulse">
                            ● flagged anomaly
                          </span>
                        )}
                      </div>
                    </td>
                    
                    {/* Classification Stamp */}
                    <td className="py-4.5 px-8">
                      <StampBadge 
                        id={tx.id}
                        category={tx.category}
                        isAnomaly={tx.isAnomaly}
                        status={tx.status}
                      />
                    </td>
                    
                    {/* Amount (Debit / Credit) */}
                    <td className={`py-4.5 px-8 text-right font-mono font-bold tabular-nums whitespace-nowrap ${
                      tx.amount < 0 ? 'text-coral' : 'text-sage'
                    }`}>
                      {formatCurrency(tx.amount)}
                    </td>
                    
                    {/* Running Balance */}
                    <td className="py-4.5 px-8 text-right font-mono font-bold text-ink-text/70 tabular-nums whitespace-nowrap">
                      {formatBalance(tx.balanceAfter)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Passbook Footer */}
        <div className="px-8 py-5 border-t border-ink/15 bg-ink/[0.01] text-[9px] font-mono text-ink-text/40 flex items-center justify-between">
          <span>* INDICATES TRANSACTION CONVERTED VIA SECURE ML AUTOMATION</span>
          <span>PAGE OUT OF 1</span>
        </div>
      </div>
    </div>
  );
};

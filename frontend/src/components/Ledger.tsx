/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef } from 'react';
import { useFin } from '../FinContext';
import { Transaction, Category } from '../types';
import { StampBadge } from './StampBadge';
import { Search, Upload, CheckCircle2, AlertCircle, Sparkles, Filter, X, Lock, Eye, EyeOff, Loader2, FileText, Cpu, ShieldCheck, Download, FileSpreadsheet } from 'lucide-react';

export const Ledger: React.FC = () => {
  const { transactions, uploadCSV, uploadPDF, commitCSV, currentPage, setPage } = useFin();
  
  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<'ALL' | 'EXPENSE' | 'INCOME'>('ALL');
  const [minAmount, setMinAmount] = useState<string>('');
  const [maxAmount, setMaxAmount] = useState<string>('');
  
  // Statement Import State (CSV & PDF)
  const [csvPreview, setCsvPreview] = useState<Transaction[] | null>(null);
  const [tierInfo, setTierInfo] = useState<{ tier: number | null; name: string | null; warnings: string[] } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [parsingMessage, setParsingMessage] = useState<string>('');
  
  // Password Decryption State (Indian Bank Statements)
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [pendingPdfFile, setPendingPdfFile] = useState<File | null>(null);
  const [pdfPassword, setPdfPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [pdfPasswordError, setPdfPasswordError] = useState<string | null>(null);
  
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
    const matchesType = typeFilter === 'ALL' || (typeFilter === 'EXPENSE' ? t.amount < 0 : t.amount > 0);
    const matchesMin = minAmount === '' || Math.abs(t.amount) >= Number(minAmount);
    const matchesMax = maxAmount === '' || Math.abs(t.amount) <= Number(maxAmount);
    
    return matchesSearch && matchesCategory && matchesType && matchesMin && matchesMax;
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
    const isCsv = file.name.toLowerCase().endsWith('.csv') || file.type === 'text/csv';
    const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';

    if (!isCsv && !isPdf) {
      setImportError('Please upload an Indian bank statement in PDF or CSV format.');
      return;
    }

    if (isCsv) {
      setTierInfo({ tier: 1, name: 'CSV Direct Reader', warnings: [] });
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
    } else {
      executePdfUpload(file);
    }
  };

  const executePdfUpload = async (file: File, password?: string) => {
    setIsParsing(true);
    setParsingMessage(password ? 'Decrypting statement & parsing tables...' : 'Analyzing statement (Tier 1 Table -> Tier 2 LLM -> Tier 3 OCR)...');
    setImportError(null);
    setPdfPasswordError(null);

    try {
      const res = await uploadPDF(file, password);
      if (res.requires_password) {
        setPendingPdfFile(file);
        setIsPasswordModalOpen(true);
        if (password) {
          setPdfPasswordError('Incorrect password. Please verify your bank statement password.');
        }
        return;
      }

      setIsPasswordModalOpen(false);
      setPendingPdfFile(null);
      setPdfPassword('');
      setTierInfo({
        tier: res.tier_used ?? null,
        name: res.tier_name ?? null,
        warnings: res.warnings || [],
      });
      setCsvPreview(res.transactions);
    } catch (err: any) {
      setImportError(err.message || 'Failed to parse PDF statement.');
    } finally {
      setIsParsing(false);
      setParsingMessage('');
    }
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pendingPdfFile) return;
    if (!pdfPassword.trim()) {
      setPdfPasswordError('Please enter the statement password.');
      return;
    }
    executePdfUpload(pendingPdfFile, pdfPassword.trim());
  };

  const handleCancelPasswordModal = () => {
    setIsPasswordModalOpen(false);
    setPendingPdfFile(null);
    setPdfPassword('');
    setPdfPasswordError(null);
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
      setTierInfo(null);
    } catch (err: any) {
      setImportError(err.message || 'Commit failed.');
    }
  };

  const handleDiscard = () => {
    setCsvPreview(null);
    setTierInfo(null);
  };

  return (
    <div className="space-y-6">
      {/* Statement Pre-commit Preview Modal */}
      {csvPreview && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-ink-raised border border-white/15 text-white w-full max-w-4xl max-h-[85vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden animate-[fadeIn_0.2s_ease-out]">
            {/* Header */}
            <div className="p-5 bg-ink/70 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Review Extracted Transactions</h3>
                  <p className="text-xs text-mist">Verify entries and categories before adding to your account</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {/* Extraction Tier Badge */}
                {tierInfo?.tier === 1 && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5" />
                    <span>Tier 1: Table Extraction</span>
                  </span>
                )}
                {tierInfo?.tier === 2 && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Tier 2: AI-Assisted</span>
                  </span>
                )}
                {tierInfo?.tier === 3 && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center space-x-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Tier 3: OCR Scanned</span>
                  </span>
                )}

                <button 
                  onClick={handleDiscard}
                  className="text-mist hover:text-white p-1 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Preview List */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {tierInfo?.warnings && tierInfo.warnings.length > 0 && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs space-y-1">
                  <div className="font-semibold flex items-center space-x-1.5">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>Extraction Note</span>
                  </div>
                  {tierInfo.warnings.map((w, idx) => (
                    <div key={idx} className="text-xs text-amber-200/80 pl-5">{w}</div>
                  ))}
                </div>
              )}

              <p className="text-xs text-mist leading-relaxed">
                Found <strong>{csvPreview.length}</strong> transactions in your statement. Our AI has auto-categorized each entry. You can adjust any category using the dropdown before saving.
              </p>

              <div className="border border-white/10 rounded-xl overflow-hidden bg-ink/40">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-ink/80 border-b border-white/10 text-xs text-mist">
                      <th className="py-3 px-4 font-semibold">Date</th>
                      <th className="py-3 px-4 font-semibold">Description</th>
                      <th className="py-3 px-4 font-semibold text-right">Amount</th>
                      <th className="py-3 px-4 font-semibold text-center">Category</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {csvPreview.map((tx) => (
                      <tr key={tx.id} className="hover:bg-white/5 text-xs transition-colors">
                        <td className="py-3 px-4 text-mist whitespace-nowrap">{tx.date}</td>
                        <td className="py-3 px-4 font-medium text-white">{tx.description}</td>
                        <td className={`py-3 px-4 text-right font-bold tabular-nums whitespace-nowrap ${
                          tx.amount < 0 ? 'text-rose-400' : 'text-emerald-400'
                        }`}>
                          {formatCurrency(tx.amount)}
                        </td>
                        <td className="py-2.5 px-4 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <StampBadge 
                              id={tx.id} 
                              category={tx.category} 
                              isAnomaly={tx.isAnomaly} 
                              status={tx.status} 
                              interactive={false}
                            />
                            <select 
                              value={tx.category}
                              onChange={(e) => handlePreviewCategoryChange(tx.id, e.target.value as Category)}
                              className="text-xs bg-ink-raised border border-white/15 text-white rounded-lg px-2 py-1 focus:ring-1 focus:ring-blue-500"
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
            <div className="p-4 bg-ink/70 border-t border-white/10 flex items-center justify-end space-x-3">
              <button 
                onClick={handleDiscard}
                className="px-4 py-2 text-xs border border-white/15 text-mist hover:text-white hover:bg-white/5 transition-colors font-medium rounded-xl"
              >
                Discard
              </button>
              <button 
                onClick={handleCommitUpload}
                className="px-5 py-2 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-md shadow-emerald-600/30 transition-all flex items-center space-x-2 rounded-xl cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Save {csvPreview.length} Transactions to Account</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Indian Bank Statement Password Decryption Modal (Tier 0) */}
      {isPasswordModalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-ink-raised border border-white/15 text-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-[fadeIn_0.2s_ease-out]">
            <div className="p-5 bg-ink/70 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                  <Lock className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Encrypted Bank Statement</h3>
                  <p className="text-[11px] text-mist">Password required to open this PDF</p>
                </div>
              </div>
              <button 
                onClick={handleCancelPasswordModal}
                disabled={isParsing}
                className="text-mist hover:text-white p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handlePasswordSubmit} className="p-5 space-y-4">
              <p className="text-xs text-mist leading-relaxed">
                Indian banks send password-protected statements to protect your privacy. Enter the password below:
              </p>

              {/* Bank password pattern guide */}
              <div className="p-3 bg-ink/50 border border-white/10 rounded-xl text-xs text-mist space-y-1">
                <div className="font-semibold text-white text-[11px] mb-1">Common Bank Formats:</div>
                <div>• <strong className="text-white">SBI:</strong> Last 5 digits of A/C + DOB (DDMMYYYY)</div>
                <div>• <strong className="text-white">HDFC:</strong> Customer ID or PAN + DOB (DDMMYYYY)</div>
                <div>• <strong className="text-white">ICICI:</strong> First 4 letters of Name + DOB (DDMM)</div>
                <div>• <strong className="text-white">Axis / Kotak:</strong> PAN (uppercase) or DOB</div>
              </div>

              {pdfPasswordError && (
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{pdfPasswordError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs text-mist font-medium mb-1">
                  Statement Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={pdfPassword}
                    onChange={(e) => {
                      setPdfPassword(e.target.value);
                      setPdfPasswordError(null);
                    }}
                    placeholder="Enter password (e.g. PAN + DOB)"
                    disabled={isParsing}
                    autoFocus
                    className="w-full bg-ink border border-white/15 text-white pl-3.5 pr-10 py-2.5 text-xs rounded-xl focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-mist hover:text-white p-1"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={handleCancelPasswordModal}
                  disabled={isParsing}
                  className="px-4 py-2 text-xs border border-white/15 text-mist hover:text-white rounded-xl transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isParsing}
                  className="px-5 py-2 text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-md shadow-blue-600/30 transition-all flex items-center space-x-2 disabled:opacity-50 cursor-pointer"
                >
                  {isParsing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Decrypting...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      <span>Decrypt & Open</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Parsing Progress Overlay */}
      {isParsing && !isPasswordModalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-ink-raised border border-white/15 p-6 rounded-2xl shadow-2xl text-center max-w-sm w-full space-y-4 animate-[fadeIn_0.2s_ease-out]">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white">Extracting Transactions</h4>
              <p className="text-xs text-mist mt-1 leading-relaxed">
                {parsingMessage || 'Analyzing bank statement tables and extracting transactions...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Upload Toolbar */}
      <div className="bg-ink-raised border border-white/10 p-4 rounded-2xl flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-lg shadow-black/20">
        
        {/* Left: Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search bar */}
          <div className="relative w-full sm:w-60">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-mist" />
            <input
              type="text"
              placeholder="Search merchant or category..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-ink border border-white/10 text-white pl-9 pr-4 py-2 text-xs rounded-xl focus:border-blue-500 placeholder:text-mist/60"
            />
          </div>

          {/* Type Toggle: All / Expenses / Income */}
          <div className="flex items-center bg-ink p-1 rounded-xl border border-white/10 text-xs">
            <button
              onClick={() => setTypeFilter('ALL')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                typeFilter === 'ALL' ? 'bg-blue-600 text-white shadow-sm' : 'text-mist hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setTypeFilter('EXPENSE')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                typeFilter === 'EXPENSE' ? 'bg-rose-600 text-white shadow-sm' : 'text-mist hover:text-white'
              }`}
            >
              Expenses
            </button>
            <button
              onClick={() => setTypeFilter('INCOME')}
              className={`px-3 py-1 rounded-lg font-medium transition-all ${
                typeFilter === 'INCOME' ? 'bg-emerald-600 text-white shadow-sm' : 'text-mist hover:text-white'
              }`}
            >
              Income
            </button>
          </div>

          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-ink border border-white/10 text-white text-xs rounded-xl px-3 py-2 focus:border-blue-500"
          >
            <option value="ALL">All Categories</option>
            {['Salary', 'Investment', 'Housing', 'Food', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Others'].map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Reset Filters Button */}
          {(searchTerm || selectedCategory !== 'ALL' || typeFilter !== 'ALL' || minAmount || maxAmount) && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedCategory('ALL');
                setTypeFilter('ALL');
                setMinAmount('');
                setMaxAmount('');
              }}
              className="text-xs text-rose-400 hover:underline font-medium"
            >
              Reset
            </button>
          )}
        </div>

        {/* Right: Upload Box */}
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed p-3 rounded-xl flex items-center space-x-3 cursor-pointer transition-all ${
            isDragging 
              ? 'border-blue-500 bg-blue-500/10 text-blue-400' 
              : 'border-white/15 bg-ink/50 text-mist hover:border-blue-500/50 hover:text-white'
          }`}
        >
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center flex-shrink-0">
            <Upload className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">
              Upload Bank Statement
            </div>
            <div className="text-[11px] text-mist">
              PDF (SBI, HDFC, ICICI, Axis) or CSV
            </div>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.csv"
            className="hidden"
          />
        </div>
      </div>

      {/* Import Error Message */}
      {importError && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{importError}</span>
        </div>
      )}

      {/* Modern Account Statement Card */}
      <div className="bg-ink-raised border border-white/10 rounded-2xl overflow-hidden shadow-xl">
        
        {/* Header Bar */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h2 className="text-base font-semibold text-white">
              Account Statement
            </h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
              {filteredTransactions.length} entries
            </span>
          </div>

          <a 
            href="/api/transactions/export" 
            target="_blank" 
            rel="noreferrer"
            className="text-xs text-mist hover:text-white flex items-center space-x-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
        </div>

        {/* Transactions Table */}
        {filteredTransactions.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-white/5 mx-auto flex items-center justify-center text-mist">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div className="text-sm font-semibold text-white">No transactions found</div>
            <p className="text-xs text-mist max-w-sm mx-auto">
              No transactions match your current filters. Upload a statement or reset your search above.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-xs font-semibold text-mist bg-ink/40">
                  <th className="py-3 px-6">Date</th>
                  <th className="py-3 px-6">Description / Merchant</th>
                  <th className="py-3 px-6">Category</th>
                  <th className="py-3 px-6 text-right">Amount</th>
                  <th className="py-3 px-6 text-right">Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredTransactions.map((tx) => (
                  <tr 
                    key={tx.id} 
                    className="hover:bg-white/[0.02] transition-colors text-xs sm:text-sm"
                  >
                    {/* Date */}
                    <td className="py-3.5 px-6 text-xs text-mist whitespace-nowrap">
                      {tx.date}
                    </td>
                    
                    {/* Particulars */}
                    <td className="py-3.5 px-6 font-medium text-white">
                      <div className="flex flex-col">
                        <span>{tx.description}</span>
                        {tx.isAnomaly && (
                          <span className="text-[10px] text-rose-400 font-semibold mt-0.5">
                            ● Flagged unusual spend
                          </span>
                        )}
                      </div>
                    </td>
                    
                    {/* Category Stamp */}
                    <td className="py-3.5 px-6">
                      <StampBadge 
                        id={tx.id}
                        category={tx.category}
                        isAnomaly={tx.isAnomaly}
                        status={tx.status}
                      />
                    </td>
                    
                    {/* Amount */}
                    <td className={`py-3.5 px-6 text-right font-bold tabular-nums whitespace-nowrap ${
                      tx.amount < 0 ? 'text-rose-400' : 'text-emerald-400'
                    }`}>
                      {tx.amount < 0 ? `- ${formatCurrency(Math.abs(tx.amount))}` : `+ ${formatCurrency(tx.amount)}`}
                    </td>
                    
                    {/* Running Balance */}
                    <td className="py-3.5 px-6 text-right font-medium text-white/80 tabular-nums whitespace-nowrap">
                      {formatBalance(tx.balanceAfter)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

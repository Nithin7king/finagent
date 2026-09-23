/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Ledger } from './Ledger';

export const TransactionsPage: React.FC = () => {
  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      <div className="pb-1">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Transactions & Statements
        </h1>
        <p className="text-xs sm:text-sm text-mist mt-0.5">
          View all account debits and credits, search merchants, or upload your bank statement (PDF or CSV).
        </p>
      </div>

      {/* The main Ledger element */}
      <Ledger />
    </div>
  );
};

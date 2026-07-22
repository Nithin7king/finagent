/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Ledger } from './Ledger';

export const TransactionsPage: React.FC = () => {
  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      <div className="border-b border-gold/10 pb-5">
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-gold font-bold">
          CONSOLIDATED SAVINGS LEDGER
        </div>
        <h2 className="text-3.5xl font-display font-medium text-white tracking-tight italic mt-1">
          Historical Passbook
        </h2>
      </div>

      {/* The main Ledger element */}
      <Ledger />
    </div>
  );
};

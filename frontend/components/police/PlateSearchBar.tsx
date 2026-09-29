'use client';

import React, { useState } from 'react';
import { Search, CheckCircle2, RotateCcw } from 'lucide-react';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { normalizePlate } from '@/lib/utils';

export function PlateSearchBar() {
  const {
    searchQuery,
    isExactMatch,
    isSearching,
    setSearchQuery,
    setIsExactMatch,
    searchPlates,
    clearSelection,
  } = useVehicleStore();

  const [inputVal, setInputVal] = useState(searchQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    setSearchQuery(inputVal.trim());
    searchPlates(inputVal.trim());
  };

  const handleReset = () => {
    setInputVal('');
    clearSelection();
  };

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] p-3 shadow-gov-sm">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-3">
        {/* Search Input Box */}
        <div className="relative flex-1 w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value.toUpperCase())}
            placeholder="ENTER VEHICLE REGISTRATION (E.G. HR26CX9021, DL01AB1234)..."
            className="w-full pl-9 pr-4 py-2 bg-tint border border-border-warm rounded-[3px] text-navy-950 font-mono text-sm uppercase placeholder:normal-case placeholder:text-slate-400 tracking-wider focus:outline-none focus:border-navy-900 focus:bg-surface transition-colors"
          />
        </div>

        {/* Exact Match Toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none px-2 py-1.5 rounded hover:bg-tint border border-transparent hover:border-border-warm transition-colors">
          <input
            type="checkbox"
            checked={isExactMatch}
            onChange={(e) => setIsExactMatch(e.target.checked)}
            className="w-4 h-4 accent-saffron-600 rounded cursor-pointer"
          />
          <span className="font-heading uppercase tracking-wider text-xs font-semibold text-slate-700">
            Exact Match Only
          </span>
        </label>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            type="submit"
            disabled={isSearching}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2 bg-navy-900 hover:bg-navy-950 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider shadow-sm transition-colors disabled:opacity-50"
          >
            {isSearching ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>SEARCHING...</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5 text-saffron-500" />
                <span>EXECUTE ANPR QUERY</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleReset}
            className="p-2 text-slate-400 hover:text-navy-900 hover:bg-tint border border-border-warm rounded-[3px] transition-colors"
            title="Reset query"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

import React from 'react';
import { Bell, Search, Info } from 'lucide-react';

const Topbar = () => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
      <div className="flex items-center w-96">
        <div className="relative w-full">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3">
            <Search size={18} className="text-slate-400" />
          </span>
          <input
            type="text"
            placeholder="Search tasks, nodes, or metrics..."
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-slate-50"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <button className="text-slate-400 hover:text-slate-600 transition-colors">
          <Info size={20} />
        </button>
        <button className="relative text-slate-400 hover:text-slate-600 transition-colors">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </button>
        <div className="h-8 w-px bg-slate-200"></div>
        <div className="flex items-center">
          <span className="text-sm font-medium text-slate-700 mr-2">C2011-01 Nursing Home</span>
          <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-md">Planning</span>
        </div>
      </div>
    </header>
  );
};

export default Topbar;

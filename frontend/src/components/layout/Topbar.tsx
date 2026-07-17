import React from 'react';
import { Bell, Search, Info } from 'lucide-react';

const Topbar = () => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
      <div className="flex items-center w-96">
        {/* Placeholder for future search or breadcrumbs */}
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
          {/* Dynamic project info can be added here later */}
        </div>
      </div>
    </header>
  );
};

export default Topbar;

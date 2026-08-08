import React from 'react';
import { Sliders, Zap, CheckCircle } from 'lucide-react';

export const SelectionTab = ({
  glpoTargetDate,
  setGlpoTargetDate,
  glpoTargetHour,
  setGlpoTargetHour,
  glpoPenaltyPerDay,
  setGlpoPenaltyPerDay,
  glpoBonusPerDay,
  setGlpoBonusPerDay,
  glpoMcIterations,
  setGlpoMcIterations,
  glpoParetoCount,
  setGlpoParetoCount,
  glpoParetoSort,
  setGlpoParetoSort,
  handleRunAI,
  isGlpoLoading,
  projectData
}: any) => {
  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-black text-slate-800">GLPO Optimization Configuration</h2>
        <p className="text-sm text-slate-500 mt-2">Set financial and time parameters for AI to find the optimal schedule for your project.</p>
      </div>

      <div className="bg-white border border-indigo-100 rounded-2xl shadow-sm overflow-hidden bg-gradient-to-br from-indigo-50/50 to-white">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 text-indigo-700 rounded-lg">
              <Sliders size={20} />
            </div>
            <h3 className="font-extrabold text-slate-800">Input Parameters</h3>
          </div>
          <span className="text-xs text-indigo-700 font-bold bg-indigo-100 px-3 py-1 rounded-full">
            HGT 3-Node + Hybrid Readout
          </span>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <h4 className="font-bold text-sm text-slate-700 border-b pb-2">1. Time Constraints (Deadline)</h4>
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1.5">Target Deadline</label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={glpoTargetDate}
                  onChange={e => setGlpoTargetDate(e.target.value)}
                  className="w-3/5 border border-slate-300 rounded-xl px-3 py-2.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                />
                <select
                  value={glpoTargetHour}
                  onChange={e => setGlpoTargetHour(e.target.value)}
                  className="w-2/5 border border-slate-300 rounded-xl px-3 py-2.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition bg-white"
                >
                  {Array.from({ length: 24 }, (_, i) => {
                    const h = i < 10 ? `0${i}` : `${i}`;
                    return <option key={h} value={`${h}:00`}>{h}:00</option>;
                  })}
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <h4 className="font-bold text-sm text-slate-700 border-b pb-2">2. Financial Constraints</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Delay Penalty ($/day)</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold">$</span>
                  <input
                    type="number" step="50" min="0"
                    value={glpoPenaltyPerDay}
                    onChange={e => setGlpoPenaltyPerDay(Number(e.target.value))}
                    className="w-full border border-rose-200 rounded-xl pl-7 pr-3 py-2.5 text-sm font-bold text-rose-700 focus:ring-2 focus:ring-rose-500 focus:border-rose-500 outline-none transition bg-rose-50/30"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Early Finish Bonus ($/day)</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold">$</span>
                  <input
                    type="number" step="50" min="0"
                    value={glpoBonusPerDay}
                    onChange={e => setGlpoBonusPerDay(Number(e.target.value))}
                    className="w-full border border-emerald-200 rounded-xl pl-7 pr-3 py-2.5 text-sm font-bold text-emerald-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition bg-emerald-50/30"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-2 space-y-6">
            <h4 className="font-bold text-sm text-slate-700 border-b pb-2">3. Algorithm Configuration</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Monte Carlo Iterations</label>
                <input
                  type="number" step="100" min="100"
                  value={glpoMcIterations}
                  onChange={e => setGlpoMcIterations(Math.max(1, Number(e.target.value)))}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 outline-none transition"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Max Pareto Options</label>
                <input
                  type="number" step="1" min="1" max="50"
                  value={glpoParetoCount}
                  onChange={e => setGlpoParetoCount(Math.max(1, Number(e.target.value)))}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 outline-none transition"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">Optimization Goal (Sort By)</label>
                <select
                  value={glpoParetoSort}
                  onChange={e => setGlpoParetoSort(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm font-semibold bg-white focus:ring-2 focus:ring-indigo-500 outline-none transition"
                >
                  <option value="makespan_hours">Minimize Makespan</option>
                  <option value="total_cost">Minimize Net Cost</option>
                  <option value="risk_score">Minimize Risk</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-center">
          <button
            onClick={handleRunAI}
            disabled={isGlpoLoading || projectData?.status === 'Simulating'}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-8 py-3.5 rounded-xl text-base font-black shadow-lg shadow-indigo-200 transition-all transform hover:-translate-y-1 active:translate-y-0 flex items-center justify-center w-full max-w-sm"
          >
            {isGlpoLoading || projectData?.status === 'Simulating' ? (
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ANALYZING...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Zap size={20} />
                RUN AI PIPELINE
              </div>
            )}
          </button>
        </div>
      </div>
      
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start gap-3 shadow-sm">
        <CheckCircle className="text-emerald-600 shrink-0 mt-0.5" size={20} />
        <div>
          <h4 className="font-bold text-emerald-800 text-sm">Instructions</h4>
          <p className="text-xs text-emerald-700 mt-1">
            Sau khi điều chỉnh các thông số phạt/thưởng và bấm "Chạy AI", hệ thống sẽ tự động tổng hợp dữ liệu, 
            sử dụng mô hình HGT 3-Node để dự báo và tối ưu hóa bằng giải thuật OR.
            Quá trình này mất khoảng vài giây đến vài phút tùy theo quy mô dự án.
          </p>
        </div>
      </div>
    </div>
  );
};

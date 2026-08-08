import React from 'react';
import { Activity, Sparkles, Zap } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Line, Legend } from 'recharts';

export const EvaluationTab = ({
  allParetoOptions,
  paretoChartType,
  setParetoChartType,
  paretoBarData,
  selectedGlpoOptionIndex,
  setSelectedGlpoOptionIndex,
  isGlpoLoading,
  isApplyingOption,
  handleRestoreBaseline,
  handleApplyParetoOption,
  handleRunAI
}: any) => {
  return (
    <div className="space-y-6 animate-fadeIn mb-8">
      {/* Pareto Frontier Scatter / Bar Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
          <div>
            <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-2">
              <Sparkles className="text-amber-500" size={18} />
              Pareto Frontier Chart (Makespan vs Net Cost)
            </h3>
            <p className="text-xs text-slate-500">Each point represents an optimal solution. Click a point to select.</p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <div className="bg-slate-100 p-1 rounded-lg flex gap-1">
              <button
                onClick={() => setParetoChartType('scatter')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition ${paretoChartType === 'scatter' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
              >
                📈 Pareto Chart
              </button>
              <button
                onClick={() => setParetoChartType('bar')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition ${paretoChartType === 'bar' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
              >
                📊 Comparison Bar Chart
              </button>
            </div>
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
              {allParetoOptions.length} PA
            </span>
          </div>
        </div>

        {allParetoOptions.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              {paretoChartType === 'scatter' ? (
                <ScatterChart margin={{ top: 20, right: 30, bottom: 35, left: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    type="number"
                    dataKey="makespan_hours"
                    name="Makespan"
                    unit="h"
                    stroke="#94a3b8"
                    fontSize={11}
                    domain={['dataMin - 15', 'dataMax + 15']}
                    tickFormatter={(v) => `${v}h`}
                  />
                  <YAxis
                    type="number"
                    dataKey="total_cost"
                    name="Cost"
                    unit="$"
                    stroke="#94a3b8"
                    fontSize={11}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                    domain={['dataMin - 3000', 'dataMax + 3000']}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const d = payload[0].payload;
                        return (
                          <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1 border border-slate-700">
                            <p className="font-bold text-amber-400">{d.option_name}</p>
                            <p>Makespan: <span className="font-bold text-indigo-300">{d.makespan_hours}h</span></p>
                            <p>Cost gốc: <span className="text-slate-300">${Number(d.base_project_cost || d.cost || 0).toLocaleString()}</span></p>
                            <p>Cost ròng: <span className="font-bold text-emerald-400">${Number(d.total_cost || d.cost || 0).toLocaleString()}</span></p>
                            <p>Delay Risk: <span className="font-bold text-rose-400">{d.risk_pct}%</span></p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter
                    name="Pareto Trade-off"
                    data={allParetoOptions}
                    fill="#4f46e5"
                    line={{ stroke: '#6366f1', strokeWidth: 2, strokeDasharray: '3 3' }}
                    onClick={(point: any) => {
                      if (!point) return;
                      const idx = allParetoOptions.findIndex((x: any) => x.option_name === point.option_name || x.makespan_hours === point.makespan_hours);
                      if (idx !== -1) setSelectedGlpoOptionIndex(idx);
                    }}
                  />
                </ScatterChart>
              ) : (
                <ComposedChart data={paretoBarData} margin={{ top: 20, right: 30, bottom: 40, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} angle={-25} textAnchor="end" height={50} />
                  <YAxis yAxisId="cost" orientation="left" tickFormatter={(v) => `$${v}k`} stroke="#4f46e5" fontSize={11} domain={['dataMin - 10', 'dataMax + 10']} />
                  <YAxis yAxisId="time" orientation="right" tickFormatter={(v) => `${Math.round(v / 8)}d`} stroke="#059669" fontSize={11} domain={['dataMin - 50', 'dataMax + 50']} />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(value: any, name: string) => {
                      if (name === 'cost') return [`$${(Number(value) * 1000).toLocaleString()}`, 'Cost Ròng'];
                      if (name === 'makespan') return [`${Math.round(Number(value) / 8)} ngày (${value}h)`, 'Makespan'];
                      return [`${value}%`, 'Rủi ro'];
                    }}
                  />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                  <Bar yAxisId="cost" dataKey="cost" name="cost" fill="#818cf8" radius={[4, 4, 0, 0]} barSize={18} />
                  <Line yAxisId="time" type="monotone" dataKey="makespan" name="makespan" stroke="#10b981" strokeWidth={3} dot={{ r: 3 }} />
                </ComposedChart>
              )}
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-400">
            <Activity size={36} className="mx-auto mb-2 opacity-40" />
            <p className="text-sm font-semibold">No Pareto chart data available.</p>
            <p className="text-xs mt-1">Switch to "Selection" tab and click "Run AI" to generate solutions.</p>
          </div>
        )}
      </div>

      {/* Pareto Comparison Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center flex-wrap gap-2">
          <h3 className="font-extrabold text-slate-800 text-sm">Detailed Pareto Solutions Table</h3>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRestoreBaseline}
              disabled={isApplyingOption}
              className="bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-sm"
              title="Restore original project baseline"
            >
              🔄 Restore Original Baseline
            </button>
            <span className="text-xs text-slate-500 font-medium">Click "Apply Solution" to apply to Database</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="text-slate-600 bg-slate-100 uppercase font-bold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">STT</th>
                <th className="px-4 py-3">Solution Name</th>
                <th className="px-4 py-3 text-right">Makespan</th>
                <th className="px-4 py-3 text-right">Completion Date</th>
                <th className="px-4 py-3 text-right">Cost Gốc ($)</th>
                <th className="px-4 py-3 text-right">Bonus / Penalty ($)</th>
                <th className="px-4 py-3 text-right">Cost Ròng ($)</th>
                <th className="px-4 py-3 text-right">Delay Risk</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {allParetoOptions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-400">
                    No optimal solutions generated. Please run AI to generate.
                  </td>
                </tr>
              ) : (
                allParetoOptions.map((opt: any, idx: number) => {
                  const isSelected = selectedGlpoOptionIndex === idx;
                  const baseCost = opt.base_project_cost || opt.cost || 0;
                  const penCost = opt.penalty_cost || 0;
                  const bonusAmt = opt.bonus_amount || 0;
                  const netCost = opt.total_cost || opt.cost || 0;
                  const riskPct = opt.risk_pct !== undefined ? opt.risk_pct : (opt.risk ? opt.risk * 100 : 0);

                  let adjustStr = "$0";
                  let adjustClass = "text-slate-500";
                  if (penCost > 0) {
                    adjustStr = `+$${Number(penCost).toLocaleString()} (Penalty)`;
                    adjustClass = "text-rose-600 font-bold";
                  } else if (bonusAmt > 0) {
                    adjustStr = `-$${Number(bonusAmt).toLocaleString()} (Bonus)`;
                    adjustClass = "text-emerald-600 font-bold";
                  }

                  return (
                    <tr
                      key={idx}
                      className={`border-b border-slate-100 transition ${isSelected ? 'bg-indigo-50/70 font-semibold border-l-4 border-l-indigo-600' : 'hover:bg-slate-50'}`}
                    >
                      <td className="px-4 py-3 font-bold text-slate-500">#{idx + 1}</td>
                      <td className="px-4 py-3 font-bold text-slate-800">{opt.option_name || `Solution ${idx + 1}`}</td>
                      <td className="px-4 py-3 text-right font-black text-indigo-600">
                        {opt.makespan_hours || opt.makespan}h
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600">{opt.finish_datetime ? new Date(opt.finish_datetime).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}</td>
                      <td className="px-4 py-3 text-right text-slate-600">${Number(baseCost).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                      <td className={`px-4 py-3 text-right ${adjustClass}`}>{adjustStr}</td>
                      <td className="px-4 py-3 text-right font-extrabold text-emerald-600">${Number(netCost).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                      <td className="px-4 py-3 text-right font-bold text-rose-500">{Number(riskPct).toFixed(1)}%</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-2 justify-center w-max mx-auto">
                          <button
                            onClick={() => setSelectedGlpoOptionIndex(idx)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition shadow-sm border flex items-center justify-center gap-1 ${isSelected ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                          >
                            {isSelected ? '👁️ Previewing' : 'Preview'}
                          </button>
                          <button
                            onClick={() => handleApplyParetoOption(idx, opt)}
                            disabled={isApplyingOption}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition shadow-sm flex items-center justify-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white w-full`}
                          >
                            💾 Save Solution
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

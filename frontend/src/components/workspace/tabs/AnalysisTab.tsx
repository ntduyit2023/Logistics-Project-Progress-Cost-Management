import React from 'react';
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar, Area, Line, AreaChart, BarChart } from 'recharts';

export const AnalysisTab = ({ combinedData, bellCurveData, optionCost }: any) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
      {/* Financial S-Curve */}
      <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[450px] flex flex-col">
        <div className="mb-4 shrink-0 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-slate-800">Financial S-Curve & Task Density</h3>
            <p className="text-xs text-slate-500">Cumulative cost and parallel task density are updated automatically</p>
          </div>
          <div className="text-right text-xs bg-emerald-50 px-2 py-1 border border-emerald-100 rounded text-emerald-700 font-bold">
            TGC: ${Number(optionCost || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={combinedData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="date" tickFormatter={(tick) => `${tick.split('-')[2]}/${tick.split('-')[1]}`} minTickGap={25} stroke="#94a3b8" fontSize={11} />
              <YAxis yAxisId="cost" orientation="left" tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} stroke="#3b82f6" fontSize={11} />
              <YAxis yAxisId="density" orientation="right" tickFormatter={(val) => `${val}`} stroke="#10b981" fontSize={11} />
              <Tooltip formatter={(value: any, name: any) => {
                if (name === 'dailyCost') return [`$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Daily Cost'];
                if (name === 'cumulativeCost') return [`$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Cumulative Cost'];
                return [`${value} tasks`, 'Parallel Tasks'];
              }} labelFormatter={(label) => `Day: ${label}`} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
              <Bar yAxisId="cost" dataKey="dailyCost" name="dailyCost" fill="#cbd5e1" barSize={14} radius={[2, 2, 0, 0]} />
              <Area yAxisId="cost" type="monotone" dataKey="cumulativeCost" name="cumulativeCost" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCumulative)" />
              <Line yAxisId="density" type="monotone" dataKey="activeCount" name="activeCount" stroke="#10b981" strokeWidth={2.5} dot={{ r: 2.5, fill: '#10b981' }} activeDot={{ r: 5 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monte Carlo Risk Analysis */}
      <div className="lg:col-span-1 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[450px] flex flex-col">
        <div className="mb-4 shrink-0">
          <h3 className="font-bold text-slate-800">Monte Carlo Risk Analysis</h3>
          <p className="text-xs text-slate-500">Probability distribution of completion time (Hours)</p>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={bellCurveData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorBell" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="days" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}h`} />
              <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                formatter={(val: any) => [`${Number(val).toFixed(1)}%`, 'Probability Density']}
                labelFormatter={(val) => `Duration: ${val}h (${(Number(val) / 8).toFixed(1)} ngày)`}
              />
              <Area type="monotone" dataKey="probability" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorBell)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Task Distribution Chart */}
      <div className="lg:col-span-3 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[300px] flex flex-col">
        <div className="mb-4 shrink-0">
          <h3 className="font-bold text-slate-800">Task Allocation Chart</h3>
          <p className="text-xs text-slate-500">Density of parallel tasks by project day</p>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={combinedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="date" tickFormatter={(tick) => `${tick.split('-')[2]}/${tick.split('-')[1]}`} stroke="#94a3b8" fontSize={11} minTickGap={20} />
              <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                formatter={(val: any) => [`${val} tasks`, 'In Progress']}
                labelFormatter={(val) => `Day: ${val.split('-')[2]}/${val.split('-')[1]}`}
                cursor={{ fill: 'transparent' }}
              />
              <Bar dataKey="activeCount" fill="#0ea5e9" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

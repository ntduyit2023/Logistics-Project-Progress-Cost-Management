import React from 'react';
import { ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Legend, Tooltip, ScatterChart, Scatter, ZAxis } from 'recharts';

interface ParetoMetricsChartProps {
  paretoOptions: any[];
  paretoChartType: 'scatter' | 'bar';
}

const ParetoMetricsChart: React.FC<ParetoMetricsChartProps> = ({ paretoOptions, paretoChartType }) => {
  const paretoBarData = paretoOptions.map((opt: any, idx: number) => ({
    name: `PA [${idx + 1}]`,
    cost: Math.round((opt.total_cost || opt.cost || 0) / 1000), // Convert to k
    makespan: Math.round(opt.makespan_hours || opt.time || 0)
  }));

  const scatterData = paretoOptions.map((opt: any, idx: number) => ({
    name: `PA [${idx + 1}]`,
    x: Math.round(opt.makespan_hours || opt.time || 0),
    y: Math.round((opt.total_cost || opt.cost || 0) / 1000),
    z: 100,
    option_name: opt.option_name || `Phuong an ${idx + 1}`,
    finish_datetime: opt.finish_datetime,
    base_project_cost: opt.base_project_cost,
    total_cost: opt.total_cost
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      {paretoChartType === 'scatter' ? (
        <ScatterChart margin={{ top: 20, right: 30, bottom: 35, left: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Makespan (h)" 
            unit="h" 
            domain={['dataMin - 50', 'dataMax + 50']} 
            stroke="#94a3b8" 
            fontSize={11} 
            label={{ value: 'Thoi gian hoan thanh (gio)', position: 'bottom', fill: '#64748b', fontSize: 12 }} 
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Total Cost ($k)" 
            unit="k" 
            domain={['dataMin - 10', 'dataMax + 10']} 
            stroke="#94a3b8" 
            fontSize={11} 
            label={{ value: 'Tong chi phi ($k)', angle: -90, position: 'left', fill: '#64748b', fontSize: 12 }} 
          />
          <ZAxis type="number" dataKey="z" range={[60, 60]} />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }} 
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload;
                return (
                  <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl text-xs space-y-1 border border-slate-700">
                    <p className="font-bold text-amber-400">{d.option_name}</p>
                    <p>Thoi gian: <span className="font-bold text-indigo-300">{d.x}h</span> (Den ngay: {d.finish_datetime || 'N/A'})</p>
                    <p>Chi phi goc: <span className="text-slate-300">${Number(d.base_project_cost || 0).toLocaleString()}</span></p>
                    <p>Chi phi rong: <span className="font-bold text-emerald-400">${Number(d.total_cost || 0).toLocaleString()}</span></p>
                  </div>
                );
              }
              return null;
            }} 
          />
          <Scatter name="Pareto Front" data={scatterData} fill="#8b5cf6" line={{ stroke: '#c4b5fd', strokeWidth: 1 }} />
        </ScatterChart>
      ) : (
        <ComposedChart data={paretoBarData} margin={{ top: 20, right: 30, bottom: 40, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} angle={-25} textAnchor="end" height={50} />
          <YAxis yAxisId="cost" orientation="left" tickFormatter={(v) => `$${v}k`} stroke="#4f46e5" fontSize={11} domain={['dataMin - 10', 'dataMax + 10']} />
          <YAxis yAxisId="time" orientation="right" tickFormatter={(v) => `${v}h`} stroke="#10b981" fontSize={11} domain={['dataMin - 50', 'dataMax + 50']} />
          <Tooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-slate-900 text-white p-2 rounded shadow-lg text-xs border border-slate-700">
                    <p className="font-bold text-amber-400">{label}</p>
                    <p>Chi phi: ${payload[0].value}k</p>
                    <p>Thoi gian: {payload[1].value}h</p>
                  </div>
                );
              }
              return null;
            }} 
          />
          <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
          <Bar yAxisId="cost" dataKey="cost" name="cost" fill="#818cf8" radius={[4, 4, 0, 0]} barSize={18} />
          <Line yAxisId="time" type="monotone" dataKey="makespan" name="makespan" stroke="#10b981" strokeWidth={3} dot={{ r: 3 }} />
        </ComposedChart>
      )}
    </ResponsiveContainer>
  );
};

export default ParetoMetricsChart;

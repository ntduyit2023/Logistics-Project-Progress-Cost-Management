import React from 'react';
import { Layers, Activity, GitCommit, Clock } from 'lucide-react';
import mockData from '../mocks/project_583.json';

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center">
    <div className={`p-4 rounded-lg mr-4 ${color}`}>
      <Icon size={24} className="text-white" />
    </div>
    <div>
      <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
    </div>
  </div>
);

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend } from 'recharts';

const Dashboard = () => {
  const { project_name, status, num_tasks, num_edges, network_density, tasks } = mockData.data;

  // Tính toán Cash Flow từng THÁNG dựa trên các Task lá
  const generateMonthlyCashFlowData = () => {
    const leafTasks = tasks.filter((t: any) => {
      return !tasks.some((other: any) => other.wbs.startsWith(`${t.wbs}.`));
    });

    const monthlyData: Record<string, number> = {};

    leafTasks.forEach((task: any) => {
      const startStr = task.time_info?.baseline_start;
      const duration = Math.max(1, Math.ceil(task.time_info?.duration || 0));
      const totalCost = task.cost_info?.total_cost || 0;
      
      if (!startStr || totalCost === 0) return;
      
      const startMs = new Date(startStr).getTime();
      const dailyCost = totalCost / duration;
      
      for (let i = 0; i < duration; i++) {
        const d = new Date(startMs + i * 24 * 60 * 60 * 1000);
        // Gom nhóm theo tháng (VD: 2012-03)
        const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        monthlyData[monthStr] = (monthlyData[monthStr] || 0) + dailyCost;
      }
    });

    const sortedMonths = Object.keys(monthlyData).sort();
    let cumulative = 0;
    return sortedMonths.map(month => {
      cumulative += monthlyData[month];
      return {
        month,
        monthlyCost: monthlyData[month],
        cumulativeCost: cumulative
      };
    });
  };

  const cashFlowData = generateMonthlyCashFlowData();

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex justify-between items-end shrink-0">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Project Analytics</h2>
          <p className="text-sm text-slate-500">{project_name}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 shrink-0">
        <StatCard 
          title="Total Tasks" 
          value={num_tasks} 
          icon={Layers} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Dependencies" 
          value={num_edges} 
          icon={GitCommit} 
          color="bg-emerald-500" 
        />
        <StatCard 
          title="Network Density" 
          value={network_density.toFixed(4)} 
          icon={Activity} 
          color="bg-amber-500" 
        />
        <StatCard 
          title="Project Status" 
          value={status} 
          icon={Clock} 
          color="bg-purple-500" 
        />
      </div>

      {/* Cash Flow Chart */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex-1 min-h-[350px] flex flex-col">
        <div className="mb-4 shrink-0">
          <h3 className="text-base font-bold text-slate-800">Biểu đồ Dòng tiền (S-Curve & Monthly Cost)</h3>
        </div>
        
        <div className="w-full flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={cashFlowData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.5}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="month" 
                tickFormatter={(tick) => {
                  const [year, month] = tick.split('-');
                  return `${month}/${year.slice(2)}`;
                }} 
                minTickGap={20}
                stroke="#94a3b8"
                fontSize={11}
              />
              <YAxis 
                yAxisId="left" 
                tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`} 
                stroke="#94a3b8"
                fontSize={11}
              />
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                tickFormatter={(val) => `$${(val/1000000).toFixed(1)}M`} 
                stroke="#3b82f6"
                fontSize={11}
              />
              <Tooltip 
                formatter={(value: any, name: string) => [
                  `$${Number(value).toLocaleString(undefined, {maximumFractionDigits:0})}`, 
                  name === 'monthlyCost' ? 'Chi tiêu tháng' : 'Lũy kế'
                ]}
                labelFormatter={(label) => `Tháng: ${label}`}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }}/>
              <Bar yAxisId="left" dataKey="monthlyCost" name="monthlyCost" fill="#94a3b8" barSize={12} radius={[2, 2, 0, 0]} />
              <Area yAxisId="right" type="monotone" dataKey="cumulativeCost" name="cumulativeCost" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCumulative)" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

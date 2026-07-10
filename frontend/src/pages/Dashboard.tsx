import React, { useState, useEffect } from 'react';
import { Layers, Activity, GitCommit, Clock, Briefcase, DollarSign } from 'lucide-react';
import { api } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend } from 'recharts';

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

const Dashboard = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.getProjects();
        setProjects(res.data?.items || []);
      } catch (err) {
        console.error("Failed to load projects", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return <div className="h-full flex items-center justify-center text-slate-500">Loading Dashboard...</div>;
  }

  // Aggregate metrics
  const totalTasks = projects.reduce((sum, p) => sum + (p.num_tasks || 0), 0);
  const totalEdges = projects.reduce((sum, p) => sum + (p.num_edges || 0), 0);
  const avgDensity = projects.length > 0 
    ? projects.reduce((sum, p) => sum + (p.network_density || 0), 0) / projects.length 
    : 0;
  const totalCost = projects.reduce((sum, p) => sum + (p.total_cost || 0), 0);

  // Chart data
  const costData = projects.map(p => ({
    name: p.project_name.length > 15 ? p.project_name.substring(0, 15) + '...' : p.project_name,
    baseCost: p.base_cost || 0,
    totalCost: p.total_cost || 0
  }));

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div className="flex justify-between items-end shrink-0">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Global Portfolio Analytics</h2>
          <p className="text-sm text-slate-500">Overview of all active projects in the system</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 shrink-0">
        <StatCard 
          title="Active Projects" 
          value={projects.length} 
          icon={Briefcase} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Total Tasks" 
          value={totalTasks} 
          icon={Layers} 
          color="bg-emerald-500" 
        />
        <StatCard 
          title="Avg Density" 
          value={avgDensity.toFixed(4)} 
          icon={Activity} 
          color="bg-amber-500" 
        />
        <StatCard 
          title="Portfolio Value" 
          value={`$${(totalCost / 1000000).toFixed(1)}M`} 
          icon={DollarSign} 
          color="bg-purple-500" 
        />
      </div>

      {/* Cost Chart */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex-1 min-h-[350px] flex flex-col">
        <div className="mb-4 shrink-0">
          <h3 className="text-base font-bold text-slate-800">Project Cost Comparison (Base vs Total)</h3>
        </div>
        
        <div className="w-full flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={costData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 11, fill: '#64748b' }}
                interval={0}
                angle={-20}
                textAnchor="end"
              />
              <YAxis 
                tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`} 
                stroke="#94a3b8"
                fontSize={11}
              />
              <Tooltip 
                formatter={(value: any, name: any) => [
                  `$${Number(value).toLocaleString(undefined, {maximumFractionDigits:0})}`, 
                  name === 'baseCost' ? 'Base Cost' : 'Total Cost'
                ]}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }}/>
              <Bar dataKey="baseCost" name="Base Cost" fill="#94a3b8" radius={[4, 4, 0, 0]} barSize={30} />
              <Bar dataKey="totalCost" name="Total Cost" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={30} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

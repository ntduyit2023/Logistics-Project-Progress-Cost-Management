import React, { useMemo } from 'react';
import AirflowGraph from './AirflowGraph';
import { Layers, Activity, GitCommit, Clock, Columns, Sparkles, Zap, ArrowRight, ShieldCheck, TrendingDown } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend, Line, ReferenceLine } from 'recharts';
import mockData from '../mocks/project_583.json';

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center">
    <div className={`p-3 rounded-lg mr-4 ${color}`}>
      <Icon size={20} className="text-white" />
    </div>
    <div>
      <p className="text-xs font-medium text-slate-500 mb-0.5 uppercase tracking-wide">{title}</p>
      <h3 className="text-xl font-bold text-slate-800">{value}</h3>
    </div>
  </div>
);

const RecommendationCard = ({ type, title, desc, impact, confidence, icon: Icon, colorClass }: any) => (
  <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
    <div className="flex justify-between items-start mb-2">
      <div className={`flex items-center text-xs font-bold uppercase tracking-wider ${colorClass}`}>
        <Icon size={14} className="mr-1.5" />
        {type}
      </div>
      <span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded-full border border-slate-200">
        {confidence} Match
      </span>
    </div>
    <h4 className="font-bold text-slate-800 text-sm mb-1">{title}</h4>
    <p className="text-xs text-slate-500 leading-relaxed mb-3">{desc}</p>
    
    <div className="bg-slate-50 rounded p-2 mb-3 border border-slate-100 flex items-center justify-center">
      <span className="text-xs font-bold text-slate-700">Expected Impact: </span>
      <span className="text-xs font-bold text-emerald-600 ml-2 bg-emerald-100 px-2 py-0.5 rounded">{impact}</span>
    </div>

    <div className="flex gap-2">
      <button className="flex-1 bg-violet-600 text-white py-1.5 rounded-md text-xs font-bold hover:bg-violet-700 transition flex justify-center items-center">
        Apply <ArrowRight size={14} className="ml-1" />
      </button>
      <button className="px-3 bg-white border border-slate-300 text-slate-600 rounded-md text-xs font-medium hover:bg-slate-50 transition">
        Dismiss
      </button>
    </div>
  </div>
);

const Workspace = () => {
  const { project_name, status, num_tasks, num_edges, network_density, tasks } = mockData.data;

  // Xử lý dữ liệu gộp chung cho biểu đồ
  const { combinedData, bellCurveData, ganttData } = useMemo(() => {
    // 1. Dữ liệu Master Analytics
    const leafTasks = tasks.filter((t: any) => !tasks.some((other: any) => other.wbs.startsWith(`${t.wbs}.`)));
    const monthlyCost: Record<string, number> = {};
    const monthlyTasks: Record<string, Set<string>> = {};

    leafTasks.forEach((task: any) => {
      const startStr = task.time_info?.baseline_start;
      const duration = Math.max(1, Math.ceil(task.time_info?.duration || 0));
      const totalCost = task.cost_info?.total_cost || 0;
      
      if (!startStr) return;
      const startMs = new Date(startStr).getTime();
      const dailyCost = totalCost / duration;
      
      for (let i = 0; i < duration; i++) {
        const d = new Date(startMs + i * 24 * 60 * 60 * 1000);
        const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        
        monthlyCost[monthStr] = (monthlyCost[monthStr] || 0) + dailyCost;
        
        if (!monthlyTasks[monthStr]) monthlyTasks[monthStr] = new Set();
        monthlyTasks[monthStr].add(task.task_id);
      }
    });

    const sortedMonths = Object.keys(monthlyCost).sort();
    let cumulative = 0;
    
    const combined = sortedMonths.map(month => {
      cumulative += monthlyCost[month];
      return { 
        month, 
        monthlyCost: monthlyCost[month], 
        cumulativeCost: cumulative,
        activeCount: monthlyTasks[month]?.size || 0
      };
    });

    // 2. Dữ liệu PERT Bell Curve (Mô phỏng Phân phối xác suất Normal Distribution)
    const meanDays = 1070; // Giả định thời lượng trung bình dự án
    const stdDev = 45; // Độ lệch chuẩn (rủi ro)
    const bellCurve = [];
    const steps = 5;
    const startX = meanDays - Math.ceil((stdDev * 3.5) / steps) * steps;
    const endX = meanDays + stdDev * 3.5;
    
    for (let x = startX; x <= endX; x += steps) {
      const prob = Math.exp(-0.5 * Math.pow((x - meanDays) / stdDev, 2)); 
      bellCurve.push({ 
        days: Math.round(x), 
        probability: prob * 100, // Chuẩn hóa lên 100% để hiển thị
      });
    }

    // 3. Dữ liệu Mini Gantt Chart (Lấy 20 công việc thực tế đầu tiên, bỏ qua Summary Task)
    const sortedTasks = [...leafTasks].sort((a, b) => new Date(a.time_info?.baseline_start).getTime() - new Date(b.time_info?.baseline_start).getTime());
    const displayTasks = sortedTasks.slice(0, 20);
    const minStart = new Date(displayTasks[0]?.time_info?.baseline_start || 0).getTime();
    let maxEnd = minStart;
    displayTasks.forEach(t => {
      const end = new Date(t.time_info?.baseline_end || t.time_info?.baseline_start).getTime();
      if(end > maxEnd) maxEnd = end;
    });
    // Thêm 5% padding cho thời gian trục X để render đẹp hơn
    const totalMs = (maxEnd - minStart) * 1.05 || 1;

    const gantt = displayTasks.map((t: any) => {
      const startMs = new Date(t.time_info?.baseline_start).getTime();
      const endMs = new Date(t.time_info?.baseline_end || t.time_info?.baseline_start).getTime();
      return {
        id: t.task_id,
        name: t.task_name,
        wbs: t.wbs,
        isCritical: t.is_critical || (t.risk_info?.criticality_index > 0.8),
        leftPercent: ((startMs - minStart) / totalMs) * 100,
        widthPercent: Math.max(0.5, ((endMs - startMs) / totalMs) * 100)
      };
    });

    return { combinedData: combined, bellCurveData: bellCurve, ganttData: gantt };
  }, [tasks]);

  return (
    <div className="w-full h-[calc(100vh-80px)] overflow-y-auto bg-slate-50 p-6 custom-scrollbar">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center">
            <Columns className="mr-2 text-blue-600" size={24} /> 
            Grafana-style Workspace
          </h1>
          <p className="text-slate-500 mt-1">{project_name}</p>
        </div>
      </div>

      <div className="flex flex-col gap-6">
        {/* ROW 1: STATS */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard title="Total Tasks" value={num_tasks} icon={Layers} color="bg-blue-500" />
          <StatCard title="Dependencies" value={num_edges} icon={GitCommit} color="bg-emerald-500" />
          <StatCard title="Network Density" value={network_density.toFixed(4)} icon={Activity} color="bg-amber-500" />
          <StatCard title="Status" value={status} icon={Clock} color="bg-purple-500" />
        </div>

        {/* ROW 2: DAG & AI INSIGHTS */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* DAG (Chiếm 3/4) */}
          <div className="lg:col-span-3 h-[600px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col relative overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center z-10 shrink-0">
              <span className="font-bold text-slate-700">Network Logic Diagram</span>
              <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded flex items-center">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
                Live Interactive
              </span>
            </div>
            <div className="flex-1 relative min-h-0">
              <div className="absolute inset-0">
                <AirflowGraph />
              </div>
            </div>
          </div>

          {/* AI INSIGHTS (Chiếm 1/4) */}
          <div className="lg:col-span-1 h-[600px] bg-white rounded-xl shadow-sm border border-violet-200 flex flex-col overflow-hidden">
            <div className="bg-violet-50 border-b border-violet-100 px-4 py-3 flex items-center justify-between shrink-0">
              <div className="flex items-center">
                <Sparkles className="text-violet-600 mr-2" size={18} />
                <span className="font-bold text-violet-900">AI Insights</span>
              </div>
              <span className="bg-violet-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full animate-pulse">3 New</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50 custom-scrollbar">
              <RecommendationCard 
                type="Fast Tracking" 
                icon={Zap}
                colorClass="text-amber-600"
                title="Song song hóa WBS 1.1.2 & 1.1.3"
                desc="AI phát hiện 2 công việc này không có ràng buộc kỹ thuật cứng. Có thể thi công song song để rút ngắn tiến độ."
                impact="Tiết kiệm 12 ngày"
                confidence="85%"
              />
              <RecommendationCard 
                type="Resource Leveling" 
                icon={ShieldCheck}
                colorClass="text-emerald-600"
                title="Giảm tải tháng 11/2012"
                desc="Mật độ công việc vượt ngưỡng an toàn (Peak: 15 tasks/ngày). Đề xuất dời WBS 2.4 sang tháng 1 để tránh bottleneck."
                impact="Giảm 30% rủi ro"
                confidence="92%"
              />
              <RecommendationCard 
                type="Crashing" 
                icon={TrendingDown}
                colorClass="text-blue-600"
                title="Tăng tốc WBS 4.1 (Critical)"
                desc="Công việc WBS 4.1 nằm trên đường găng (Critical Path) có rủi ro trễ hạn cao. Đề xuất bổ sung thêm 2 nhân sự."
                impact="Time -8d, Cost +$5k"
                confidence="78%"
              />
            </div>
          </div>

        </div>

        {/* ROW 3: MASTER ANALYTICS & PERT BELL CURVE */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* COMBINED CHART (Chiếm 2/3) */}
          <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
            <div className="mb-4 shrink-0">
              <h3 className="font-bold text-slate-800">Master Analytics (Financial S-Curve & Task Density)</h3>
              <p className="text-xs text-slate-500">Combined view of Monthly Cost, Cumulative Cost, and Concurrent Tasks</p>
            </div>
            <div className="flex-1 min-h-0 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={combinedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.5}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="month" tickFormatter={(tick) => `${tick.split('-')[1]}/${tick.split('-')[0].slice(2)}`} minTickGap={20} stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="cost" orientation="left" tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`} stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="cumulative" orientation="right" tickFormatter={(val) => `$${(val/1000000).toFixed(1)}M`} stroke="#3b82f6" fontSize={11} />
                  <YAxis yAxisId="density" orientation="right" tickFormatter={(val) => `${val} tasks`} stroke="#10b981" fontSize={11} />
                  <Tooltip formatter={(value: any, name: string) => {
                    if (name === 'monthlyCost') return [`$${Number(value).toLocaleString()}`, 'Monthly Cost'];
                    if (name === 'cumulativeCost') return [`$${Number(value).toLocaleString()}`, 'Cumulative Cost'];
                    return [`${value} tasks`, 'Concurrent Tasks'];
                  }} labelFormatter={(label) => `Month: ${label}`} />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }}/>
                  <Bar yAxisId="cost" dataKey="monthlyCost" name="monthlyCost" fill="#cbd5e1" barSize={16} radius={[2, 2, 0, 0]} />
                  <Area yAxisId="cumulative" type="monotone" dataKey="cumulativeCost" name="cumulativeCost" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCumulative)" />
                  <Line yAxisId="density" type="monotone" dataKey="activeCount" name="activeCount" stroke="#10b981" strokeWidth={3} dot={{ r: 3, fill: '#10b981' }} activeDot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* PERT BELL CURVE (Chiếm 1/3) */}
          <div className="lg:col-span-1 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
            <div className="mb-4 shrink-0">
              <h3 className="font-bold text-slate-800">PERT Risk Analysis (AI Model)</h3>
              <p className="text-xs text-slate-500">Probability Distribution of Project Completion</p>
            </div>
            <div className="flex-1 min-h-0 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={bellCurveData} margin={{ top: 30, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBell" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.6}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="days" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}d`} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={() => ''} />
                  <Tooltip 
                    formatter={(val: number) => [`${val.toFixed(1)}% Relative Probability`, 'Probability']}
                    labelFormatter={(label) => `Completion Time: ${label} Days`}
                  />
                  <ReferenceLine 
                    x={1070} 
                    stroke="#8b5cf6" 
                    strokeDasharray="3 3" 
                    label={{ position: 'top', value: 'Most Likely: 1070d', fill: '#6d28d9', fontSize: 12, fontWeight: 'bold' }} 
                  />
                  <Area type="monotone" dataKey="probability" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorBell)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

        {/* ROW 4: MINI GANTT CHART (FULL WIDTH) */}
        <div className="w-full bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col overflow-hidden mb-8">
          <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-slate-800">Timeline WBS View (Gantt Chart)</h3>
              <p className="text-xs text-slate-500 mt-1">Showing first 20 chronological tasks</p>
            </div>
          </div>
          <div className="p-0">
            {/* Gantt Header */}
            <div className="flex border-b border-slate-200 bg-slate-100 py-2 px-4 text-xs font-bold text-slate-600">
              <div className="w-1/3">Task Name</div>
              <div className="w-2/3 border-l border-slate-300 pl-4 relative">
                <span className="absolute left-0">Start</span>
                <span className="absolute right-0 text-right pr-4">End</span>
                <span className="w-full text-center block text-slate-400 font-medium">Project Timeline Axis</span>
              </div>
            </div>
            {/* Gantt Rows */}
            <div className="flex flex-col">
              {ganttData.map((task, idx) => (
                <div key={task.id} className={`flex py-2 px-4 border-b border-slate-100 hover:bg-slate-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                  <div className="w-1/3 flex flex-col justify-center pr-4">
                    <span className="text-xs font-bold text-slate-500">WBS {task.wbs}</span>
                    <span className="text-sm font-medium text-slate-800 truncate" title={task.name}>{task.name}</span>
                  </div>
                  <div className="w-2/3 border-l border-slate-200 pl-4 relative h-10 flex items-center">
                    <div 
                      className={`absolute h-5 rounded shadow-sm ${task.isCritical ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ 
                        left: `calc(${task.leftPercent}% + 1rem)`, 
                        width: `${task.widthPercent}%`,
                        minWidth: '4px'
                      }}
                      title={`${task.name} (${task.isCritical ? 'Critical' : 'Standard'})`}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Workspace;

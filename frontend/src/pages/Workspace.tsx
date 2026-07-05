import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import AirflowGraph from './AirflowGraph';
import { Layers, Activity, GitCommit, Clock, Columns, Sparkles, Zap, ArrowRight, ShieldCheck, TrendingDown } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend, Line, ReferenceLine } from 'recharts';
import { api } from '../services/api';

import TaskFormModal from '../components/TaskFormModal';
import ResourceManagerModal from '../components/ResourceManagerModal';
import TimeManagerModal from '../components/TimeManagerModal';

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
  const { projectId } = useParams();
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<any | null>(null);
  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false);
  const [isTimeModalOpen, setIsTimeModalOpen] = useState(false);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        const res = await api.getProject(Number(projectId));
        setProjectData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (projectId) fetchProject();
  }, [projectId]);

  const handleSaveTask = async (data: any) => {
    try {
      const { predecessor_id, dependency_type, lag_days, stagedResources, ...taskData } = data;
      let newTaskId = editingTask?.id;

      if (editingTask) {
        await api.updateTask(Number(projectId), editingTask.id, taskData);
      } else {
        newTaskId = "T-" + Math.random().toString(36).substr(2, 6);
        await api.createTask(Number(projectId), { id: newTaskId, ...taskData });
      }

      // Sync Logic Constraint (Predecessor)
      if (newTaskId) {
        const oldEdge = projectData.constraint_logic?.find((e: any) => e.successor_id === newTaskId);
        try {
          if (predecessor_id) {
            if (oldEdge && oldEdge.predecessor_id !== predecessor_id) {
              await api.deleteLogicConstraint(Number(projectId), oldEdge.predecessor_id, newTaskId);
            }
            if (!oldEdge || oldEdge.predecessor_id !== predecessor_id || oldEdge.dependency_type !== dependency_type || oldEdge.lag_days !== lag_days) {
              if (oldEdge && oldEdge.predecessor_id === predecessor_id) {
                // Delete to recreate with new lag/type
                await api.deleteLogicConstraint(Number(projectId), oldEdge.predecessor_id, newTaskId);
              }
              await api.createLogicConstraint(Number(projectId), {
                predecessor_id: predecessor_id,
                successor_id: newTaskId,
                dependency_type: dependency_type || 'FS',
                lag_days: lag_days || 0
              });
            }
          } else if (!predecessor_id && oldEdge) {
            await api.deleteLogicConstraint(Number(projectId), oldEdge.predecessor_id, newTaskId);
          }
        } catch (e) {
          console.error("Failed to sync logic constraint", e);
        }
      }

      // Save staged resources
      if (stagedResources && newTaskId) {
        try {
          // 1. Fetch current from backend to know what to delete
          const currentRes = await api.getTaskResources(Number(projectId), newTaskId);
          const currentIds = currentRes.data.map((r: any) => r.resource_id);
          const stagedIds = stagedResources.map((r: any) => r.resource_id);
          
          // 2. Delete ones that are no longer staged
          const toDelete = currentIds.filter((id: number) => !stagedIds.includes(id));
          for (const id of toDelete) {
            await api.removeTaskResource(Number(projectId), newTaskId, id);
          }
          
          // 3. Upsert staged ones
          for (const res of stagedResources) {
            await api.assignTaskResource(Number(projectId), newTaskId, {
              resource_id: res.resource_id,
              request_quantity: res.request_quantity
            });
          }
        } catch (err) {
          console.error("Failed to sync task resources", err);
        }
      }

      setIsTaskModalOpen(false);
      window.location.reload();
    } catch (err) {
      alert('Failed to save task: ' + (err as Error).message);
    }
  };

  // Xử lý dữ liệu gộp chung cho biểu đồ
  const { combinedData, bellCurveData, ganttData } = useMemo(() => {
    if (!projectData) return { combinedData: [], bellCurveData: [], ganttData: [] };
    const tasks = projectData.tasks || [];
    
    // 1. Dữ liệu Master Analytics
    const leafTasks = tasks; // Tạm thời dùng tất cả tasks
    const monthlyCost: Record<string, number> = {};
    const monthlyTasks: Record<string, Set<string>> = {};

    leafTasks.forEach((task: any) => {
      const startStr = task.baseline_start;
      const duration = Math.max(1, Math.ceil(task.duration_days || 0));
      const totalCost = (task.internal_labor_cost || 0) + (task.equipment_cost || 0) + (task.material_cost || 0);
      
      if (!startStr) return;
      const startMs = new Date(startStr).getTime();
      const dailyCost = totalCost / duration;
      
      for (let i = 0; i < duration; i++) {
        const d = new Date(startMs + i * 24 * 60 * 60 * 1000);
        const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        
        monthlyCost[monthStr] = (monthlyCost[monthStr] || 0) + dailyCost;
        
        if (!monthlyTasks[monthStr]) monthlyTasks[monthStr] = new Set();
        monthlyTasks[monthStr].add(task.id);
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
    const sortedTasks = [...leafTasks]
      .filter(t => t.baseline_start)
      .sort((a, b) => new Date(a.baseline_start).getTime() - new Date(b.baseline_start).getTime());
    const displayTasks = sortedTasks.slice(0, 20);
    const minStart = new Date(displayTasks[0]?.baseline_start || 0).getTime();
    let maxEnd = minStart;
    displayTasks.forEach(t => {
      const end = new Date(t.baseline_start).getTime() + (t.duration_days || 0) * 24*60*60*1000;
      if(end > maxEnd) maxEnd = end;
    });
    // Thêm 5% padding cho thời gian trục X để render đẹp hơn
    const totalMs = (maxEnd - minStart) * 1.05 || 1;

    const gantt = displayTasks.map((t: any) => {
      const startMs = new Date(t.baseline_start).getTime();
      const endMs = startMs + (t.duration_days || 0) * 24*60*60*1000;
      return {
        id: t.id,
        name: t.task_name,
        wbs: t.wbs || t.id,
        isCritical: t.duration_days > 50,
        leftPercent: ((startMs - minStart) / totalMs) * 100,
        widthPercent: Math.max(0.5, ((endMs - startMs) / totalMs) * 100)
      };
    });

    return { combinedData: combined, bellCurveData: bellCurve, ganttData: gantt };
  }, [projectData]);

  if (loading || !projectData) {
    return <div className="h-full flex items-center justify-center">Loading Workspace...</div>;
  }

  const { project_name, status, num_tasks, num_edges, network_density, tasks, constraint_logic, constraint_resources } = projectData;

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
        <div className="flex gap-3">
          <button 
            onClick={() => setIsTimeModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-all"
          >
            Manage Calendar
          </button>
          <button 
            onClick={() => setIsResourceModalOpen(true)}
            className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-all"
          >
            Manage Resources
          </button>
          <button 
            onClick={() => {
              setEditingTask(null);
              setIsTaskModalOpen(true);
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-all"
          >
            + Add Node
          </button>
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
                <AirflowGraph 
                  tasks={tasks} 
                  dependencies={constraint_logic} 
                  onConnectEdge={async (source, target) => {
                    try {
                      await api.createLogicConstraint(Number(projectId), {
                        predecessor_id: source,
                        successor_id: target,
                        dependency_type: "FS"
                      });
                      window.location.reload();
                    } catch (err) {
                      alert("Failed to connect nodes: " + (err as Error).message);
                    }
                  }}
                  onDeleteTask={async (taskId) => {
                    try {
                      await api.deleteTask(Number(projectId), taskId);
                      window.location.reload();
                    } catch (err) {
                      alert("Failed to delete task: " + (err as Error).message);
                    }
                  }}
                  onEditTask={(task) => {
                    setEditingTask(task);
                    setIsTaskModalOpen(true);
                  }}
                />
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
                impact="Tránh trễ 5 ngày"
                confidence="88%"
              />
            </div>
          </div>

        </div>

        {/* ROW 3: CHARTS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-80">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-slate-800">Master Analytics</h3>
              <select className="text-xs bg-slate-50 border border-slate-200 rounded px-2 py-1 outline-none">
                <option>Cost & Activity</option>
              </select>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="month" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis yAxisId="left" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value/1000}k`} />
                  <YAxis yAxisId="right" orientation="right" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(value: any, name: string): [string, string] => {
                      if (name === 'Cumulative Cost') return [`$${value.toLocaleString()}`, name];
                      if (name === 'Monthly Cost') return [`$${value.toLocaleString()}`, name];
                      return [`${value} tasks`, name];
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                  <Bar yAxisId="right" dataKey="activeCount" name="Active Tasks" fill="#94a3b8" radius={[4, 4, 0, 0]} barSize={20} />
                  <Area yAxisId="left" type="monotone" dataKey="cumulativeCost" name="Cumulative Cost" fill="#cbd5e1" stroke="#94a3b8" fillOpacity={0.3} />
                  <Line yAxisId="left" type="monotone" dataKey="monthlyCost" name="Monthly Cost" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-80">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-slate-800">Monte Carlo Simulation</h3>
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded">Normal Dist.</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={bellCurveData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="days" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val: number) => `${val}%`} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(val: number): [string, string] => [`${val.toFixed(2)}%`, 'Probability']}
                  />
                  <ReferenceLine x={1070} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'top', value: 'Mean (1070d)', fill: '#ef4444', fontSize: 10 }} />
                  <Area type="monotone" dataKey="probability" stroke="#3b82f6" fill="#bfdbfe" fillOpacity={0.5} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* GANTT CHART */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-slate-800">Critical Path Gantt View</h3>
            <span className="text-xs text-slate-500">First 20 tasks</span>
          </div>
          <div className="space-y-3">
            {ganttData.map((task: any) => (
              <div key={task.id} className="flex items-center text-xs">
                <div className="w-48 shrink-0 font-medium text-slate-700 truncate pr-4" title={task.name}>
                  <span className="text-slate-400 mr-2">{task.wbs}</span>
                  {task.name}
                </div>
                <div className="flex-1 h-6 bg-slate-100 rounded-md relative">
                  <div 
                    className={`absolute h-full rounded-md shadow-sm transition-all ${
                      task.isCritical ? 'bg-red-400' : 'bg-blue-400'
                    }`}
                    style={{ left: `${task.leftPercent}%`, width: `${task.widthPercent}%` }}
                  ></div>
                </div>
              </div>
            ))}
            {ganttData.length === 0 && (
              <div className="text-center text-slate-400 py-6">No scheduled tasks available</div>
            )}
          </div>
        </div>

      </div>
      
      <TaskFormModal 
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        onSubmit={handleSaveTask}
        initialData={editingTask}
        availableTasks={tasks}
        projectResources={constraint_resources || []}
        constraintLogic={constraint_logic || []}
      />
      
      <ResourceManagerModal
        isOpen={isResourceModalOpen}
        onClose={() => setIsResourceModalOpen(false)}
        projectId={Number(projectId)}
        initialResources={constraint_resources || []}
      />

      <TimeManagerModal
        isOpen={isTimeModalOpen}
        onClose={() => setIsTimeModalOpen(false)}
        projectId={Number(projectId)}
        initialTimeConstraint={projectData.constraint_time}
      />
    </div>
  );
};

export default Workspace;

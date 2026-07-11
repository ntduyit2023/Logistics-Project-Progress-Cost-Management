import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AirflowGraph from './AirflowGraph';
import { 
  Layers, Activity, GitCommit, Clock, Columns, Sparkles, Zap, ArrowRight, ShieldCheck, TrendingDown, Cpu, Database, Sliders, DollarSign
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend, Line, ReferenceLine } from 'recharts';
import { api } from '../services/api';

import TaskFormModal from '../components/TaskFormModal';
import ResourceManagerModal from '../components/ResourceManagerModal';
import TimeManagerModal from '../components/TimeManagerModal';

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center transition-all hover:shadow-md">
    <div className={`p-3 rounded-lg mr-4 ${color}`}>
      <Icon size={20} className="text-white" />
    </div>
    <div>
      <p className="text-xs font-semibold text-slate-400 mb-0.5 uppercase tracking-wider">{title}</p>
      <h3 className="text-xl font-black text-slate-800">{value}</h3>
    </div>
  </div>
);

const RecommendationCard = ({ type, icon: Icon, colorClass, title, desc, impact, confidence }: any) => (
  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm transition-all hover:shadow-md group">
    <div className="flex justify-between items-start mb-2">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg bg-slate-50 mr-3 group-hover:scale-110 transition-transform ${colorClass}`}>
          <Icon size={18} />
        </div>
        <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider">{type}</span>
      </div>
      <span className="text-[10px] bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full border border-indigo-100 flex items-center">
        <Sparkles size={10} className="mr-1" /> {confidence}
      </span>
    </div>
    <h4 className="font-bold text-slate-800 text-sm mb-1.5 leading-tight">{title}</h4>
    <p className="text-xs text-slate-500 mb-3 leading-relaxed">{desc}</p>
    <div className="flex justify-between items-center pt-3 border-t border-slate-100">
      <span className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-1 rounded">
        Dự kiến: <span className={colorClass}>{impact}</span>
      </span>
      <button className="text-[11px] font-bold text-blue-600 hover:text-blue-800 flex items-center group-hover:translate-x-1 transition-transform">
        Apply <ArrowRight size={12} className="ml-1" />
      </button>
    </div>
  </div>
);

const Workspace = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [activeTab, setActiveTab] = useState<'recommendations' | 'baseline' | 'pareto' | 'ppo'>('recommendations');
  const [selectedParetoOptionIndex, setSelectedParetoOptionIndex] = useState<number>(0);

  // Modal State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<any | null>(null);
  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false);
  const [isTimeModalOpen, setIsTimeModalOpen] = useState(false);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        if (projectId && !isNaN(Number(projectId))) {
          const res = await api.getProject(Number(projectId));
          setProjectData(res.data);
          setActiveTab('recommendations');
        } else {
          // If no valid projectId, redirect to dashboard
          navigate('/dashboard');
        }
      } catch (err) {
        console.error(err);
        navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [projectId, navigate]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (projectData?.status === 'Simulating') {
      interval = setInterval(async () => {
        try {
          if (projectId && !isNaN(Number(projectId))) {
            const res = await api.getProject(Number(projectId));
            setProjectData(res.data);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [projectData?.status, projectId]);
  const handleSaveTask = async (data: any) => {
    try {
      if (!projectId || isNaN(Number(projectId))) {
         alert("Editing is only supported for valid projects.");
         return;
      }
      const { predecessor_id, dependency_type, lag_days, stagedResources, ...taskData } = data;
      let newTaskId = editingTask?.id;

      if (editingTask) {
        await api.updateTask(Number(projectId), editingTask.id, taskData);
      } else {
        newTaskId = "T-" + Math.random().toString(36).substr(2, 6);
        await api.createTask(Number(projectId), { id: newTaskId, ...taskData });
      }

      if (newTaskId) {
        const oldEdge = projectData.constraint_logic?.find((e: any) => e.successor_id === newTaskId);
        try {
          if (predecessor_id) {
            if (oldEdge && oldEdge.predecessor_id !== predecessor_id) {
              await api.deleteLogicConstraint(Number(projectId), oldEdge.predecessor_id, newTaskId);
            }
            if (!oldEdge || oldEdge.predecessor_id !== predecessor_id || oldEdge.dependency_type !== dependency_type || oldEdge.lag_days !== lag_days) {
              if (oldEdge && oldEdge.predecessor_id === predecessor_id) {
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

      setIsTaskModalOpen(false);
      window.location.reload();
    } catch (err) {
      alert('Failed to save task: ' + (err as Error).message);
    }
  };

  const handleRunAI = async () => {
    try {
      if (!projectId || isNaN(Number(projectId))) return;
      await api.runAISimulation(Number(projectId));
      window.location.reload();
    } catch (err) {
      alert('Failed to run AI Simulation: ' + (err as Error).message);
    }
  };

  const tasks = useMemo(() => projectData?.tasks || [], [projectData]);
  const dependencies = useMemo(() => projectData?.constraint_logic || [], [projectData]);
  const cpm_static_makespan = projectData?.tasks?.length * 5 || 0;
  const budget = projectData?.tasks?.reduce((sum: number, t: any) => sum + (t.total_cost || t.internal_labor_cost || 0), 0) || 0;
  const deadline = projectData?.constraint_time?.global_deadline_hours || (cpm_static_makespan * 1.2);

  const paretoOptions = useMemo(() => projectData?.pareto_nsga2?.options || [], [projectData]);
  const monte_carlo = useMemo(() => projectData?.monte_carlo || null, [projectData]);
  const ppo_schedule = useMemo(() => projectData?.ppo_schedule || null, [projectData]);
  const project_state_evolution = useMemo(() => projectData?.project_state_evolution || null, [projectData]);
  const simulationResults = useMemo(() => projectData?.metadata_json?.simulation_results || {}, [projectData]);

  const { selectedOptionModes, optionLabel, optionMakespan, optionCost, optionRisk } = useMemo(() => {
    let modes: number[] = new Array(tasks.length).fill(0);
    let label = 'Baseline (Normal)';
    let msk = cpm_static_makespan;
    let cost = budget / 1.5 || 0;
    let risk = 0.5;

    if (activeTab === 'recommendations' || activeTab === 'baseline') {
      modes = new Array(tasks.length).fill(0);
      label = activeTab === 'recommendations' ? 'API Live Data' : 'Baseline (Normal)';
      msk = cpm_static_makespan;
      cost = tasks.reduce((sum: number, t: any) => sum + (t.normal_cost || t.total_cost || t.internal_labor_cost || 0), 0);
      risk = 0.5;
    } else if (activeTab === 'pareto' && paretoOptions.length > 0) {
      const opt = paretoOptions[selectedParetoOptionIndex] || paretoOptions[0];
      modes = opt.modes;
      label = `Pareto Option ${selectedParetoOptionIndex + 1}`;
      msk = opt.makespan;
      cost = opt.cost;
      risk = opt.risk;
    } else if (activeTab === 'ppo') {
      modes = ppo_schedule?.modes || new Array(tasks.length).fill(0);
      label = 'PPO RL Adaptive Control';
      msk = ppo_schedule?.makespan || cpm_static_makespan;
      cost = ppo_schedule?.tgc || (budget * 0.8);
      risk = 0.15;
    }

    return { selectedOptionModes: modes, optionLabel: label, optionMakespan: msk, optionCost: cost, optionRisk: risk };
  }, [activeTab, selectedParetoOptionIndex, tasks, cpm_static_makespan, budget, paretoOptions, ppo_schedule]);

  const criticalityIndices = useMemo(() => monte_carlo?.criticality_indices || {}, [monte_carlo]);

  const { combinedData, bellCurveData, ganttData, maxEndHour } = useMemo(() => {
    const dailyCostMap: Record<string, number> = {};
    const dailyTasksMap: Record<string, Set<string>> = {};
    const startTime = new Date('2026-07-08').getTime();

    tasks.forEach((task: any, idx: number) => {
      const mode = selectedOptionModes[idx] || 0;
      const duration = mode === 1 
        ? Math.round((task.most_probable_duration || task.duration_days || 10) / 1.5) 
        : mode === 2 
          ? Math.round((task.most_probable_duration || task.duration_days || 10) / 2.0) 
          : (task.most_probable_duration || task.duration_days || 10);
      
      const cost = mode === 1 
        ? (task.crash_cost || 1500)
        : mode === 2 
          ? (task.outsource_cost || 2000)
          : (task.normal_cost || task.total_cost || task.internal_labor_cost || 0);

      let startMs = startTime;
      if (task.baseline_start) {
        startMs = new Date(task.baseline_start).getTime();
      } else {
        const startHour = idx * 12;
        startMs = startTime + (startHour / 8) * 24 * 60 * 60 * 1000;
      }

      const durationDays = Math.max(1, Math.round(duration) || 1);
      const dailyCostVal = cost / durationDays;

      for (let i = 0; i < durationDays; i++) {
        const d = new Date(startMs + i * 24 * 60 * 60 * 1000);
        const dayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        dailyCostMap[dayStr] = (dailyCostMap[dayStr] || 0) + dailyCostVal;

        if (!dailyTasksMap[dayStr]) dailyTasksMap[dayStr] = new Set();
        dailyTasksMap[dayStr].add(task.id);
      }
    });

    const sortedDays = Object.keys(dailyCostMap).sort();
    let cumulative = 0;
    const combined = sortedDays.map(date => {
      cumulative += dailyCostMap[date];
      return {
        date,
        dailyCost: dailyCostMap[date],
        cumulativeCost: cumulative,
        activeCount: dailyTasksMap[date]?.size || 0
      };
    });

    const mean = monte_carlo?.mean_makespan || cpm_static_makespan || 1000;
    const p90Val = monte_carlo?.P90 || (mean * 1.15);
    const stdDev = Math.max(5, (p90Val - mean) / 1.28 || mean * 0.05);

    const bellCurve: any[] = [];
    const steps = 30;
    const startX = mean - stdDev * 3.5;
    const endX = mean + stdDev * 3.5;
    const delta = (endX - startX) / steps;

    for (let x = startX; x <= endX; x += delta) {
      const prob = Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2));
      bellCurve.push({
        days: Math.round(x),
        probability: prob * 100
      });
    }

    const cpSatSchedule = projectData?.cp_sat_schedule?.schedule || {};
    const displayGanttTasks = tasks.slice(0, 20);

    let maxEndHour = 1;
    displayGanttTasks.forEach((t: any) => {
      const sched = cpSatSchedule[t.id];
      if (sched && sched.end > maxEndHour) maxEndHour = sched.end;
      if (t.duration_days && t.duration_days > maxEndHour) maxEndHour = t.duration_days;
    });

    return { combinedData: combined, bellCurveData: bellCurve, ganttData: [], maxEndHour };
  }, [tasks, selectedOptionModes, monte_carlo, cpm_static_makespan, projectData]);

  if (loading || !projectData) {
    return <div className="h-full flex items-center justify-center">Loading Workspace...</div>;
  }

  return (
    <div className="w-full h-[calc(100vh-80px)] overflow-y-auto bg-slate-50 p-6 custom-scrollbar">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-black text-slate-800 tracking-tight flex items-center">
            <Columns className="mr-2 text-blue-600 animate-pulse" size={22} />
            {projectData.project_name || "Digital Twin Workspace"}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">Merged UI: Live Backend API + Mocks Presentation</p>
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
            onClick={handleRunAI}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-all flex items-center"
            disabled={projectData?.status === 'Simulating'}
          >
            <Sparkles className="mr-2" size={16} /> 
            {projectData?.status === 'Simulating' ? 'AI is running...' : 'Run AI Pipeline'}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard title="Số lượng công việc" value={`${tasks.length} tasks`} icon={Layers} color="bg-blue-500" />
          <StatCard title="Số cạnh phụ thuộc" value={`${dependencies.length} edges`} icon={GitCommit} color="bg-emerald-500" />
          <StatCard title="Makespan CPM gốc" value={`${cpm_static_makespan.toFixed(1)} hrs`} icon={Clock} color="bg-amber-500" />
          <StatCard title="Hạn chót & Ngân sách" value={`${deadline.toFixed(0)}h / $${(budget/1000).toFixed(0)}k`} icon={Activity} color="bg-purple-500" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 h-[580px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col relative overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center z-10 shrink-0">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-700">Project Network Graph</span>
                <span className="text-[10px] bg-blue-100 text-blue-700 font-extrabold px-2 py-0.5 rounded uppercase">
                  {optionLabel}
                </span>
              </div>
            </div>
            <div className="flex-1 relative min-h-0">
              <div className="absolute inset-0">
                <AirflowGraph 
                  projectId={projectData.project_name}
                  tasks={tasks}
                  dependencies={dependencies}
                  selectedOptionModes={selectedOptionModes}
                  criticalityIndices={criticalityIndices}
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

          <div className="lg:col-span-1 h-[580px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center shrink-0">
              <Sliders className="text-blue-600 mr-2" size={18} />
              <span className="font-bold text-slate-700 text-sm">Pipeline Action Center</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50 custom-scrollbar">
              <div className="bg-slate-200/70 p-1 rounded-lg grid grid-cols-4 text-center text-xs font-bold">
                <button 
                  onClick={() => setActiveTab('recommendations')}
                  className={`py-1.5 rounded-md transition-colors ${activeTab === 'recommendations' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  Live AI
                </button>
                <button 
                  onClick={() => setActiveTab('baseline')}
                  className={`py-1.5 rounded-md transition-colors ${activeTab === 'baseline' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  Base
                </button>
                <button 
                  onClick={() => setActiveTab('pareto')}
                  className={`py-1.5 rounded-md transition-colors ${activeTab === 'pareto' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  Pareto
                </button>
                <button 
                  onClick={() => setActiveTab('ppo')}
                  className={`py-1.5 rounded-md transition-colors ${activeTab === 'ppo' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                >
                  RL
                </button>
              </div>

              {activeTab === 'recommendations' && (
                <div className="space-y-4">
                  {projectData?.status === 'Simulating' ? (
                    <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                      <p className="text-sm font-medium text-center">AI đang tiến hành phân tích dự án...</p>
                      <p className="text-xs text-center mt-1">Quá trình này có thể mất vài phút.</p>
                    </div>
                  ) : simulationResults?.recommendations && simulationResults.recommendations.length > 0 ? (
                    simulationResults.recommendations.map((rec: any, idx: number) => (
                      <RecommendationCard 
                        key={idx}
                        type={rec.type || "AI Suggestion"} 
                        icon={Zap} 
                        colorClass="text-blue-600" 
                        title={rec.title || `Khuyến nghị ${idx + 1}`} 
                        desc={rec.desc || ""}
                        impact={rec.impact || ""} 
                        confidence={rec.confidence || "90%"}
                      />
                    ))
                  ) : (
                    <div className="flex flex-col items-center justify-center py-8 text-slate-400">
                      <Activity size={32} className="mb-2 opacity-50" />
                      <p className="text-sm font-medium">Chưa có đề xuất tối ưu.</p>
                      <p className="text-xs text-center mt-1">Hãy khởi chạy AI Pipeline để nhận khuyến nghị.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab !== 'recommendations' && (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-black text-blue-600 uppercase tracking-wider">Cấu hình Đang Chọn</span>
                  </div>
                  <div>
                    <h4 className="font-extrabold text-slate-800 text-sm">{optionLabel}</h4>
                  </div>
                  <div className="border-t pt-3 space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Makespan dự báo:</span>
                      <span className="font-bold text-slate-800">{optionMakespan.toFixed(1)}h</span>
                    </div>
                    <div className="flex justify-between flex-wrap">
                      <span className="text-slate-400">Chi phí quy đổi (TGC):</span>
                      <span className="font-bold text-emerald-600">${Number(optionCost).toLocaleString(undefined, {maximumFractionDigits:0})}</span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'pareto' && paretoOptions.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-500 block uppercase">Danh sách Pareto Options:</span>
                  <div className="space-y-2">
                    {paretoOptions.slice(0, 4).map((opt: any, index: number) => (
                      <button
                        key={index}
                        onClick={() => setSelectedParetoOptionIndex(index)}
                        className={`w-full text-left p-3 rounded-lg border text-xs transition-all flex justify-between items-center ${
                          selectedParetoOptionIndex === index 
                            ? 'bg-blue-50 border-blue-500 shadow-sm' 
                            : 'bg-white hover:bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div>
                          <span className="font-bold text-slate-800 block">Option {index + 1} {index === 0 && '⭐ (Best)'}</span>
                          <span className="text-slate-500 text-[10px]">Cost: ${Number(opt.cost).toLocaleString(undefined, {maximumFractionDigits:0})}</span>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-blue-600 block">{opt.makespan.toFixed(1)}h</span>
                          <span className="text-slate-400 text-[9px]">Risk: {opt.risk.toFixed(2)}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
            <div className="mb-4 shrink-0 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-slate-800">Financial S-Curve & Task Density</h3>
                <p className="text-xs text-slate-500">Chi tiêu lũy kế và mật độ công việc song song được cập nhật tự động</p>
              </div>
              <div className="text-right text-xs bg-emerald-50 px-2 py-1 border border-emerald-100 rounded text-emerald-700 font-bold">
                TGC: ${Number(optionCost).toLocaleString(undefined, {maximumFractionDigits:0})}
              </div>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={combinedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" tickFormatter={(tick) => `${tick.split('-')[2]}/${tick.split('-')[1]}`} minTickGap={20} stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="cost" orientation="left" tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`} stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="cumulative" orientation="right" tickFormatter={(val) => `$${(val/1000).toFixed(0)}k`} stroke="#3b82f6" fontSize={11} />
                  <YAxis yAxisId="density" orientation="right" tickFormatter={(val) => `${val} tasks`} stroke="#10b981" fontSize={11} />
                  <Tooltip formatter={(value: any, name: any) => {
                    if (name === 'dailyCost') return [`$${Number(value).toLocaleString(undefined, {maximumFractionDigits:0})}`, 'Chi phí ngày'];
                    if (name === 'cumulativeCost') return [`$${Number(value).toLocaleString(undefined, {maximumFractionDigits:0})}`, 'Lũy kế'];
                    return [`${value} tasks`, 'Số công việc song song'];
                  }} labelFormatter={(label) => `Ngày: ${label}`} />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }}/>
                  <Bar yAxisId="cost" dataKey="dailyCost" name="dailyCost" fill="#cbd5e1" barSize={16} radius={[2, 2, 0, 0]} />
                  <Area yAxisId="cumulative" type="monotone" dataKey="cumulativeCost" name="cumulativeCost" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCumulative)" />
                  <Line yAxisId="density" type="monotone" dataKey="activeCount" name="activeCount" stroke="#10b981" strokeWidth={3} dot={{ r: 3, fill: '#10b981' }} activeDot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="lg:col-span-1 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
            <div className="mb-4 shrink-0">
              <h3 className="font-bold text-slate-800">Monte Carlo Risk Analysis</h3>
              <p className="text-xs text-slate-500">Phân phối xác suất thời gian hoàn thành dự án</p>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={bellCurveData} margin={{ top: 30, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBell" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.5}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="days" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => `${v}h`} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={() => ''} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    formatter={(val: number): [string, string] => [`${val.toFixed(2)}%`, 'Xác suất']}
                    labelFormatter={(val) => `${val}h`}
                  />
                  <Area type="monotone" dataKey="probability" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorBell)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
      
      {isTaskModalOpen && (
        <TaskFormModal
          isOpen={isTaskModalOpen}
          onClose={() => { setIsTaskModalOpen(false); setEditingTask(null); }}
          onSave={handleSaveTask}
          initialData={editingTask}
          tasks={tasks}
          constraintLogic={dependencies}
          projectResources={projectData?.constraint_resources || []}
          projectId={Number(projectId)}
          projectType={projectData?.type}
        />
      )}
      
      {isResourceModalOpen && (
        <ResourceManagerModal
          isOpen={isResourceModalOpen}
          onClose={() => setIsResourceModalOpen(false)}
          projectId={Number(projectId)}
          initialResources={projectData.constraint_resources || []}
        />
      )}

      {isTimeModalOpen && (
        <TimeManagerModal
          isOpen={isTimeModalOpen}
          onClose={() => setIsTimeModalOpen(false)}
          projectId={Number(projectId)}
          initialTimeConstraint={projectData.constraint_time || {}}
        />
      )}
    </div>
  );
};

export default Workspace;

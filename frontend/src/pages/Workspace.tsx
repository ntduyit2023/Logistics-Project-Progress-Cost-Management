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

const RecommendationCard = ({ type, title, desc, impact, confidence, icon: Icon, colorClass, onApply }: any) => (
  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">
    <div className="flex justify-between items-start mb-3">
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
      <button 
        onClick={onApply}
        className="text-[11px] font-bold text-blue-600 hover:text-blue-800 flex items-center group-hover:translate-x-1 transition-transform"
      >
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
        const randStr = Math.random().toString(36).substr(2, 6);
        newTaskId = `${projectId}_T-${randStr}`;
        await api.createTask(Number(projectId), { id: newTaskId, ...taskData });
      }

      // Sync resources assigned to the task
      if (stagedResources && Array.isArray(stagedResources)) {
        if (editingTask) {
          // Editing mode: sync resources
          try {
            const existingResRes = await api.getTaskResources(Number(projectId), newTaskId);
            const existingRes = existingResRes.data || [];
            
            // 1. Remove resources that are no longer assigned
            for (const ext of existingRes) {
              if (!stagedResources.some(sr => sr.resource_id === ext.resource_id)) {
                await api.removeTaskResource(Number(projectId), newTaskId, ext.resource_id);
              }
            }
            
            // 2. Assign new or updated resources
            for (const sr of stagedResources) {
              const ext = existingRes.find(x => x.resource_id === sr.resource_id);
              if (!ext || ext.request_quantity !== sr.request_quantity) {
                await api.assignTaskResource(Number(projectId), newTaskId, {
                  resource_id: sr.resource_id,
                  request_quantity: sr.request_quantity
                });
              }
            }
          } catch (resErr) {
            console.error("Failed to sync resources for task", resErr);
          }
        } else {
          // Creating mode: simply assign all staged resources
          for (const sr of stagedResources) {
            try {
              await api.assignTaskResource(Number(projectId), newTaskId, {
                resource_id: sr.resource_id,
                request_quantity: sr.request_quantity
              });
            } catch (resErr) {
              console.error("Failed to assign resource to new task", resErr);
            }
          }
        }
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
  const cpm_static_makespan = projectData?.metadata_json?.simulation_results?.cpm_static_makespan || (projectData?.tasks?.length * 5) || 0;
  const budget = projectData?.metadata_json?.simulation_results?.budget || projectData?.tasks?.reduce((sum: number, t: any) => sum + (t.total_cost || t.internal_labor_cost || 0), 0) || 0;
  const deadline = projectData?.metadata_json?.simulation_results?.deadline || projectData?.constraint_time?.global_deadline_hours || (cpm_static_makespan * 1.2);

  const simulationResults = useMemo(() => projectData?.metadata_json?.simulation_results || {}, [projectData]);
  const paretoOptions = useMemo(() => simulationResults?.pareto_nsga2?.options || [], [simulationResults]);
  const monte_carlo = useMemo(() => simulationResults?.monte_carlo || null, [simulationResults]);
  const ppo_schedule = useMemo(() => simulationResults?.ppo_schedule || null, [simulationResults]);
  const project_state_evolution = useMemo(() => simulationResults?.project_state_evolution || null, [simulationResults]);

  const liveRecommendations = useMemo(() => {
    if (simulationResults?.recommendations && simulationResults.recommendations.length > 0) {
      return simulationResults.recommendations;
    }
    const stateEvol = simulationResults?.project_state_evolution;
    if (!stateEvol) return [];

    // Case 1: action_applied inside before_after_comparison (Project 16/17 format)
    if (stateEvol.before_after_comparison?.action_applied) {
      const action = stateEvol.before_after_comparison.action_applied;
      const comp = stateEvol.before_after_comparison;
      
      let reduction = 0;
      if (comp.metrics_comparison?.makespan?.percent_change !== undefined) {
        reduction = Math.abs(comp.metrics_comparison.makespan.percent_change);
      } else if (comp.mean_makespan?.before && comp.mean_makespan?.after) {
        reduction = ((comp.mean_makespan.before - comp.mean_makespan.after) / comp.mean_makespan.before) * 100;
      }
      
      const dynamicConfidence = Math.min(99, 80 + reduction).toFixed(0) + "%";
      return [{
        type: "Tối ưu PPO",
        title: `Gợi ý hành động: ${action.action_type}`,
        desc: `PPO đề xuất tác động lên ${action.affected_tasks?.length || 0} công việc trên Critical Path.`,
        impact: `Giảm ${reduction.toFixed(1)}% Makespan`,
        confidence: dynamicConfidence
      }];
    }

    // Case 2: action_applied inside history array (Project 19 format)
    if (stateEvol.history && Array.isArray(stateEvol.history)) {
      const actions = stateEvol.history.filter((h: any) => h.action_applied);
      if (actions.length > 0) {
        const lastActionObj = actions[actions.length - 1];
        const action = lastActionObj.action_applied;
        
        // Cố gắng tính reduction từ history
        const firstState = stateEvol.history[0];
        const reduction = firstState?.makespan && lastActionObj.makespan 
          ? ((firstState.makespan - lastActionObj.makespan) / firstState.makespan) * 100 
          : 0;
          
        const dynamicConfidence = Math.min(99, 80 + reduction).toFixed(0) + "%";
        
        return [{
          type: "Tối ưu PPO",
          title: `Gợi ý hành động: ${action.action_type}`,
          desc: `PPO đề xuất tác động lên ${action.affected_tasks?.length || 0} công việc trên Critical Path.`,
          impact: `Giảm ${reduction.toFixed(1)}% Makespan`,
          confidence: dynamicConfidence
        }];
      }
    }

    // Case 3: action_applied directly on stateEvol (fallback)
    if (stateEvol.action_applied) {
      const action = stateEvol.action_applied;
      return [{
        type: "Tối ưu PPO",
        title: `Gợi ý hành động: ${action.action_type}`,
        desc: `PPO đề xuất tác động lên ${action.affected_tasks?.length || 0} công việc trên Critical Path.`,
        impact: `Tối ưu thời gian`,
        confidence: "95%"
      }];
    }

    return [];
  }, [simulationResults]);

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
      cost = projectData?.metadata_json?.simulation_results?.baseline_cost || tasks.reduce((sum: number, t: any) => sum + (t.normal_cost || t.total_cost || t.internal_labor_cost || 0), 0);
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
      const agendaHours = projectData?.constraint_time?.working_hours_per_day || projectData?.metadata_json?.agenda_working_hours || 8;
      const daysPerWeek = 5;
      let baseTaskDuration = 10;
      if (task.duration_hours !== undefined && task.duration_hours !== null && parseFloat(task.duration_hours) > 0) {
        baseTaskDuration = parseFloat(task.duration_hours);
      } else if (task.most_probable_duration) {
        baseTaskDuration = task.most_probable_duration;
      } else {
        const d_m = parseFloat(task.duration_months) || 0;
        const d_w = parseFloat(task.duration_weeks) || 0;
        const d_d = parseFloat(task.duration_days) || 0;
        const d_h = parseFloat(task.duration_hours) || 0;
        baseTaskDuration = d_m * 4 * daysPerWeek * agendaHours + d_w * daysPerWeek * agendaHours + d_d * agendaHours + d_h;
        if (baseTaskDuration <= 0) baseTaskDuration = 10;
      }
      const duration = mode === 1 
        ? Math.round(baseTaskDuration / 1.5) 
        : mode === 2 
          ? Math.round(baseTaskDuration / 2.0) 
          : baseTaskDuration;
      
      const baseTaskCost = (task.total_cost !== undefined && task.total_cost !== null)
        ? parseFloat(task.total_cost)
        : task.normal_cost || task.internal_labor_cost || 0;
      const cost = mode === 1 
        ? (task.crash_cost || baseTaskCost * 1.25)
        : mode === 2 
          ? (task.outsource_cost || baseTaskCost * 1.5)
          : baseTaskCost;

      let startMs = startTime;
      if (task.baseline_start) {
        startMs = new Date(task.baseline_start).getTime();
      } else {
        const startHour = idx * 12;
        startMs = startTime + (startHour / 8) * 24 * 60 * 60 * 1000;
      }

      const durationDays = Math.max(1, Math.ceil(duration / agendaHours) || 1);
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

    const cpSatSchedule = simulationResults?.cp_sat_schedule?.schedule || {};
    const displayGanttTasks = tasks.slice(0, 20);

    let maxEndHour = 1;
    
    const gantt = displayGanttTasks.map((t: any) => {
      const sched = cpSatSchedule[t.id];
      let start = 0;
      let duration = 10;
      if (t.duration_hours !== undefined && t.duration_hours !== null && parseFloat(t.duration_hours) > 0) {
        duration = parseFloat(t.duration_hours);
      } else if (t.most_probable_duration) {
        duration = t.most_probable_duration;
      } else {
        const agendaHours = projectData?.constraint_time?.working_hours_per_day || projectData?.metadata_json?.agenda_working_hours || 8;
        const daysPerWeek = 5;
        const d_m = parseFloat(t.duration_months) || 0;
        const d_w = parseFloat(t.duration_weeks) || 0;
        const d_d = parseFloat(t.duration_days) || 0;
        const d_h = parseFloat(t.duration_hours) || 0;
        duration = d_m * 4 * daysPerWeek * agendaHours + d_w * daysPerWeek * agendaHours + d_d * agendaHours + d_h;
        if (duration <= 0) duration = 10;
      }
      
      // If we are in Baseline or Recommendations, we simulate a simple waterfall start for visualization
      // Ideally we should use CPM early_start, but for now we stack them if no schedule exists
      
      if (sched) {
        start = sched.start;
        duration = sched.end - sched.start;
      } else {
        // Fallback approximation if no CP-SAT schedule
        start = Math.random() * (cpm_static_makespan * 0.5); 
      }
      
      const end = start + duration;
      if (end > maxEndHour) maxEndHour = end;
      
      return {
        id: t.id,
        name: t.name || t.task_name || `Task ${t.id}`,
        start,
        end,
        duration,
        isCritical: (monte_carlo?.criticality_indices && monte_carlo.criticality_indices[t.id] > 0.75)
      };
    });
    
    gantt.sort((a, b) => a.start - b.start);

    return { combinedData: combined, bellCurveData: bellCurve, ganttData: gantt, maxEndHour };
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
                      <p className="text-sm font-medium text-center">
                        {projectData?.metadata_json?.simulation_progress || 'AI đang tiến hành phân tích dự án...'}
                      </p>
                      <p className="text-xs text-center mt-1">Quá trình này có thể mất vài phút.</p>
                    </div>
                  ) : liveRecommendations && liveRecommendations.length > 0 ? (
                    liveRecommendations.map((rec: any, idx: number) => (
                      <RecommendationCard 
                        key={idx}
                        type={rec.type || "AI Suggestion"} 
                        icon={Zap} 
                        colorClass="text-blue-600" 
                        title={rec.title || `Khuyến nghị ${idx + 1}`} 
                        desc={rec.desc || ""}
                        impact={rec.impact || ""} 
                        confidence={rec.confidence || "90%"}
                        onApply={() => setActiveTab('ppo')}
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

        {/* Gantt Chart Section */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm mt-6">
          <div className="mb-4 shrink-0">
            <h3 className="font-bold text-slate-800">Project Gantt Chart (Top 20 Tasks)</h3>
            <p className="text-xs text-slate-500">Tiến độ thời gian thực hiện công việc (Ước tính)</p>
          </div>
          <div className="overflow-x-auto relative w-full border border-slate-100 rounded-lg bg-slate-50 p-4">
            <div className="min-w-[800px] relative" style={{ height: `${ganttData.length * 40 + 40}px` }}>
              {/* X-axis ticks (approximate based on maxEndHour) */}
              <div className="absolute top-0 left-0 right-0 h-6 border-b border-slate-200 flex text-[10px] text-slate-400">
                {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
                  <div key={ratio} className="absolute border-l border-slate-200 pl-1 h-full" style={{ left: `${ratio * 100}%` }}>
                    {(maxEndHour * ratio).toFixed(0)}h
                  </div>
                ))}
              </div>
              
              {/* Render Bars */}
              <div className="mt-8">
                {ganttData.map((task, index) => {
                  const leftPercent = maxEndHour ? (task.start / maxEndHour) * 100 : 0;
                  const widthPercent = maxEndHour ? (task.duration / maxEndHour) * 100 : 0;
                  return (
                    <div key={task.id} className="relative h-8 mb-2 flex items-center group">
                      <div className="w-32 shrink-0 text-xs text-slate-600 truncate pr-2 font-medium" title={task.name}>
                        {task.name}
                      </div>
                      <div className="flex-1 relative h-full bg-slate-200/50 rounded-md">
                        <div 
                          className={`absolute top-1 bottom-1 rounded-md shadow-sm transition-all duration-300 flex items-center px-2 overflow-hidden ${
                            task.isCritical 
                              ? 'bg-rose-500 text-white' 
                              : 'bg-blue-500 text-white'
                          }`}
                          style={{ left: `${leftPercent}%`, width: `${Math.max(widthPercent, 1)}%` }}
                        >
                          {widthPercent > 5 && <span className="text-[10px] truncate">{task.duration.toFixed(1)}h</span>}
                        </div>
                      </div>
                      
                      {/* Tooltip */}
                      <div className="absolute left-32 top-full mt-1 bg-slate-800 text-white text-xs px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                        <strong>{task.name}</strong><br/>
                        Start: {task.start.toFixed(1)}h | End: {task.end.toFixed(1)}h
                      </div>
                    </div>
                  );
                })}
              </div>
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

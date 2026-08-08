import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AirflowGraph from './AirflowGraph';
import {
  Layers, Activity, GitCommit, Clock, Columns, Sparkles, Zap, ArrowRight, ShieldCheck, TrendingDown, Cpu, Database, Sliders, DollarSign, ArrowLeft, AlertTriangle
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Bar, Legend, Line, ReferenceLine, ScatterChart, Scatter, ZAxis } from 'recharts';
import { api } from '../services/api';

import TaskFormModal from '../components/TaskFormModal';
import ResourceManagerModal from '../components/ResourceManagerModal';
import TimeManagerModal from '../components/TimeManagerModal';

import { OverviewTab } from '../components/workspace/tabs/OverviewTab';
import { AnalysisTab } from '../components/workspace/tabs/AnalysisTab';
import { AssignmentTab } from '../components/workspace/tabs/AssignmentTab';
import { SelectionTab } from '../components/workspace/tabs/SelectionTab';
import { EvaluationTab } from '../components/workspace/tabs/EvaluationTab';

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

  // Custom Toast State
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [wasSimulating, setWasSimulating] = useState(false);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      if (projectId) {
        const res = await api.getProject(projectId);
        setProjectData(res.data);
      } else {
        setErrorMsg("Mã dự án không hợp lệ.");
      }
    } catch (err) {
      console.error("Lỗi khi tải chi tiết dự án:", err);
      setErrorMsg((err as Error).message || "Không thể tải thông tin dự án từ máy chủ Backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  // Real-Time SSE Stream Listener (Fast & Light Stream Push)
  useEffect(() => {
    let eventSource: EventSource | null = null;

    if (projectData?.status === 'Simulating' && projectId) {
      const hostname = window.location.hostname;
      const streamUrl = `http://${hostname}:8000/api/v1/projects/${projectId}/simulation-stream`;

      eventSource = new EventSource(streamUrl);

      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.message) {
            showToast(data.message, data.status === 'Error' ? 'error' : data.status === 'Planning' ? 'success' : 'info');
          }

          // When simulation finishes or errors out, fetch updated project details ONCE & close stream
          if (data.status && data.status !== 'Simulating') {
            const res = await api.getProject(Number(projectId));
            setProjectData(res.data);
            eventSource?.close();
          }
        } catch (err) {
          console.error("Error parsing SSE event data", err);
        }
      };

      eventSource.onerror = (err) => {
        console.error("SSE Connection error", err);
        eventSource?.close();
      };
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [projectData?.status, projectId]);

  const handleSaveTask = async (data: any) => {
    try {
      if (!projectId) {
        alert("Invalid project ID.");
        return;
      }
      const { predecessor_id, dependency_type, lag_days, stagedResources, stagedPredecessors, ...taskData } = data;
      let newTaskId = editingTask ? (editingTask.task_id || editingTask.id) : null;

      if (editingTask && newTaskId) {
        await api.updateTask(projectId, String(newTaskId), taskData);
      } else {
        const createRes = await api.createTask(projectId, taskData);
        if (createRes && createRes.data && (createRes.data.task_id || createRes.data.id)) {
          newTaskId = createRes.data.task_id || createRes.data.id;
        } else {
          throw new Error("Failed to get task ID from server after creation.");
        }
      }

      // Sync resources assigned to the task
      if (stagedResources && Array.isArray(stagedResources) && newTaskId) {
        if (editingTask) {
          // Editing mode: sync resources
          try {
            const existingResRes = await api.getTaskResources(projectId, newTaskId);
            const existingRes = existingResRes.data || [];

            // 1. Remove resources that are no longer assigned
            for (const ext of existingRes) {
              if (!stagedResources.some(sr => sr.resource_id === ext.resource_id)) {
                await api.removeTaskResource(projectId, newTaskId, ext.resource_id);
              }
            }

            // 2. Assign new or updated resources
            for (const sr of stagedResources) {
              const ext = existingRes.find(x => x.resource_id === sr.resource_id);
              if (!ext || ext.request_quantity !== sr.request_quantity) {
                await api.assignTaskResource(projectId, newTaskId, {
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
              await api.assignTaskResource(projectId, newTaskId, {
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
        // Handle staged predecessors (from the + button on new tasks)
        if (stagedPredecessors && stagedPredecessors.length > 0) {
          for (const p of stagedPredecessors) {
            try {
              await api.createLogicConstraint(projectId, {
                predecessor_id: p.predecessor_id,
                successor_id: newTaskId,
                dependency_type: p.dependency_type || 'FS',
                lag_hours: p.lag_hours || 0
              });
            } catch (e) {
              console.error("Failed to save staged logic constraint", e);
            }
          }
        }
      }

      setIsTaskModalOpen(false);
      fetchProjectDetails();
    } catch (err) {
      alert('Failed to save task: ' + (err as Error).message);
    }
  };

  const handleRunAI = async () => {
    if (!projectId) return;
    try {
      setIsGlpoLoading(true);
      const projectCode = projectData?.metadata_json?.project_code || String(projectId);
      showToast('Đang khởi chạy luồng tối ưu GLPO AI (HGT + CP-SAT + Monte Carlo)...', 'info');

      const formattedDeadline = glpoTargetDate 
        ? `${glpoTargetDate} ${glpoTargetHour}:00` 
        : undefined;

      const res = await api.runGLPOOptimization(projectCode, {
        mc_iterations: glpoMcIterations,
        pareto_count: glpoParetoCount,
        overtime_multiplier: glpoOvertimeMulti,
        penalty_per_day: glpoPenaltyPerDay,
        bonus_per_day: glpoBonusPerDay,
        target_deadline: formattedDeadline,
        pareto_sort: glpoParetoSort
      });

      if (res && res.success) {
        setGlpoResult(res.data);
        setSelectedGlpoOptionIndex(-1);
        if (res.data?.metadata_json?.simulation_results?.pareto_options) {
          setWorkspaceTab('ai_pipeline');
        }
        showToast('Tối ưu hóa GLPO AI + OR hoàn tất thành công!', 'success');
        await fetchProjectDetails();
      } else {
        await api.runAISimulation(projectId);
        setProjectData((prev: any) => ({ ...prev, status: 'Simulating' }));
        showToast('Đã kích hoạt giả lập AI ngầm thành công!', 'success');
      }
    } catch (err) {
      showToast('Tối ưu hóa AI thất bại: ' + (err as Error).message, 'error');
    } finally {
      setIsGlpoLoading(false);
    }
  };

  const [isApplyingOption, setIsApplyingOption] = useState<boolean>(false);

  const handleApplyParetoOption = async (optionIndex: number, optionData: any) => {
    if (!projectId || !optionData) return;
    try {
      setIsApplyingOption(true);
      setSelectedGlpoOptionIndex(optionIndex);
      showToast(`Đang áp dụng ${optionData.option_name || `Phương án ${optionIndex + 1}`} vào CSDL dự án...`, 'info');

      const res = await api.applyParetoOption(String(projectId), optionIndex, optionData);
      if (res && res.success) {
        const updatedInfo = res.data?.updated_tasks ? ` (${res.data.updated_tasks} công việc đã cập nhật)` : '';
        showToast((res.message || `Đã áp dụng thành công ${optionData.option_name || `Phương án ${optionIndex + 1}`}!`) + updatedInfo, 'success');
        await fetchProjectDetails();
      }
    } catch (err) {
      showToast('Áp dụng phương án thất bại: ' + (err as Error).message, 'error');
    } finally {
      setIsApplyingOption(false);
    }
  };

  const handleRestoreBaseline = async () => {
    if (!projectId) return;
    if (!window.confirm("Bạn có chắc chắn muốn khôi phục dữ liệu ban đầu (Baseline Gốc) của toàn bộ công việc trong dự án?")) return;
    try {
      setIsApplyingOption(true);
      showToast('Đang khôi phục dữ liệu ban đầu (Baseline Gốc) của dự án...', 'info');
      const res = await api.restoreBaseline(String(projectId));
      if (res && res.success) {
        showToast(res.message || 'Đã khôi phục thành công dữ liệu ban đầu!', 'success');
        setSelectedGlpoOptionIndex(-1);
        await fetchProjectDetails();
      }
    } catch (err) {
      showToast('Khôi phục dữ liệu thất bại: ' + (err as Error).message, 'error');
    } finally {
      setIsApplyingOption(false);
    }
  };

  const [workspaceTab, setWorkspaceTab] = useState<'overview' | 'analysis' | 'assignment' | 'ai_pipeline'>('overview');
  const [paretoChartType, setParetoChartType] = useState<'scatter' | 'bar'>('scatter');
  const [glpoResult, setGlpoResult] = useState<any>(null);
  const [selectedGlpoOptionIndex, setSelectedGlpoOptionIndex] = useState<number>(-1);
  const [isGlpoLoading, setIsGlpoLoading] = useState<boolean>(false);

  // Contract & AI Parameters State
  const [glpoMcIterations, setGlpoMcIterations] = useState<number>(1000);
  const [glpoParetoCount, setGlpoParetoCount] = useState<number>(20);
  const [glpoOvertimeMulti, setGlpoOvertimeMulti] = useState<number>(1.5);
  const [glpoPenaltyPerDay, setGlpoPenaltyPerDay] = useState<number>(0.0);
  const [glpoBonusPerDay, setGlpoBonusPerDay] = useState<number>(0.0);
  const [glpoTargetDate, setGlpoTargetDate] = useState<string>("");
  const [glpoTargetHour, setGlpoTargetHour] = useState<string>("17:00");
  const [glpoParetoSort, setGlpoParetoSort] = useState<string>("makespan_hours");

  const handleRunGLPO = async () => {
    try {
      setIsGlpoLoading(true);
      const projectCode = projectData?.metadata_json?.project_code || 'C2011-07';
      showToast('Đang khởi chạy luồng tối ưu GLPO (HGT AI + Monte Carlo CPM + CP-SAT)...', 'info');

      const formattedDeadline = glpoTargetDate 
        ? `${glpoTargetDate} ${glpoTargetHour}:00` 
        : undefined;

      const res = await api.runGLPOOptimization(projectCode, {
        mc_iterations: glpoMcIterations,
        pareto_count: glpoParetoCount,
        overtime_multiplier: glpoOvertimeMulti,
        penalty_per_day: glpoPenaltyPerDay,
        bonus_per_day: glpoBonusPerDay,
        target_deadline: formattedDeadline,
        pareto_sort: glpoParetoSort
      });
      if (res.success) {
        setGlpoResult(res.data);
        setSelectedGlpoOptionIndex(-1);
        setActiveTab('pareto');
        showToast('Tối ưu hóa GLPO AI + OR hoàn tất thành công!', 'success');
      }
    } catch (err) {
      showToast('Tối ưu hóa GLPO thất bại: ' + (err as Error).message, 'error');
    } finally {
      setIsGlpoLoading(false);
    }
  };

  const tasks = useMemo(() => projectData?.tasks || [], [projectData]);
  const dependencies = useMemo(() => projectData?.constraint_logic || [], [projectData]);
  


  const cpm_static_makespan = projectData?.metadata_json?.simulation_results?.cpm_static_makespan || 0;
  const budget = projectData?.metadata_json?.simulation_results?.budget || projectData?.tasks?.reduce((sum: number, t: any) => sum + (t.total_cost || t.internal_labor_cost || 0), 0) || 0;
  const deadline = projectData?.metadata_json?.simulation_results?.deadline || projectData?.constraint_time?.global_deadline_hours || (cpm_static_makespan * 1.2);

  const simulationResults = useMemo(() => projectData?.metadata_json?.simulation_results || {}, [projectData]);
  const paretoOptions = useMemo(() => simulationResults?.pareto_nsga2?.options || [], [simulationResults]);
  const allParetoOptions = useMemo(() => {
    return glpoResult?.pareto_options || glpoResult?.pareto_solutions || projectData?.metadata_json?.pareto_options_data?.pareto_options || paretoOptions || [];
  }, [glpoResult, paretoOptions, projectData]);
  const paretoBarData = useMemo(() => {
    return allParetoOptions.map((opt: any, idx: number) => ({
      name: opt.option_name || `PA ${idx + 1}`,
      cost: (opt.total_cost || opt.cost || 0) / 1000,
      makespan: opt.makespan_hours || opt.makespan || 0,
      risk: opt.risk_pct !== undefined ? opt.risk_pct : (opt.risk ? opt.risk * 100 : 0),
      raw: opt
    }));
  }, [allParetoOptions]);

  const currentOption = useMemo(() => {
    return allParetoOptions[selectedGlpoOptionIndex] || null;
  }, [allParetoOptions, selectedGlpoOptionIndex]);

  const displayMakespan = useMemo(() => {
    if (currentOption?.makespan_hours) return Number(currentOption.makespan_hours);
    if (currentOption?.makespan) return Number(currentOption.makespan);
    return cpm_static_makespan;
  }, [currentOption, cpm_static_makespan]);

  const displayCost = useMemo(() => {
    if (currentOption?.total_cost) return Number(currentOption.total_cost);
    if (currentOption?.cost) return Number(currentOption.cost);
    if (projectData?.total_cost) return Number(projectData.total_cost);
    return budget;
  }, [currentOption, projectData, budget]);
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
    if (!tasks || tasks.length === 0) {
      return { combinedData: [], bellCurveData: [], ganttData: [], maxEndHour: 100 };
    }

    const agendaHours = projectData?.constraint_time?.working_hours_per_day || 8;

    // GLPO preview schedule: when user clicks "Xem trước", use optimized task data
    const glpoSchedule: Record<string, any> = currentOption?.tasks_schedule || currentOption?.tasks || {};

    const getBaseTaskDurationHours = (t: any) => {
      if (t.duration_hours !== undefined && t.duration_hours !== null && parseFloat(t.duration_hours) > 0) {
        return parseFloat(t.duration_hours);
      }
      if (t.most_probable_duration) return t.most_probable_duration;
      const d_d = parseFloat(t.duration_days) || 0;
      const d_h = parseFloat(t.duration_hours) || 0;
      const dur = d_d * agendaHours + d_h;
      return dur > 0 ? dur : agendaHours;
    };

    const getTaskDurationHours = (t: any) => {
      // If a GLPO option is being previewed, use its optimized duration
      const taskKey = String(t.task_id || t.id);
      const glpoTask = glpoSchedule[taskKey] || glpoSchedule[String(t.id)];
      if (glpoTask) {
        const newDur = glpoTask.new_duration ?? glpoTask.duration_hours;
        if (newDur !== undefined && newDur !== null && parseFloat(newDur) > 0) {
          return parseFloat(newDur);
        }
      }
      return getBaseTaskDurationHours(t);
    };

    // 1. Determine earliest project start timestamp
    let earliestStartMs = Infinity;
    tasks.forEach((t: any) => {
      if (t.baseline_start) {
        const ms = new Date(t.baseline_start).getTime();
        if (!isNaN(ms) && ms < earliestStartMs) earliestStartMs = ms;
      }
    });

    if (earliestStartMs === Infinity) {
      earliestStartMs = new Date('2026-01-01T08:00:00Z').getTime();
    }

    // 2. Build topological CPM fallback
    const predMap: Record<string, string[]> = {};
    const taskMap: Record<string, any> = {};
    tasks.forEach((t: any) => {
      taskMap[t.id] = t;
      if (t.task_id) taskMap[t.task_id] = t;
      predMap[t.id] = [];
    });

    const logicList = projectData?.constraint_logic || [];
    logicList.forEach((leg: any) => {
      const pred = String(leg.predecessor_id);
      const succ = String(leg.successor_id);
      if (predMap[succ]) {
        predMap[succ].push(pred);
      }
    });

    const esMap: Record<string, number> = {};
    const getEarlyStart = (taskId: string, visited = new Set<string>()): number => {
      if (esMap[taskId] !== undefined) return esMap[taskId];
      if (visited.has(taskId)) return 0;
      visited.add(taskId);

      const preds = predMap[taskId] || [];
      if (preds.length === 0) {
        esMap[taskId] = 0;
        return 0;
      }

      let maxEs = 0;
      for (const pId of preds) {
        const pTask = taskMap[pId];
        const pEs = getEarlyStart(pId, visited);
        const pDur = pTask ? getTaskDurationHours(pTask) : agendaHours;
        if (pEs + pDur > maxEs) maxEs = pEs + pDur;
      }
      esMap[taskId] = maxEs;
      return maxEs;
    };

    tasks.forEach((t: any) => getEarlyStart(t.id));

    // 3. Financial S-Curve (Daily Cost & Active Task Density)
    const dailyCostMap: Record<string, number> = {};
    const dailyTasksMap: Record<string, Set<string>> = {};

    tasks.forEach((t: any, idx: number) => {
      const mode = selectedOptionModes[idx] || 0;
      const taskKey = String(t.task_id || t.id);
      const glpoTask = glpoSchedule[taskKey] || glpoSchedule[String(t.id)];
      const durationHours = getTaskDurationHours(t);

      const baseTaskCost = (t.total_cost !== undefined && t.total_cost !== null)
        ? parseFloat(t.total_cost)
        : t.normal_cost || t.internal_labor_cost || 0;
      const cost = glpoTask?.total_cost ? parseFloat(glpoTask.total_cost) : (mode === 1 ? (t.crash_cost || baseTaskCost * 1.25) : mode === 2 ? (t.outsource_cost || baseTaskCost * 1.5) : baseTaskCost);

      let taskStartMs = earliestStartMs;
      if (glpoTask && glpoTask.baseline_start) {
        // Use the pre-computed calendar-aware datetime from schedule_extractor directly
        const parsedMs = new Date(glpoTask.baseline_start).getTime();
        if (!isNaN(parsedMs)) taskStartMs = parsedMs;
      } else if (glpoTask && glpoTask.start_hours !== undefined) {
        // Fallback: offset from project start (approximate - only when no datetime available)
        taskStartMs = earliestStartMs + glpoTask.start_hours * 3600 * 1000;
      } else if (t.baseline_start) {
        const parsedMs = new Date(t.baseline_start).getTime();
        if (!isNaN(parsedMs)) taskStartMs = parsedMs;
      } else {
        const esHours = esMap[t.id] ?? (idx * agendaHours);
        const esDays = Math.floor(esHours / agendaHours);
        taskStartMs = earliestStartMs + esDays * 24 * 60 * 60 * 1000;
      }

      const durationDays = Math.max(1, Math.ceil(durationHours / agendaHours));
      const dailyCostVal = cost / durationDays;

      for (let i = 0; i < durationDays; i++) {
        const d = new Date(taskStartMs + i * 24 * 60 * 60 * 1000);
        const dayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        dailyCostMap[dayStr] = (dailyCostMap[dayStr] || 0) + dailyCostVal;

        if (!dailyTasksMap[dayStr]) dailyTasksMap[dayStr] = new Set();
        dailyTasksMap[dayStr].add(t.id);
      }
    });

    const sortedDays = Object.keys(dailyCostMap).sort();
    let cumulative = 0;
    const combined = sortedDays.map(date => {
      cumulative += dailyCostMap[date];
      return {
        date,
        dailyCost: Number(dailyCostMap[date].toFixed(2)),
        cumulativeCost: Number(cumulative.toFixed(2)),
        activeCount: dailyTasksMap[date]?.size || 0
      };
    });

    // 4. Monte Carlo Bell Curve
    let maxProjectHour = 0;
    tasks.forEach((t: any) => {
      let tStartHour = 0;
      if (t.baseline_start) {
        const parsedMs = new Date(t.baseline_start).getTime();
        if (!isNaN(parsedMs)) {
          tStartHour = (parsedMs - earliestStartMs) / (3600 * 1000);
        }
      } else {
        tStartHour = esMap[t.id] ?? 0;
      }
      const tEnd = tStartHour + getTaskDurationHours(t);
      if (tEnd > maxProjectHour) maxProjectHour = tEnd;
    });

    const mean = (currentOption ? displayMakespan : null) || monte_carlo?.mean_makespan || cpm_static_makespan || (maxProjectHour > 0 ? maxProjectHour : 500);
    const p90Val = monte_carlo?.P90 || (mean * 1.15);
    const stdDev = Math.max(5, (p90Val - mean) / 1.28 || mean * 0.08);

    const bellCurve: any[] = [];
    const steps = 35;
    const startX = Math.max(0, mean - stdDev * 3.2);
    const endX = mean + stdDev * 3.2;
    const delta = (endX - startX) / steps;

    for (let x = startX; x <= endX; x += delta) {
      const z = (x - mean) / stdDev;
      const probDensity = Math.exp(-0.5 * z * z);
      bellCurve.push({
        days: Math.round(x),
        probability: Number((probDensity * 100).toFixed(1))
      });
    }

    // 5. Gantt Chart (All Tasks)
    const cpSatSchedule = simulationResults?.cp_sat_schedule?.schedule || {};
    const displayGanttTasks = tasks;

    let maxEnd = 1;

    const gantt = displayGanttTasks.map((t: any, originalIndex: number) => {
      const sched = cpSatSchedule[t.id] || cpSatSchedule[t.task_id];
      const taskKey = String(t.task_id || t.id);
      const glpoTask = glpoSchedule[taskKey] || glpoSchedule[String(t.id)];
      let start = 0;
      let duration = getTaskDurationHours(t);
      const baseDuration = getBaseTaskDurationHours(t);

      if (glpoTask && glpoTask.start_hours !== undefined) {
        start = glpoTask.start_hours;
        duration = glpoTask.new_duration ?? glpoTask.duration_hours ?? baseDuration;
      } else if (t.baseline_start) {
        const parsedMs = new Date(t.baseline_start).getTime();
        if (!isNaN(parsedMs)) {
          start = (parsedMs - earliestStartMs) / (3600 * 1000);
        }
      } else {
        start = esMap[t.id] ?? 0;
      }

      const end = start + duration;
      if (end > maxEnd) maxEnd = end;

      const appliedIds: string[] = projectData?.metadata_json?.applied_task_ids || [];
      const appliedDetails: Record<string, any> = projectData?.metadata_json?.applied_task_details || {};
      const detail = glpoTask || appliedDetails[taskKey] || appliedDetails[String(t.id)] || null;
      
      const mode = selectedOptionModes[originalIndex] || 0;
      const durDiff = detail ? ((detail.old_duration || baseDuration) - (detail.new_duration ?? detail.duration_hours ?? baseDuration)) : 0;
      const isOpt = mode > 0 || durDiff > 0.01 || (t.is_ai_optimized === true);

      return {
        id: t.id,
        task_id: taskKey,
        name: t.name || t.task_name || `Task ${t.id}`,
        status: t.status || 'Planning',
        start: Number(start.toFixed(1)),
        end: Number(end.toFixed(1)),
        duration: Number(duration.toFixed(1)),
        baselineStart: t.baseline_start ? t.baseline_start.split('T')[0] : null,
        isCritical: Boolean(monte_carlo?.criticality_indices && (monte_carlo.criticality_indices[t.id] > 0.5 || monte_carlo.criticality_indices[t.task_id] > 0.5)),
        isOptimized: isOpt,
        optimizedDetail: detail
      };
    });

    gantt.sort((a, b) => a.start - b.start || a.end - b.end);

    return { combinedData: combined, bellCurveData: bellCurve, ganttData: gantt, maxEndHour: maxEnd };
  }, [tasks, selectedOptionModes, monte_carlo, cpm_static_makespan, projectData, currentOption, displayMakespan]);

  if (loading) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-sm font-bold text-slate-600">Đang tải không gian làm việc kỹ thuật số...</p>
      </div>
    );
  }

  if (errorMsg || !projectData) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-50 p-6">
        <div className="bg-white border border-rose-200 rounded-2xl p-8 max-w-md shadow-lg text-center">
          <AlertTriangle className="mx-auto text-rose-500 mb-4" size={48} />
          <h3 className="text-lg font-black text-slate-800 mb-2">Không thể nạp thông tin dự án</h3>
          <p className="text-xs text-slate-500 mb-6">{errorMsg || "Dữ liệu dự án không tồn tại hoặc đã bị xóa."}</p>
          <button
            onClick={() => navigate('/projects')}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm"
          >
            Quay lại Danh sách Dự án
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen overflow-y-auto bg-slate-50 p-6 custom-scrollbar">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Back to Projects"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-800 tracking-tight flex items-center">
              <Columns className="mr-2 text-blue-600 animate-pulse" size={22} />
              {projectData.project_name || "Digital Twin Workspace"}
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">Merged UI: Live Backend API + Mocks Presentation</p>
          </div>
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

            {/* Main Navigation Tabs */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl shadow-sm mb-6 overflow-hidden">
        {[
          { id: 'overview', label: '1. Overview', icon: Layers },
          { id: 'analysis', label: '2. Analysis', icon: Activity },
          { id: 'assignment', label: '3. Assignment', icon: GitCommit },
          { id: 'ai_pipeline', label: '4. AI Pipeline (Selection)', icon: Sparkles }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setWorkspaceTab(tab.id as any)}
            className={`flex-1 py-3.5 px-2 sm:px-6 font-bold text-[10px] sm:text-sm border-b-2 transition-all flex items-center justify-center gap-1 sm:gap-2 ${
              workspaceTab === tab.id
                ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mb-8">
        {workspaceTab === 'overview' && (
          <OverviewTab 
            tasks={tasks}
            dependencies={dependencies}
            displayMakespan={displayMakespan}
            displayCost={displayCost}
            projectData={projectData}
            ganttData={ganttData}
            maxEndHour={maxEndHour}
          />
        )}
        {workspaceTab === 'analysis' && (
          <AnalysisTab 
            combinedData={combinedData}
            bellCurveData={bellCurveData}
            optionCost={optionCost}
          />
        )}
        {workspaceTab === 'assignment' && (
          <AssignmentTab 
            tasks={tasks}
            dependencies={dependencies}
            projectData={projectData}
            projectId={projectId}
            optionLabel={optionLabel}
            selectedOptionModes={selectedOptionModes}
            currentOption={currentOption}
            criticalityIndices={criticalityIndices}
            ganttData={ganttData}
            maxEndHour={maxEndHour}
            api={api}
            setEditingTask={setEditingTask}
            setIsTaskModalOpen={setIsTaskModalOpen}
            onRefresh={fetchProjectDetails}
          />
        )}
        {workspaceTab === 'ai_pipeline' && (
          <div className="space-y-12">
            {/* Phân vùng 1: Cấu hình AI */}
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-indigo-50/30 border border-indigo-100/50 -z-10"></div>
              <SelectionTab 
                glpoTargetDate={glpoTargetDate}
                setGlpoTargetDate={setGlpoTargetDate}
                glpoTargetHour={glpoTargetHour}
                setGlpoTargetHour={setGlpoTargetHour}
                glpoPenaltyPerDay={glpoPenaltyPerDay}
                setGlpoPenaltyPerDay={setGlpoPenaltyPerDay}
                glpoBonusPerDay={glpoBonusPerDay}
                setGlpoBonusPerDay={setGlpoBonusPerDay}
                glpoMcIterations={glpoMcIterations}
                setGlpoMcIterations={setGlpoMcIterations}
                glpoParetoCount={glpoParetoCount}
                setGlpoParetoCount={setGlpoParetoCount}
                glpoParetoSort={glpoParetoSort}
                setGlpoParetoSort={setGlpoParetoSort}
                handleRunAI={handleRunAI}
                isGlpoLoading={isGlpoLoading}
                projectData={projectData}
              />
            </div>
            
            {/* Đường phân cách */}
            <div className="flex items-center justify-center relative mt-8 mb-4">
              <div className="w-full h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent"></div>
              <div className="absolute bg-slate-50 px-4 text-indigo-400 text-xs font-black uppercase tracking-widest flex items-center gap-2">
                <Sparkles size={14} /> KẾT QUẢ MÔ PHỎNG AI
              </div>
            </div>

            {/* Phân vùng 2: Đánh giá AI */}
            <div className="relative pt-4">
              <EvaluationTab 
                allParetoOptions={allParetoOptions}
                paretoChartType={paretoChartType}
                setParetoChartType={setParetoChartType}
                paretoBarData={paretoBarData}
                selectedGlpoOptionIndex={selectedGlpoOptionIndex}
                setSelectedGlpoOptionIndex={setSelectedGlpoOptionIndex}
                isGlpoLoading={isGlpoLoading}
                isApplyingOption={isApplyingOption}
                handleRestoreBaseline={handleRestoreBaseline}
                handleApplyParetoOption={handleApplyParetoOption}
                handleRunAI={handleRunAI}
              />
            </div>
          </div>
        )}
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
          projectId={projectId}
          projectType={projectData?.type}
        />
      )}

      {isResourceModalOpen && (
        <ResourceManagerModal
          isOpen={isResourceModalOpen}
          onClose={(refresh) => {
            setIsResourceModalOpen(false);
            if (refresh) fetchProjectDetails();
          }}
          projectId={projectId || ''}
          initialResources={projectData?.constraint_resources || []}
        />
      )}

      {isTimeModalOpen && (
        <TimeManagerModal
          isOpen={isTimeModalOpen}
          onClose={(refresh) => {
            setIsTimeModalOpen(false);
            if (refresh) fetchProjectDetails();
          }}
          projectId={projectId || ''}
          initialTimeConstraint={projectData.constraint_time || {}}
          projectData={projectData}
        />
      )}

      {toast && (
        <div className={`fixed bottom-5 right-5 px-4 py-3 rounded-lg shadow-lg text-white font-bold text-sm transition-all duration-300 transform translate-y-0 z-[100] flex items-center gap-2 ${toast.type === 'success' ? 'bg-emerald-600' : toast.type === 'error' ? 'bg-rose-600' : 'bg-blue-600'
          }`}>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
};

export default Workspace;

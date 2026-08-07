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
        alert("Mã dự án không hợp lệ.");
        return;
      }
      const { predecessor_id, dependency_type, lag_days, stagedResources, ...taskData } = data;
      let newTaskId = editingTask ? (editingTask.task_id || editingTask.id) : null;

      if (editingTask && newTaskId) {
        await api.updateTask(projectId, String(newTaskId), taskData);
      } else {
        const randStr = Math.random().toString(36).substr(2, 6);
        newTaskId = `${projectId}_T-${randStr}`;
        await api.createTask(projectId, { id: newTaskId, ...taskData });
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
        const oldEdge = projectData?.constraint_logic?.find((e: any) => e.successor_id === newTaskId);
        try {
          if (predecessor_id) {
            if (oldEdge && oldEdge.predecessor_id !== predecessor_id) {
              await api.deleteLogicConstraint(projectId, oldEdge.predecessor_id, newTaskId);
            }
            if (!oldEdge || oldEdge.predecessor_id !== predecessor_id || oldEdge.dependency_type !== dependency_type || oldEdge.lag_days !== lag_days) {
              if (oldEdge && oldEdge.predecessor_id === predecessor_id) {
                await api.deleteLogicConstraint(projectId, oldEdge.predecessor_id, newTaskId);
              }
              await api.createLogicConstraint(projectId, {
                predecessor_id: predecessor_id,
                successor_id: newTaskId,
                dependency_type: dependency_type || 'FS',
                lag_days: lag_days || 0
              });
            }
          } else if (!predecessor_id && oldEdge) {
            await api.deleteLogicConstraint(projectId, oldEdge.predecessor_id, newTaskId);
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
        setSelectedGlpoOptionIndex(0);
        setActiveTab('pareto');
        setMainPageTab('comparison');
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

  const [mainPageTab, setMainPageTab] = useState<'details' | 'comparison'>('details');
  const [paretoChartType, setParetoChartType] = useState<'scatter' | 'bar'>('scatter');
  const [glpoResult, setGlpoResult] = useState<any>(null);
  const [selectedGlpoOptionIndex, setSelectedGlpoOptionIndex] = useState<number>(0);
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
        setSelectedGlpoOptionIndex(0);
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
  const cpm_static_makespan = projectData?.metadata_json?.simulation_results?.cpm_static_makespan || (projectData?.tasks?.length * 5) || 0;
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

    const getTaskDurationHours = (t: any) => {
      if (t.duration_hours !== undefined && t.duration_hours !== null && parseFloat(t.duration_hours) > 0) {
        return parseFloat(t.duration_hours);
      }
      if (t.most_probable_duration) return t.most_probable_duration;
      const d_d = parseFloat(t.duration_days) || 0;
      const d_h = parseFloat(t.duration_hours) || 0;
      const dur = d_d * agendaHours + d_h;
      return dur > 0 ? dur : agendaHours;
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
      const baseTaskDuration = getTaskDurationHours(t);
      const durationHours = mode === 1 ? Math.round(baseTaskDuration / 1.5) : mode === 2 ? Math.round(baseTaskDuration / 2.0) : baseTaskDuration;

      const baseTaskCost = (t.total_cost !== undefined && t.total_cost !== null)
        ? parseFloat(t.total_cost)
        : t.normal_cost || t.internal_labor_cost || 0;
      const cost = mode === 1 ? (t.crash_cost || baseTaskCost * 1.25) : mode === 2 ? (t.outsource_cost || baseTaskCost * 1.5) : baseTaskCost;

      let taskStartMs = earliestStartMs;
      if (t.baseline_start) {
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

    const mean = monte_carlo?.mean_makespan || cpm_static_makespan || (maxProjectHour > 0 ? maxProjectHour : 500);
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

    // 5. Gantt Chart (Top 20 Tasks)
    const cpSatSchedule = simulationResults?.cp_sat_schedule?.schedule || {};
    const displayGanttTasks = tasks.slice(0, 20);

    let maxEnd = 1;

    const gantt = displayGanttTasks.map((t: any) => {
      const sched = cpSatSchedule[t.id] || cpSatSchedule[t.task_id];
      let start = 0;
      let duration = getTaskDurationHours(t);

      if (sched) {
        start = sched.start;
        duration = Math.max(1, sched.end - sched.start);
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
      const taskIdStr = String(t.task_id || t.id);
      const isOpt = parseFloat(t.overtime || 0) > 0 || appliedIds.includes(taskIdStr) || appliedIds.includes(String(t.id));
      const detail = appliedDetails[taskIdStr] || appliedDetails[String(t.id)] || null;

      return {
        id: t.id,
        task_id: taskIdStr,
        name: t.name || t.task_name || `Task ${t.id}`,
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
  }, [tasks, selectedOptionModes, monte_carlo, cpm_static_makespan, projectData]);

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
            onClick={handleRunAI}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-all flex items-center"
            disabled={projectData?.status === 'Simulating'}
          >
            <Zap className="mr-2" size={16} />
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

      {/* Main Navigation Tabs (Trang 1 vs Trang 2) */}
      <div className="flex border-b border-slate-200 bg-white rounded-xl shadow-sm mb-6 overflow-hidden">
        <button
          onClick={() => setMainPageTab('details')}
          className={`flex-1 py-3.5 px-6 font-bold text-sm border-b-2 transition-all flex items-center justify-center gap-2 ${mainPageTab === 'details'
              ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50'
              : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
        >
          <Layers size={18} />
          Trang 1: Chi tiết Dự án & Đồ thị
        </button>
        <button
          onClick={() => setMainPageTab('comparison')}
          className={`flex-1 py-3.5 px-6 font-bold text-sm border-b-2 transition-all flex items-center justify-center gap-2 ${mainPageTab === 'comparison'
              ? 'border-indigo-600 text-indigo-600 bg-indigo-50/50'
              : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
        >
          <Activity size={18} />
          Trang 2: Bảng So sánh & Biểu đồ Phương án Tối ưu (Pareto)
          {allParetoOptions.length > 0 && (
            <span className="bg-indigo-600 text-white text-[11px] font-black px-2 py-0.5 rounded-full animate-pulse">
              {allParetoOptions.length} PA
            </span>
          )}
        </button>
      </div>

      {mainPageTab === 'comparison' && (
        <div className="space-y-6 animate-fadeIn mb-8">
          {/* Header Banner */}
          <div className="bg-white border border-indigo-200 rounded-xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gradient-to-r from-indigo-50/70 to-white">
            <div>
              <h2 className="text-lg font-black text-slate-800 flex items-center gap-2">
                <Activity className="text-indigo-600" size={22} />
                Bảng So sánh Chi tiết & Biểu đồ Tối ưu Pareto Frontier (GLPO AI + OR)
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Tự động tối ưu hóa 3 mục tiêu độc lập: Rút ngắn thời gian (Makespan), Giảm chi phí ròng (Net Cost) và Giảm rủi ro trễ hạn.
              </p>
            </div>
            <button
              onClick={handleRunAI}
              disabled={isGlpoLoading}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm flex items-center gap-2 shrink-0"
            >
              <Zap size={16} />
              {isGlpoLoading ? 'Đang chạy AI...' : 'Chạy lại Tối ưu AI'}
            </button>
          </div>

          {/* Pareto Frontier Scatter / Bar Chart */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
              <div>
                <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-2">
                  <Sparkles className="text-amber-500" size={18} />
                  Biểu đồ Pareto Frontier (Thời gian vs Chi phí Ròng)
                </h3>
                <p className="text-xs text-slate-500">Mỗi điểm tròn đại diện cho 1 phương án tối ưu. Bấm vào điểm để chọn phương án.</p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <div className="bg-slate-100 p-1 rounded-lg flex gap-1">
                  <button
                    onClick={() => setParetoChartType('scatter')}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition ${paretoChartType === 'scatter' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                      }`}
                  >
                    📈 Đồ thị Pareto
                  </button>
                  <button
                    onClick={() => setParetoChartType('bar')}
                    className={`px-3 py-1 text-xs font-bold rounded-md transition ${paretoChartType === 'bar' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                      }`}
                  >
                    📊 Cột So sánh
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
                        name="Thời gian"
                        unit="h"
                        stroke="#94a3b8"
                        fontSize={11}
                        domain={['dataMin - 15', 'dataMax + 15']}
                        tickFormatter={(v) => `${v}h`}
                      />
                      <YAxis
                        type="number"
                        dataKey="total_cost"
                        name="Chi phí"
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
                                <p>Thời gian: <span className="font-bold text-indigo-300">{d.makespan_hours}h</span> (Đến ngày: {d.finish_datetime ? new Date(d.finish_datetime).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'})</p>
                                <p>Chi phí gốc: <span className="text-slate-300">${Number(d.base_project_cost || d.cost || 0).toLocaleString()}</span></p>
                                <p>Chi phí ròng: <span className="font-bold text-emerald-400">${Number(d.total_cost || d.cost || 0).toLocaleString()}</span></p>
                                <p>Rủi ro trễ: <span className="font-bold text-rose-400">{d.risk_pct}%</span></p>
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
                      <YAxis yAxisId="time" orientation="right" tickFormatter={(v) => `${v}h`} stroke="#059669" fontSize={11} domain={['dataMin - 50', 'dataMax + 50']} />
                      <Tooltip
                        formatter={(value: any, name: any) => {
                          if (name === 'cost') return [`$${(value * 1000).toLocaleString()}`, 'Chi phí Ròng'];
                          if (name === 'makespan') return [`${value}h`, 'Thời gian'];
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
                <p className="text-sm font-semibold">Chưa có dữ liệu biểu đồ Pareto.</p>
                <p className="text-xs mt-1">Hãy bấm nút "Run AI Pipeline" phía trên để tạo biểu đồ và bảng so sánh phương án.</p>
              </div>
            )}
          </div>

          {/* Pareto Comparison Table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center flex-wrap gap-2">
              <h3 className="font-extrabold text-slate-800 text-sm">Bảng So sánh Chi tiết Các Phương án Pareto (Pareto Solutions Table)</h3>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleRestoreBaseline}
                  disabled={isApplyingOption}
                  className="bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-sm"
                  title="Khôi phục dữ liệu ban đầu (Baseline Gốc) của dự án"
                >
                  🔄 Khôi phục Baseline Gốc
                </button>
                <span className="text-xs text-slate-500 font-medium">Bấm "Áp dụng PA này" để áp dụng lên CSDL</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-slate-600 bg-slate-100 uppercase font-bold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">STT</th>
                    <th className="px-4 py-3">Tên Phương án</th>
                    <th className="px-4 py-3 text-right">Thời gian (Hours)</th>
                    <th className="px-4 py-3 text-right">Hoàn thành Ngày</th>
                    <th className="px-4 py-3 text-right">Chi phí Gốc ($)</th>
                    <th className="px-4 py-3 text-right">Thưởng / Phạt ($)</th>
                    <th className="px-4 py-3 text-right">Chi phí Ròng ($)</th>
                    <th className="px-4 py-3 text-right">Rủi ro Trễ</th>
                    <th className="px-4 py-3 text-center">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {allParetoOptions.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="text-center py-8 text-slate-400">
                        Chưa có phương án tối ưu nào được tạo. Vui lòng bấm "Run AI Pipeline" để tạo phương án.
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
                        adjustStr = `+$${Number(penCost).toLocaleString()} (Phạt)`;
                        adjustClass = "text-rose-600 font-bold";
                      } else if (bonusAmt > 0) {
                        adjustStr = `-$${Number(bonusAmt).toLocaleString()} (Thưởng)`;
                        adjustClass = "text-emerald-600 font-bold";
                      }

                      return (
                        <tr
                          key={idx}
                          className={`border-b border-slate-100 transition ${isSelected ? 'bg-indigo-50/70 font-semibold border-l-4 border-l-indigo-600' : 'hover:bg-slate-50'
                            }`}
                        >
                          <td className="px-4 py-3 font-bold text-slate-500">#{idx + 1}</td>
                          <td className="px-4 py-3 font-bold text-slate-800">{opt.option_name || `Phương án ${idx + 1}`}</td>
                          <td className="px-4 py-3 text-right font-black text-indigo-600">{opt.makespan_hours || opt.makespan}h</td>
                          <td className="px-4 py-3 text-right text-slate-600">{opt.finish_datetime ? new Date(opt.finish_datetime).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}</td>
                          <td className="px-4 py-3 text-right text-slate-600">${Number(baseCost).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                          <td className={`px-4 py-3 text-right ${adjustClass}`}>{adjustStr}</td>
                          <td className="px-4 py-3 text-right font-extrabold text-emerald-600">${Number(netCost).toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                          <td className="px-4 py-3 text-right font-bold text-rose-500">{Number(riskPct).toFixed(1)}%</td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleApplyParetoOption(idx, opt)}
                              disabled={isApplyingOption}
                              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition shadow-sm flex items-center gap-1 mx-auto ${isSelected
                                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                }`}
                            >
                              {isSelected ? '✓ Đã áp dụng' : 'Áp dụng PA này'}
                            </button>
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
      )}

      {mainPageTab === 'details' && (
        <>
          {/* Contract & GLPO Configuration Panel */}
          <div className="bg-white border border-indigo-100 rounded-xl p-4 shadow-sm mb-6 bg-gradient-to-r from-indigo-50/50 to-white">
            <div className="flex items-center justify-between mb-3 border-b border-indigo-50 pb-2">
              <div className="flex items-center gap-2">
                <Sliders className="text-indigo-600" size={18} />
                <h3 className="font-extrabold text-slate-800 text-sm">Cấu hình Tối ưu Hóa AI & Hợp đồng (GLPO Contract Parameters)</h3>
              </div>
              <span className="text-xs text-indigo-700 font-bold bg-indigo-100 px-2 py-0.5 rounded-full">
                HGT 3-Node + Hybrid Readout
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Hạn chót Mục tiêu (00-23h)</label>
                <div className="flex gap-1">
                  <input
                    type="date"
                    value={glpoTargetDate}
                    onChange={e => setGlpoTargetDate(e.target.value)}
                    className="w-3/5 border border-slate-300 rounded px-1.5 py-1.5 font-semibold text-xs focus:ring-1 focus:ring-indigo-500 bg-white text-slate-800 cursor-pointer"
                  />
                  <select
                    value={glpoTargetHour}
                    onChange={e => setGlpoTargetHour(e.target.value)}
                    className="w-2/5 border border-slate-300 rounded px-1 py-1.5 font-semibold text-xs bg-white text-slate-800 cursor-pointer"
                  >
                    {Array.from({ length: 24 }, (_, i) => {
                      const h = i < 10 ? `0${i}` : `${i}`;
                      return <option key={h} value={`${h}:00`}>{h}:00</option>;
                    })}
                  </select>
                </div>
              </div>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Phạt Trễ ($/ngày)</label>
                <input
                  type="number" step="50"
                  value={glpoPenaltyPerDay}
                  onChange={e => setGlpoPenaltyPerDay(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 font-semibold focus:ring-1 focus:ring-indigo-500 bg-white"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Thưởng Sớm ($/ngày)</label>
                <input
                  type="number" step="50"
                  value={glpoBonusPerDay}
                  onChange={e => setGlpoBonusPerDay(Number(e.target.value))}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 font-semibold focus:ring-1 focus:ring-indigo-500 bg-white"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Số vòng Monte Carlo</label>
                <input
                  type="number" step="100" min="100"
                  value={glpoMcIterations}
                  onChange={e => setGlpoMcIterations(Math.max(1, Number(e.target.value)))}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 font-semibold focus:ring-1 focus:ring-indigo-500 bg-white"
                  placeholder="1000"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Số PA Pareto</label>
                <input
                  type="number" step="1" min="1"
                  value={glpoParetoCount}
                  onChange={e => setGlpoParetoCount(Math.max(1, Number(e.target.value)))}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 font-semibold focus:ring-1 focus:ring-indigo-500 bg-white"
                  placeholder="20"
                />
              </div>
              <div>
                <label className="block font-bold text-slate-700 mb-1">Sắp xếp Pareto</label>
                <select
                  value={glpoParetoSort}
                  onChange={e => setGlpoParetoSort(e.target.value)}
                  className="w-full border border-slate-300 rounded px-2 py-1.5 font-semibold bg-white"
                >
                  <option value="makespan_hours">Theo Thời gian</option>
                  <option value="total_cost">Theo Chi phí</option>
                  <option value="risk_score">Theo Rủi ro</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            {projectData?.status === 'Error' && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3 shadow-sm animate-fadeIn">
                <AlertTriangle className="text-rose-600 shrink-0 mt-0.5" size={20} />
                <div className="flex-1">
                  <h4 className="font-bold text-rose-800 text-sm">Phát hiện lỗi trong quá trình chạy mô phỏng AI</h4>
                  <p className="text-xs text-rose-600 mt-1">
                    AI Pipeline đã dừng do lỗi tính toán hoặc cấu trúc đồ thị. Vui lòng kiểm tra lại ràng buộc logic và tài nguyên của dự án.
                  </p>
                  {projectData.metadata_json?.simulation_error && (
                    <div className="mt-3 bg-slate-950 text-rose-400 font-mono text-[10px] p-3 rounded-lg border border-slate-800 max-h-32 overflow-y-auto whitespace-pre-wrap">
                      {projectData.metadata_json.simulation_error}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard title="Số lượng Công việc" value={`${tasks.length} công việc`} icon={Layers} color="bg-blue-500" />
              <StatCard title="Ràng buộc Phụ thuộc" value={`${dependencies.length} liên kết`} icon={GitCommit} color="bg-emerald-500" />
              <StatCard title="Thời gian Hoàn thành (Makespan)" value={`${displayMakespan.toFixed(0)}h (~${(displayMakespan / 24).toFixed(0)} ngày)`} icon={Clock} color="bg-amber-500" />
              <StatCard title="Tổng Chi phí Dự án (TGC)" value={`$${(displayCost / 1000).toFixed(1)}k`} icon={Activity} color="bg-purple-500" />
            </div>

            <div className="w-full h-[620px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col relative overflow-hidden">
              <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center z-10 shrink-0">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-700">Project Network Graph (Digital Twin DAG)</span>
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
                    appliedTaskIds={projectData?.metadata_json?.applied_task_ids || []}
                    appliedTaskDetails={projectData?.metadata_json?.applied_task_details || {}}
                    onConnectEdge={async (source, target) => {
                      try {
                        if (!projectId) return;
                        await api.createLogicConstraint(projectId, {
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
                        if (!projectId) return;
                        await api.deleteTask(projectId, taskId);
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
                <div className="mb-4 shrink-0 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-slate-800">Financial S-Curve & Task Density</h3>
                    <p className="text-xs text-slate-500">Chi tiêu lũy kế và mật độ công việc song song được cập nhật tự động</p>
                  </div>
                  <div className="text-right text-xs bg-emerald-50 px-2 py-1 border border-emerald-100 rounded text-emerald-700 font-bold">
                    TGC: ${Number(optionCost).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="h-64">
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
                        if (name === 'dailyCost') return [`$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Chi phí ngày'];
                        if (name === 'cumulativeCost') return [`$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Chi phí lũy kế'];
                        return [`${value} công việc`, 'Số CV song song'];
                      }} labelFormatter={(label) => `Ngày: ${label}`} />
                      <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px' }} />
                      <Bar yAxisId="cost" dataKey="dailyCost" name="dailyCost" fill="#cbd5e1" barSize={14} radius={[2, 2, 0, 0]} />
                      <Area yAxisId="cost" type="monotone" dataKey="cumulativeCost" name="cumulativeCost" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCumulative)" />
                      <Line yAxisId="density" type="monotone" dataKey="activeCount" name="activeCount" stroke="#10b981" strokeWidth={2.5} dot={{ r: 2.5, fill: '#10b981' }} activeDot={{ r: 5 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="lg:col-span-1 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-[400px] flex flex-col">
                <div className="mb-4 shrink-0">
                  <h3 className="font-bold text-slate-800">Monte Carlo Risk Analysis</h3>
                  <p className="text-xs text-slate-500">Phân phối xác suất thời gian hoàn thành (Giờ)</p>
                </div>
                <div className="h-64">
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
                        formatter={(val: any) => [`${Number(val).toFixed(1)}%`, 'Mật độ xác suất']}
                        labelFormatter={(val) => `Thời lượng: ${val}h (${(Number(val) / 8).toFixed(1)} ngày)`}
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
                        <div key={task.id} className={`relative h-8 mb-2 flex items-center group ${task.isOptimized ? 'bg-amber-50/60 rounded-lg border-l-4 border-l-amber-500' : ''}`}>
                          <div className={`w-32 shrink-0 text-xs truncate pr-2 font-medium ${task.isOptimized ? 'text-amber-800 font-bold' : 'text-slate-600'}`} title={task.name}>
                            {task.isOptimized && <span className="mr-0.5">⚡</span>}{task.name}
                          </div>
                          <div className="flex-1 relative h-full bg-slate-200/50 rounded-md">
                            <div
                              className={`absolute top-1 bottom-1 rounded-md shadow-sm transition-all duration-300 flex items-center px-2 overflow-hidden ${
                                task.isOptimized
                                  ? 'bg-amber-500 text-white ring-1 ring-amber-400'
                                  : task.isCritical
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
                            <strong>{task.name}</strong>{task.isOptimized && <span className="ml-1 text-amber-300 font-bold">⚡ AI Optimized</span>}<br />
                            Start: {task.start.toFixed(1)}h | End: {task.end.toFixed(1)}h
                            {task.optimizedDetail && (
                              <><br />Baseline: {task.optimizedDetail.old_duration}h → {task.optimizedDetail.new_duration}h
                              {task.optimizedDetail.overtime_hours_per_day > 0 && <> | OT: +{task.optimizedDetail.overtime_hours_per_day}h/ngày</>}
                              {task.optimizedDetail.overtime_cost > 0 && <> | Chi phí OT: ${task.optimizedDetail.overtime_cost.toFixed(0)}</>}
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

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
          onClose={() => setIsResourceModalOpen(false)}
          projectId={projectId || ''}
          initialResources={projectData?.constraint_resources || []}
        />
      )}

      {isTimeModalOpen && (
        <TimeManagerModal
          isOpen={isTimeModalOpen}
          onClose={() => setIsTimeModalOpen(false)}
          projectId={projectId || ''}
          initialTimeConstraint={projectData.constraint_time || {}}
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

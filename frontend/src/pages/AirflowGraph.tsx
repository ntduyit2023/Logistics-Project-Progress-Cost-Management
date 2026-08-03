import React, { useState, useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Panel,
  MarkerType,
} from 'reactflow';
import dagre from '@dagrejs/dagre';
import 'reactflow/dist/style.css';
import { X, Clock, DollarSign, Calendar, Activity, AlertTriangle, Sliders, SlidersHorizontal, Sparkles } from 'lucide-react';
import TaskNode from '../components/graph/TaskNode';

const nodeTypes = {
  taskNode: TaskNode,
};

const getLayoutedElements = (
  nodes: any[],
  edges: any[],
  direction = 'LR',
  horizontalSpacing = 300,
  verticalSpacing = 80
) => {
  if (nodes.length === 0) return { nodes, edges };

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: Math.max(30, Math.round(verticalSpacing * 1.5)),
    ranksep: Math.max(80, Math.round(horizontalSpacing + 100)),
    edgesep: 50,
    ranker: 'network-simplex'
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 220, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    if (nodeWithPosition) {
      node.targetPosition = isHorizontal ? 'left' : 'top';
      node.sourcePosition = isHorizontal ? 'right' : 'bottom';
      node.position = {
        x: nodeWithPosition.x - 220 / 2,
        y: nodeWithPosition.y - 80 / 2,
      };
    }
  });

  return { nodes, edges };
};

interface AirflowGraphProps {
  projectId?: string;
  tasks: any[];
  dependencies: any[];
  onConnectEdge?: (source: string, target: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onEditTask?: (task: any) => void;
  selectedOptionModes?: number[];
  criticalityIndices?: Record<string, number>;
  appliedTaskIds?: string[];
  appliedTaskDetails?: Record<string, any>;
}

const AirflowGraph: React.FC<AirflowGraphProps> = ({
  projectId, tasks, dependencies, onConnectEdge, onDeleteTask, onEditTask, selectedOptionModes, criticalityIndices, appliedTaskIds = [], appliedTaskDetails = {}
}) => {
  const [horizSpacing, setHorizSpacing] = useState(300);
  const [vertSpacing, setVertSpacing] = useState(80);
  const [showSpacingConfig, setShowSpacingConfig] = useState(false);

  // Extract real features from task schema
  const getTaskGroups = (task: any) => {
    const hubInfo: Record<string, any> = {};
    if (task.duration_months && parseFloat(task.duration_months) > 0) hubInfo["duration_months"] = task.duration_months;
    if (task.duration_weeks && parseFloat(task.duration_weeks) > 0) hubInfo["duration_weeks"] = task.duration_weeks;
    if (task.duration_days && parseFloat(task.duration_days) > 0) hubInfo["duration_days"] = task.duration_days;
    if (task.duration_hours && parseFloat(task.duration_hours) > 0) hubInfo["duration_hours"] = task.duration_hours;

    if (Object.keys(hubInfo).length === 0) {
      hubInfo["duration_hours"] = task.duration_hours || task.duration || 0;
    }

    return {
      "Hub": hubInfo,
      "Resource Cost": {
        "labor": task.labor ?? task.internal_labor_cost,
        "material": task.material ?? task.material_cost,
        "equipment": task.equipment ?? task.equipment_fuel_cost,
        "energy": task.energy,
        "testing_inspection": task.testing_inspection ?? task.qa_qc_cost
      },
      "Overhead Cost": {
        "project_management": task.project_management,
        "facility": task.facility ?? task.facility_rent,
        "utilities": task.utilities ?? task.utilities_cost,
        "communication": task.communication ?? task.communication_cost,
        "training": task.training ?? task.training_cost,
        "quality_management": task.quality_management
      },
      "Time-dependent Cost": {
        "overtime": task.overtime ?? task.overtime_cost,
        "delay_penalty": task.delay_penalty,
        "inventory_holding": task.inventory_holding ?? task.holding_cost,
        "waiting_cost": task.waiting_cost,
        "idle_resource": task.idle_resource,
        "revenue_delay": task.revenue_delay,
        "expediting": task.expediting
      },
      "Risk & Compliance Cost": {
        "insurance": task.insurance ?? task.insurance_cost,
        "rework": task.rework,
        "warranty": task.warranty ?? task.warranty_cost,
        "litigation": task.litigation,
        "regulatory_compliance": task.regulatory_compliance ?? task.licensing_cost,
        "contingency_reserve": task.contingency_reserve,
        "management_reserve": task.management_reserve
      },
      "Supply Chain & External Cost": {
        "transportation": task.transportation ?? task.international_freight,
        "ordering": task.ordering,
        "packaging": task.packaging,
        "reverse_logistics": task.reverse_logistics,
        "customs": task.customs,
        "supplier_coordination": task.supplier_coordination
      },
      "Strategic & Financial Cost": {
        "opportunity_cost": task.opportunity_cost,
        "capital_cost": task.capital_cost,
        "financing_cost": task.financing_cost,
        "npv_loss": task.npv_loss,
        "esg_cost": task.esg_cost,
        "carbon_tax": task.carbon_tax,
        "reputation_cost": task.reputation_cost
      }
    };
  };

  const { initialNodesLayout, initialEdgesLayout } = useMemo(() => {
    if (!tasks || tasks.length === 0) return { initialNodesLayout: [], initialEdgesLayout: [] };

    const normalizeId = (val: any): string => {
      if (val === undefined || val === null) return '';
      let str = String(val).trim();
      if (str.endsWith('.0')) str = str.slice(0, -2);
      return str;
    };

    const getCanonicalId = (t: any): string => {
      if (!t) return '';
      return normalizeId(t.task_id || t.wbs || t.task_code || t.id);
    };

    const displayTasks = tasks;

    // Build dictionary mapping any task identifier (id, task_id, wbs) -> canonical string ID
    const taskIdToCanonicalMap = new Map<string, string>();
    displayTasks.forEach((t: any) => {
      const canonical = getCanonicalId(t);
      if (t.id !== undefined && t.id !== null) taskIdToCanonicalMap.set(normalizeId(t.id), canonical);
      if (t.task_id) taskIdToCanonicalMap.set(normalizeId(t.task_id), canonical);
      if (t.wbs) taskIdToCanonicalMap.set(normalizeId(t.wbs), canonical);
      if (t.task_code) taskIdToCanonicalMap.set(normalizeId(t.task_code), canonical);
    });

    const displayTaskIds = new Set(Array.from(taskIdToCanonicalMap.values()));

    const rawNodes = displayTasks.map((task: any, idx: number) => {
      const mode = selectedOptionModes && selectedOptionModes[idx] !== undefined ? selectedOptionModes[idx] : 0;
      const canonicalId = getCanonicalId(task);
      const wbs = task.wbs || (canonicalId.includes("_") ? canonicalId.split("_")[1] : canonicalId);
      const isCritical = (criticalityIndices && (criticalityIndices[canonicalId] > 0.75 || criticalityIndices[task.id] > 0.75)) || task.duration_days > 50;

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
        baseTaskDuration = d_m * 160 + d_w * 40 + d_d * 8 + d_h;
        if (baseTaskDuration <= 0) baseTaskDuration = 10;
      }
      const duration = mode === 1
        ? Math.round(baseTaskDuration / 1.5)
        : mode === 2
          ? Math.round(baseTaskDuration / 2.0)
          : baseTaskDuration;

      const baseTaskCost = (task.total_cost !== undefined && task.total_cost !== null)
        ? parseFloat(task.total_cost)
        : (
          (parseFloat(task.labor || task.internal_labor_cost) || 0) +
          (parseFloat(task.equipment || task.equipment_fuel_cost) || 0) +
          (parseFloat(task.material || task.material_cost) || 0) +
          (parseFloat(task.overtime || task.overtime_cost) || 0) +
          (parseFloat(task.energy) || 0)
        ) || task.normal_cost || 0;

      const cost = mode === 1
        ? (task.crash_cost || baseTaskCost * 1.25)
        : mode === 2
          ? (task.outsource_cost || baseTaskCost * 1.5)
          : baseTaskCost;

      const optDetail = appliedTaskDetails?.[canonicalId] || appliedTaskDetails?.[String(task.id)] || appliedTaskDetails?.[String(task.task_id)];

      return {
        id: canonicalId,
        type: 'taskNode',
        position: { x: 0, y: 0 },
        data: {
          task_id: task.task_id || task.id,
          task_label: canonicalId,
          wbs,
          task_name: task.task_name || task.name || canonicalId,
          duration: optDetail ? optDetail.new_duration : duration,
          total_cost: cost,
          base_duration: optDetail ? optDetail.old_duration : baseTaskDuration,
          base_cost: baseTaskCost,
          is_critical: isCritical,
          is_ai_optimized: Boolean(task.is_ai_optimized || (task.overtime && parseFloat(task.overtime) > 0) || appliedTaskIds.includes(canonicalId) || appliedTaskIds.includes(String(task.id)) || appliedTaskIds.includes(String(task.task_id))),
          overtime_cost: optDetail ? optDetail.overtime_cost : parseFloat(task.overtime || task.overtime_cost || 0),
          overtime_hours_per_day: optDetail ? optDetail.overtime_hours_per_day : parseFloat(task.overtime_hours_per_day || task.overtime_hours || 0),
          resources: task.resources || [],
          features: getTaskGroups(task),
          baseline_start: optDetail ? optDetail.baseline_start : task.baseline_start,
          baseline_end: optDetail ? optDetail.baseline_end : task.baseline_end,
          // === FIELDS MỚI ===
          base_effort_hours: optDetail?.base_effort_hours ?? parseFloat(task.duration_hours || 0),
          extra_workers: optDetail?.extra_workers ?? 0,
          crashing_strategy: optDetail?.crashing_strategy ?? 'Normal',
          labor_ot_premium: optDetail?.labor_ot_premium ?? 0,
          equipment_ot_extra: optDetail?.equipment_ot_extra ?? 0,
          energy_ot_extra: optDetail?.energy_ot_extra ?? 0,
          added_resources_cost: optDetail?.added_resources_cost ?? 0
        },
      };
    });

    const rawEdges = dependencies
      .map((dep: any) => {
        const rawSource = dep.predecessor_id || dep.source_id || dep.source || dep.pred || (Array.isArray(dep) ? dep[0] : '');
        const rawTarget = dep.successor_id || dep.target_id || dep.target || dep.succ || (Array.isArray(dep) ? dep[1] : '');
        const sourceId = taskIdToCanonicalMap.get(normalizeId(rawSource)) || normalizeId(rawSource);
        const targetId = taskIdToCanonicalMap.get(normalizeId(rawTarget)) || normalizeId(rawTarget);
        return { sourceId, targetId };
      })
      .filter((dep) => dep.sourceId && dep.targetId && displayTaskIds.has(dep.sourceId) && displayTaskIds.has(dep.targetId))
      .map((dep) => ({
        id: `e-${dep.sourceId}-${dep.targetId}`,
        source: dep.sourceId,
        target: dep.targetId,
        type: 'default',
        animated: false,
        style: { stroke: '#64748b', strokeWidth: 2, opacity: 0.7 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: '#64748b',
        },
      }));

    const layouted = getLayoutedElements(rawNodes, rawEdges, 'LR', horizSpacing, vertSpacing);
    return { initialNodesLayout: layouted.nodes, initialEdgesLayout: layouted.edges };
  }, [tasks, dependencies, selectedOptionModes, criticalityIndices, horizSpacing, vertSpacing, appliedTaskIds, appliedTaskDetails]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodesLayout);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdgesLayout);
  const [selectedTask, setSelectedTask] = useState<any>(null);

  useEffect(() => {
    setNodes(initialNodesLayout);
    setEdges(initialEdgesLayout);
    setSelectedTask(null);
  }, [initialNodesLayout, initialEdgesLayout, setNodes, setEdges]);

  const onNodeClick = useCallback((_: any, node: any) => {
    setSelectedTask(node.data);
  }, []);

  const onConnect = useCallback((connection: any) => {
    if (onConnectEdge && connection.source && connection.target) {
      onConnectEdge(connection.source, connection.target);
    }
  }, [onConnectEdge]);

  return (
    <div className="w-full h-full min-h-[550px] bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden relative flex flex-col animate-fadeIn">
      <div className="w-full h-full min-h-[550px] flex-1 relative" style={{ width: '100%', height: '100%', minHeight: '550px' }}>
        <ReactFlow
          style={{ width: '100%', height: '100%', minHeight: '550px' }}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.1 }}
          minZoom={0.05}
          maxZoom={1.5}
        >
          <Background color="#f1f5f9" gap={16} />
          <Controls />
          <Panel position="top-left" className="bg-white/95 backdrop-blur-sm p-3 rounded-lg shadow-md border border-slate-200 text-sm m-4 z-10">
            <h3 className="font-bold text-slate-800 text-lg mb-1">{projectId || 'Project Graph'}</h3>
            <p className="text-slate-500 mb-3">{tasks.length} Tasks • {dependencies.length} Dependencies</p>
            <div className="space-y-1.5">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-rose-50 border border-rose-500 rounded-sm mr-2"></div>
                <span className="text-slate-700 text-xs font-medium">Critical Path Task (Găng)</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-amber-50 border border-amber-500 rounded-sm mr-2"></div>
                <span className="text-slate-700 text-xs font-medium">Crashed Task (Tăng tốc)</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-violet-50 border border-violet-500 rounded-sm mr-2"></div>
                <span className="text-slate-700 text-xs font-medium">Outsourced Task (Thuê ngoài)</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-white border border-slate-300 rounded-sm mr-2"></div>
                <span className="text-slate-700 text-xs font-medium">Standard Task (Thường)</span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 mt-3 italic border-t pt-1.5">
              * Hiển thị toàn bộ mạng lưới công việc của dự án
            </p>
          </Panel>

          <Panel position="bottom-right" className="flex items-center gap-2 bg-white/95 backdrop-blur-md p-1.5 rounded-2xl shadow-xl border border-slate-200/80 mb-4 mr-4">
            <div className="relative">
              <button
                onClick={() => setShowSpacingConfig(!showSpacingConfig)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition shadow-sm ${
                  showSpacingConfig ? 'bg-indigo-600 text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
                title="Cấu hình khoảng cách giữa các Node"
              >
                <SlidersHorizontal size={14} />
                <span>Khoảng cách Node</span>
              </button>

              {showSpacingConfig && (
                <div className="absolute bottom-full right-0 mb-3 w-64 bg-white p-4 rounded-2xl shadow-2xl border border-slate-200 space-y-3.5 text-xs animate-fadeIn z-50">
                  <div className="flex justify-between items-center border-b pb-2">
                    <h4 className="font-extrabold text-slate-800 flex items-center gap-1.5">
                      <SlidersHorizontal size={14} className="text-indigo-600" />
                      Giãn cách Sơ đồ Network
                    </h4>
                    <button onClick={() => setShowSpacingConfig(false)} className="text-slate-400 hover:text-slate-600">
                      <X size={14} />
                    </button>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-600 font-medium">
                      <span>Khoảng cách Ngang:</span>
                      <span className="font-bold font-mono text-indigo-600">{horizSpacing}px</span>
                    </div>
                    <input
                      type="range"
                      min="100"
                      max="600"
                      step="20"
                      value={horizSpacing}
                      onChange={(e) => setHorizSpacing(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-slate-600 font-medium">
                      <span>Khoảng cách Dọc:</span>
                      <span className="font-bold font-mono text-indigo-600">{vertSpacing}px</span>
                    </div>
                    <input
                      type="range"
                      min="20"
                      max="300"
                      step="10"
                      value={vertSpacing}
                      onChange={(e) => setVertSpacing(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Drawer */}
      <div
        className={`absolute top-0 right-0 h-full w-96 bg-white shadow-2xl border-l border-slate-200 transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${selectedTask ? 'translate-x-0' : 'translate-x-full'
          }`}
      >
        {selectedTask && (
          <>
            <div className={`p-4 flex justify-between items-start border-b ${selectedTask.is_critical ? 'bg-rose-50 border-rose-100' : 'bg-slate-50 border-slate-200'}`}>
              <div>
                <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                  <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-xs font-bold">
                    WBS {selectedTask.wbs}
                  </span>
                  {selectedTask.is_critical && (
                    <span className="px-2 py-0.5 bg-rose-100 text-rose-600 rounded flex items-center text-xs font-bold border border-rose-200">
                      <AlertTriangle size={11} className="mr-1 animate-pulse" /> Critical Path
                    </span>
                  )}
                  {selectedTask.mode === 1 && (
                    <span className="px-2 py-0.5 bg-amber-500 text-white rounded text-xs font-bold">
                      Crashed
                    </span>
                  )}
                  {selectedTask.mode === 2 && (
                    <span className="px-2 py-0.5 bg-violet-600 text-white rounded text-xs font-bold">
                      Outsourced
                    </span>
                  )}
                </div>
                <h2 className="text-sm font-bold text-slate-800 leading-tight pr-4">
                  {selectedTask.task_name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-full transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-4 flex-1 overflow-y-auto custom-scrollbar space-y-5">
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-500 mb-1">
                    <Clock size={13} className="mr-1.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider">Duration</span>
                  </div>
                  <div className="text-lg font-extrabold text-slate-800">{selectedTask.duration} <span className="text-xs font-normal text-slate-500">hours</span></div>
                </div>

                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <div className="flex items-center text-emerald-600 mb-1">
                    <DollarSign size={13} className="mr-1.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider">Cost</span>
                  </div>
                  <div className="text-lg font-extrabold text-slate-800">${Number(selectedTask.total_cost).toLocaleString()}</div>
                </div>
              </div>

              {/* Actions */}
              {(onEditTask || onDeleteTask) && (
                <div className="mb-6 flex gap-3">
                  {onEditTask && <button
                    onClick={() => {
                      const selId = String(selectedTask.task_id || selectedTask.task_label || '');
                      const selWbs = String(selectedTask.wbs || '');
                      const t = tasks.find(x => 
                        String(x.id) === selId || 
                        String(x.task_id) === selId || 
                        String(x.wbs) === selId ||
                        (selWbs && String(x.wbs) === selWbs)
                      ) || selectedTask;
                      if (t) onEditTask(t);
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-lg transition-colors shadow-sm text-xs"
                  >
                    Edit Node
                  </button>}
                  {onDeleteTask && <button
                    onClick={async () => {
                      if (window.confirm("Delete this node?")) {
                        onDeleteTask(selectedTask.task_id || selectedTask.task_label || selectedTask.id);
                      }
                    }}
                    className="flex-1 bg-red-50 hover:bg-red-100 text-red-600 font-bold py-2 rounded-lg border border-red-200 transition-colors"
                  >
                    Delete Node
                  </button>}
                </div>
              )}

              {/* Resource Allocations */}
              {selectedTask.resources && selectedTask.resources.length > 0 && (
                <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100 space-y-2">
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b pb-1">
                    Nhân lực & Thiết bị yêu cầu
                  </div>
                  <div className="space-y-1.5">
                    {selectedTask.resources.map((res: any, rIdx: number) => (
                      <div key={rIdx} className="flex justify-between items-center text-xs">
                        <span className="text-slate-600 font-semibold">{res.resource_id || res.resource_name}</span>
                        <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-blue-200">
                          {res.quantity || res.request_quantity} đơn vị
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Optimization Details Panel */}
              {(selectedTask.is_ai_optimized || selectedTask.crashing_strategy !== 'Normal') && (
                <div className="mb-4 bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 bg-amber-100 rounded-bl-full -mr-4 -mt-4 opacity-50 pointer-events-none"></div>
                  
                  <h3 className="text-sm font-black text-amber-800 mb-3 flex items-center border-b border-amber-200/60 pb-2 relative z-10">
                    <Sparkles size={16} className="mr-2 text-amber-500" />
                    Optimization Details (CP-SAT)
                  </h3>
                  
                  <div className="space-y-2 relative z-10 text-xs">
                    <div className="flex justify-between items-center bg-white/60 p-1.5 rounded border border-amber-100">
                      <span className="text-amber-700 font-medium">Crashing Strategy:</span>
                      <span className="font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded">{selectedTask.crashing_strategy}</span>
                    </div>
                    
                    <div className="flex justify-between items-center bg-white/60 p-1.5 rounded border border-amber-100">
                      <span className="text-amber-700 font-medium">Base Effort:</span>
                      <span className="font-bold text-slate-800">{selectedTask.base_effort_hours}h</span>
                    </div>
                    
                    {selectedTask.extra_workers > 0 && (
                      <div className="flex justify-between items-center bg-emerald-50 p-1.5 rounded border border-emerald-100">
                        <span className="text-emerald-700 font-medium">Extra Workers:</span>
                        <span className="font-bold text-emerald-800">+{selectedTask.extra_workers}</span>
                      </div>
                    )}
                    
                    {(selectedTask.added_resources_cost > 0 || selectedTask.labor_ot_premium > 0 || selectedTask.equipment_ot_extra > 0 || selectedTask.energy_ot_extra > 0) && (
                      <div className="mt-2 pt-2 border-t border-amber-200/50">
                        <p className="text-[10px] font-bold text-amber-800/70 mb-1 uppercase tracking-wider">Chi phí phát sinh</p>
                        {selectedTask.added_resources_cost > 0 && (
                          <div className="flex justify-between items-center py-0.5">
                            <span className="text-slate-600">Thuê thêm (Added Res):</span>
                            <span className="font-bold text-rose-600">+${Number(selectedTask.added_resources_cost).toFixed(0)}</span>
                          </div>
                        )}
                        {selectedTask.labor_ot_premium > 0 && (
                          <div className="flex justify-between items-center py-0.5">
                            <span className="text-slate-600">OT Labor:</span>
                            <span className="font-bold text-rose-600">+${Number(selectedTask.labor_ot_premium).toFixed(0)}</span>
                          </div>
                        )}
                        {selectedTask.equipment_ot_extra > 0 && (
                          <div className="flex justify-between items-center py-0.5">
                            <span className="text-slate-600">OT Equip:</span>
                            <span className="font-bold text-rose-600">+${Number(selectedTask.equipment_ot_extra).toFixed(0)}</span>
                          </div>
                        )}
                        {selectedTask.energy_ot_extra > 0 && (
                          <div className="flex justify-between items-center py-0.5">
                            <span className="text-slate-600">OT Energy:</span>
                            <span className="font-bold text-rose-600">+${Number(selectedTask.energy_ot_extra).toFixed(0)}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Real Task Schema Fields */}
              <div>
                <h3 className="text-sm font-bold text-slate-800 mb-2.5 flex items-center border-b pb-1">
                  <Activity size={16} className="mr-1.5 text-blue-600" />
                  Thông tin chi tiết (Task Details)
                </h3>
                <p className="text-xs text-slate-500 mb-3 italic">
                  Các chỉ số được lấy trực tiếp từ Pydantic Schema của Backend API. Click "Edit Node" để sửa.
                </p>
                <div className="space-y-3">
                  {Object.entries(selectedTask.features || {}).map(([groupName, groupFeats]: any) => (
                    <div key={groupName} className="border border-slate-200 rounded-lg overflow-hidden shadow-sm">
                      <div className="bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 border-b border-slate-200 flex justify-between items-center">
                        <span>{groupName}</span>
                        <span className="text-[10px] text-slate-500 font-normal bg-white px-1.5 py-0.5 rounded border">{Object.keys(groupFeats).length} items</span>
                      </div>
                      <div className="p-2.5 bg-white space-y-1.5 text-xs">
                        {Object.entries(groupFeats).map(([featKey, featVal]: any) => {
                          const formattedKey = featKey.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                          return (
                            <div key={featKey} className="flex justify-between items-center py-1 border-b border-slate-50 last:border-0 hover:bg-slate-50 px-1.5 rounded transition-colors">
                              <span className="text-slate-600 font-medium">{formattedKey}</span>
                              <span className="font-bold text-slate-900 font-mono bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                                {featVal == null ? "0.00" : Number.isFinite(featVal) && !Number.isInteger(featVal) ? Number(featVal).toFixed(2) : String(featVal)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AirflowGraph;

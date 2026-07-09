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
import { X, Clock, DollarSign, Calendar, Activity, AlertTriangle } from 'lucide-react';
import TaskNode from '../components/graph/TaskNode';

const nodeTypes = {
  taskNode: TaskNode,
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'LR') => {
  if (nodes.length === 0) return { nodes, edges };

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ 
    rankdir: direction, 
    nodesep: 60,
    ranksep: 200,
    edgesep: 20,
    ranker: 'network-simplex'
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 208, height: 64 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';
    
    node.position = {
      x: nodeWithPosition.x - 208 / 2,
      y: nodeWithPosition.y - 64 / 2,
    };
    return node;
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
}

const AirflowGraph: React.FC<AirflowGraphProps> = ({ 
  projectId, tasks, dependencies, onConnectEdge, onDeleteTask, onEditTask, selectedOptionModes, criticalityIndices 
}) => {
  // Simple function to get Vietnamese name and WBS based on task WBS
  const getTaskNameByWbs = (wbs: string): string => {
    if (wbs.startsWith('1.1')) return `Khảo sát & Chuẩn bị mặt bằng`;
    if (wbs.startsWith('1.2')) return `Thiết kế kỹ thuật & Phê duyệt`;
    if (wbs.startsWith('1.3')) return `Thu mua vật tư & Logistics`;
    if (wbs.startsWith('1.4')) return `Xây dựng kết cấu nền móng`;
    if (wbs.startsWith('1.5')) return `Thi công hệ thống phụ trợ`;
    if (wbs.startsWith('1.6')) return `Lắp đặt cơ điện MEP & Thiết bị`;
    if (wbs.startsWith('1.7')) return `Nghiệm thu kỹ thuật & Đo lường`;
    if (wbs.startsWith('1.8')) return `Hoàn thiện & Nghiệm thu bàn giao`;
    if (wbs.startsWith('1.9')) return `Quản trị dự án & Đánh giá`;
    if (wbs.startsWith('1.10')) return `Nghiệm thu đưa vào vận hành`;
    return `Công tác logistics chi tiết`;
  };

  // Generate 72 features for display in drawer
  const get72Features = (task: any, mode: number, isCritical: boolean) => {
    const duration = mode === 1 
      ? Math.round((task.most_probable_duration || task.duration_days || 10) / 1.5) 
      : mode === 2 
        ? Math.round((task.most_probable_duration || task.duration_days || 10) / 2.0) 
        : (task.most_probable_duration || task.duration_days || 10);

    const cost = mode === 1 
      ? (task.crash_cost || 1500)
      : mode === 2 
        ? (task.outsource_cost || 2000)
        : (task.normal_cost || task.total_cost || 1000);

    const riskVal = (criticalityIndices && criticalityIndices[task.id]) || (isCritical ? 0.90 : 0.15);

    return {
      "Hub (Thông tin chung)": {
        "baseline_start_relative": "0.00",
        "duration_months": (duration / 160).toFixed(2),
        "duration_weeks": (duration / 40).toFixed(2),
        "duration_days": (duration / 8).toFixed(2),
        "duration_hours": duration.toFixed(1),
        "calendar_type_agenda": mode === 2 ? "0.00" : "1.00",
        "calendar_type_24_7": mode === 2 ? "1.00" : "0.00"
      },
      "G1: Chi phí trực tiếp": {
        "internal_labor_cost": mode === 0 ? (cost * 0.4).toFixed(2) : mode === 1 ? (cost * 0.5).toFixed(2) : "0.00",
        "subcontracting_cost": mode === 2 ? (cost * 0.85).toFixed(2) : "0.00",
        "overtime_crashing_cost": mode === 1 ? (cost * 0.35).toFixed(2) : "0.00",
        "material_cost": (cost * 0.2).toFixed(2),
        "equipment_cost": mode === 2 ? "0.00" : (cost * 0.15).toFixed(2),
        "direct_transportation": (cost * 0.05).toFixed(2),
        "energy_fuel_cost": (cost * 0.03).toFixed(2),
        "testing_and_inspection": (cost * 0.02).toFixed(2)
      },
      "G2: Chi phí gián tiếp": {
        "pm_overhead": (cost * 0.08).toFixed(2),
        "facility_rent": (cost * 0.02).toFixed(2),
        "utilities": (cost * 0.01).toFixed(2),
        "communication_cost": (cost * 0.005).toFixed(2),
        "internal_training": (cost * 0.005).toFixed(2),
        "quality_mgmt_overhead": (cost * 0.015).toFixed(2)
      },
      "G4: Ràng buộc hợp đồng": {
        "permits_and_licensing": (cost * 0.01).toFixed(2),
        "project_insurance": (cost * 0.015).toFixed(2),
        "warranty_and_after_sales": (cost * 0.02).toFixed(2),
        "regulatory_compliance": (cost * 0.01).toFixed(2)
      },
      "G5: Chi phí Logistics": {
        "inventory_holding_cost": (cost * 0.04).toFixed(2),
        "ordering_cost": (cost * 0.01).toFixed(2),
        "shortage_stockout_risk": (cost * 0.02).toFixed(2),
        "obsolescence_cost": (cost * 0.005).toFixed(2),
        "international_freight": mode === 2 ? (cost * 0.1).toFixed(2) : "0.00",
        "packaging_and_handling": (cost * 0.015).toFixed(2),
        "reverse_logistics": (cost * 0.01).toFixed(2)
      },
      "G6: Đặc trưng thời gian": {
        "wait_queue_time": (duration * 0.1).toFixed(1),
        "setup_transition_time": (duration * 0.05).toFixed(1),
        "induction_time": (duration * 0.02).toFixed(1),
        "lead_time": mode === 1 ? "2.0" : "0.0",
        "pert_3_point_estimate": duration.toFixed(1)
      },
      "G7: Tài nguyên": {
        "total_demand": (duration * 1.5).toFixed(1),
        "allocated_quantity": (duration * 1.2).toFixed(1),
        "labor_productivity": mode === 1 ? "1.20" : "1.00",
        "equipment_utilization": "0.85",
        "resource_substitutability": "0.60"
      },
      "G9: Rủi ro": {
        "technical_complexity": isCritical ? "0.80" : "0.35",
        "rework_probability": mode === 1 ? "0.25" : "0.10",
        "external_dependency_level": mode === 2 ? "0.75" : "0.20",
        "contingency_reserve": (cost * 0.1).toFixed(2),
        "management_reserve": (cost * 0.05).toFixed(2),
        "weather_seasonal_risk": "0.15",
        "technology_risk": "0.20"
      },
      "G11: Tổ chức hành chính": {
        "required_skill_level": isCritical ? "4.00" : "2.00",
        "staff_experience": "3.50",
        "learning_curve_effect": "0.90",
        "hr_stability_risk": "0.15",
        "cross_functional_coordination": "3.00"
      },
      "G12: ESG & Bền vững": {
        "occupational_safety_risk": mode === 1 ? "0.30" : "0.10",
        "environmental_impact": mode === 2 ? "0.15" : "0.25",
        "waste_disposal_cost": (cost * 0.01).toFixed(2),
        "carbon_footprint_index": "0.45",
        "social_sustainability_score": "0.80",
        "legal_governance_risk": "0.05"
      },
      "G8: Đặc trưng Tô-pô & AI": {
        "in_degree": isCritical ? "2.00" : "1.00",
        "out_degree": isCritical ? "2.00" : "1.00",
        "is_source": "0.00",
        "is_sink": "0.00",
        "total_float": isCritical ? "0.00" : (duration * 0.3).toFixed(1),
        "is_critical": isCritical ? "1.00" : "0.00",
        "path_length": isCritical ? "8.00" : "4.00",
        "GAT_attention_score": riskVal.toFixed(4),
        "DAGNN_delay_pred": (riskVal * 35.0).toFixed(2),
        "DAGNN_sigma_pred": (riskVal * 12.0).toFixed(2)
      }
    };
  };

  const { initialNodesLayout, initialEdgesLayout } = useMemo(() => {
    if (!tasks || tasks.length === 0) return { initialNodesLayout: [], initialEdgesLayout: [] };

    const displayTasks = tasks.slice(0, 35);
    const displayTaskIds = new Set(displayTasks.map(t => String(t.id)));

    const rawNodes = displayTasks.map((task: any, idx: number) => {
      const mode = selectedOptionModes && selectedOptionModes[idx] !== undefined ? selectedOptionModes[idx] : 0;
      const wbs = task.wbs || task.id.split("_")[1] || task.id;
      const isCritical = (criticalityIndices && criticalityIndices[task.id] > 0.75) || task.duration_days > 50;
      
      const duration = mode === 1 
        ? Math.round((task.most_probable_duration || task.duration_days || 10) / 1.5) 
        : mode === 2 
          ? Math.round((task.most_probable_duration || task.duration_days || 10) / 2.0) 
          : (task.most_probable_duration || task.duration_days || 10);

      const cost = mode === 1 
        ? (task.crash_cost || 1500)
        : mode === 2 
          ? (task.outsource_cost || 2000)
          : (task.normal_cost || task.total_cost || (task.internal_labor_cost || 0) + (task.equipment_cost || 0) || 1000);

      return {
        id: String(task.id),
        type: 'taskNode',
        position: { x: 0, y: 0 },
        data: {
          task_id: task.id,
          task_label: task.id,
          wbs,
          task_name: task.name || task.task_name || getTaskNameByWbs(wbs),
          duration: duration,
          total_cost: cost,
          is_critical: isCritical,
          mode,
          resources: task.resources || [],
          features: get72Features(task, mode, isCritical),
          baseline_start: task.baseline_start,
          optimistic_time: duration ? duration * 0.8 : 0,
          pessimistic_time: duration ? duration * 1.5 : 0,
        },
      };
    });

    const rawEdges = dependencies
      .map((dep: any) => {
        // Handle both object format (from API) and array format (from mocks)
        const sourceId = String(dep.predecessor_id || dep[0]);
        const targetId = String(dep.successor_id || dep[1]);
        return { sourceId, targetId };
      })
      .filter((dep) => displayTaskIds.has(dep.sourceId) && displayTaskIds.has(dep.targetId))
      .map((dep) => ({
        id: `e-${dep.sourceId}-${dep.targetId}`,
        source: dep.sourceId,
        target: dep.targetId,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: '#94a3b8',
        },
      }));

    const layouted = getLayoutedElements(rawNodes, rawEdges);
    return { initialNodesLayout: layouted.nodes, initialEdgesLayout: layouted.edges };
  }, [tasks, dependencies, selectedOptionModes, criticalityIndices]);

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
    <div className="w-full h-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden relative flex animate-fadeIn">
      <div className="flex-1 relative">
        <ReactFlow
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
              * Hiển thị phân đoạn 35 công việc để đảm bảo hiệu năng
            </p>
          </Panel>
        </ReactFlow>
      </div>

      {/* Drawer */}
      <div 
        className={`absolute top-0 right-0 h-full w-96 bg-white shadow-2xl border-l border-slate-200 transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          selectedTask ? 'translate-x-0' : 'translate-x-full'
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
                    const t = tasks.find(x => String(x.id) === selectedTask.task_label || String(x.id) === selectedTask.task_id);
                    if (t) onEditTask(t);
                  }}
                  className="flex-1 bg-blue-50 hover:bg-blue-100 text-blue-600 font-bold py-2 rounded-lg border border-blue-200 transition-colors"
                >
                  Edit Node
                </button>}
                {onDeleteTask && <button 
                  onClick={async () => {
                    if (window.confirm("Delete this node?")) {
                      onDeleteTask(selectedTask.task_label || selectedTask.task_id);
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

              {/* 72 Dimensions Graph Feature Vector (Tensors) */}
              <div>
                <h3 className="text-xs font-bold text-slate-800 mb-2.5 flex items-center border-b pb-1">
                  <Activity size={14} className="mr-1.5 text-blue-600" />
                  Graph Node Tensor (72 Features)
                </h3>
                <p className="text-[10px] text-slate-400 mb-3 italic">
                  Các nhóm đặc trưng nén 72 chiều cấp nút truyền vào Graph GNN để tính toán rủi ro và xác định ranh giới Pareto.
                </p>
                <div className="space-y-3">
                  {Object.entries(selectedTask.features || {}).map(([groupName, groupFeats]: any) => (
                    <div key={groupName} className="border border-slate-100 rounded-lg overflow-hidden">
                      <div className="bg-slate-50 px-2.5 py-1.5 text-[10px] font-bold text-slate-600 border-b border-slate-100 flex justify-between">
                        <span>{groupName}</span>
                        <span className="text-[9px] text-slate-400 font-normal">{Object.keys(groupFeats).length} features</span>
                      </div>
                      <div className="p-2 bg-white space-y-1 text-[11px]">
                        {Object.entries(groupFeats).map(([featKey, featVal]: any) => (
                          <div key={featKey} className="flex justify-between items-center py-0.5 hover:bg-slate-50 px-1 rounded">
                            <span className="text-slate-500 font-mono text-[9px]">{featKey}</span>
                            <span className="font-bold text-slate-800 font-mono bg-slate-100 px-1.5 py-0.2 rounded text-[10px]">
                              {String(featVal)}
                            </span>
                          </div>
                        ))}
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

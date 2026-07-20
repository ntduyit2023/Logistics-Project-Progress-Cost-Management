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
import { X, Clock, DollarSign, Calendar, Activity, AlertTriangle, Sliders } from 'lucide-react';
import TaskNode from '../components/graph/TaskNode';

const nodeTypes = {
  taskNode: TaskNode,
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (
  nodes: any[], 
  edges: any[], 
  direction = 'LR', 
  horizontalSpacing = 300, 
  verticalSpacing = 80
) => {
  if (nodes.length === 0) return { nodes, edges };

  // Check if we have enough baseline_start data to do a time-based layout
  const nodesWithTime = nodes.filter(n => n.data && n.data.baseline_start);
  if (nodesWithTime.length > nodes.length * 0.2) {
    // TIME-BASED GANTT LAYOUT
    const PIXELS_PER_DAY = horizontalSpacing; // Control horizontal spacing directly
    const NODE_WIDTH = 250;
    const NODE_HEIGHT = 80;
    const LANE_SPACING = Math.max(10, Math.round(verticalSpacing * 0.4)); // Scaled lane spacing

    // Sort nodes topologically or by time to assign lanes properly
    const sortedNodes = [...nodes].sort((a, b) => {
      const timeA = a.data?.baseline_start ? new Date(a.data.baseline_start).getTime() : 0;
      const timeB = b.data?.baseline_start ? new Date(b.data.baseline_start).getTime() : 0;
      return timeA - timeB;
    });

    let minTime = Number.MAX_SAFE_INTEGER;
    sortedNodes.forEach(n => {
      if (n.data?.baseline_start) {
        const t = new Date(n.data.baseline_start).getTime();
        if (t < minTime) minTime = t;
      }
    });
    if (minTime === Number.MAX_SAFE_INTEGER) minTime = 0;

    const laneEnds: number[] = []; // Tracks the end X coordinate of each lane

    sortedNodes.forEach(node => {
      let x = 0;
      if (node.data?.baseline_start) {
        const t = new Date(node.data.baseline_start).getTime();
        const days = (t - minTime) / (1000 * 60 * 60 * 24);
        x = days * PIXELS_PER_DAY;
      }

      const durationDays = node.data?.duration || 1;
      const estimatedEndX = x + NODE_WIDTH + (durationDays * 2); // Approximate space taken by this node horizontally

      // Find an available lane
      let assignedLane = -1;
      for (let i = 0; i < laneEnds.length; i++) {
        if (laneEnds[i] < x - 20) { // 20px padding between nodes in the same lane
          assignedLane = i;
          break;
        }
      }

      if (assignedLane === -1) {
        assignedLane = laneEnds.length;
        laneEnds.push(estimatedEndX);
      } else {
        laneEnds[assignedLane] = estimatedEndX;
      }

      node.targetPosition = 'left';
      node.sourcePosition = 'right';
      node.position = {
        x: x,
        y: assignedLane * (NODE_HEIGHT + LANE_SPACING)
      };
    });

    return { nodes, edges };
  }

  // FALLBACK TO DAGRE
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: Math.max(20, Math.round(verticalSpacing * 1.8)), // Scaled nodesep
    ranksep: Math.max(50, Math.round(horizontalSpacing + 150)), // Scaled ranksep
    edgesep: 80,
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
  const [horizSpacing, setHorizSpacing] = useState(300);
  const [vertSpacing, setVertSpacing] = useState(80);
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

  // Extract real features from task schema
  const getTaskGroups = (task: any) => {
    return {
      "Hub (Thông tin chung)": {
        "duration_months": task.duration_months,
        "duration_weeks": task.duration_weeks,
        "duration_days": task.duration_days,
        "duration_hours": task.duration_hours,
        "calendar_type": task.calendar_type
      },
      "G1: Chi phí trực tiếp": {
        "internal_labor_cost": task.internal_labor_cost,
        "overtime_cost": task.overtime_cost,
        "equipment_fuel_cost": task.equipment_fuel_cost,
        "qa_qc_cost": task.qa_qc_cost,
        "material_cost": task.material_cost,
        "outsourcing_cost": task.outsourcing_cost
      },
      "G2: Chi phí gián tiếp": {
        "training_cost": task.training_cost,
        "facility_rent": task.facility_rent,
        "communication_cost": task.communication_cost,
        "utilities_cost": task.utilities_cost
      },
      "G4: Ràng buộc hợp đồng": {
        "insurance_cost": task.insurance_cost,
        "licensing_cost": task.licensing_cost,
        "warranty_cost": task.warranty_cost
      },
      "G5: Hệ số rủi ro": {
        "complexity": task.complexity,
        "weather_contingency": task.weather_contingency,
        "general_contingency": task.general_contingency,
        "rework_risk": task.rework_risk
      },
      "G6: Logistics": {
        "holding_cost": task.holding_cost,
        "international_freight": task.international_freight,
        "handling_cost": task.handling_cost,
        "reverse_logistics": task.reverse_logistics,
        "defect_cost": task.defect_cost
      },
      "G7: Thời gian (Time)": {
        "overtime_hours": task.overtime_hours,
        "lag_time": task.lag_time
      }
    };
  };

  const { initialNodesLayout, initialEdgesLayout } = useMemo(() => {
    if (!tasks || tasks.length === 0) return { initialNodesLayout: [], initialEdgesLayout: [] };

    const displayTasks = tasks;
    const displayTaskIds = new Set(displayTasks.map((t: any) => String(t.id)));

    const rawNodes = displayTasks.map((task: any, idx: number) => {
      const mode = selectedOptionModes && selectedOptionModes[idx] !== undefined ? selectedOptionModes[idx] : 0;
      const wbs = task.wbs || task.id.split("_")[1] || task.id;
      const isCritical = (criticalityIndices && criticalityIndices[task.id] > 0.75) || task.duration_days > 50;

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
          (task.internal_labor_cost || 0) +
          (task.equipment_fuel_cost || 0) +
          (task.material_cost || 0) +
          (task.outsourcing_cost || 0)
        ) || task.normal_cost || 0;

      const cost = mode === 1
        ? (task.crash_cost || baseTaskCost * 1.25)
        : mode === 2
          ? (task.outsource_cost || baseTaskCost * 1.5)
          : baseTaskCost;

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
          base_duration: baseTaskDuration,
          base_cost: baseTaskCost,
          is_critical: isCritical,
          mode,
          resources: task.resources || [],
          features: getTaskGroups(task),
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
        type: 'default',
        animated: false,
        style: { stroke: '#94a3b8', strokeWidth: 1.5, opacity: 0.4 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 15,
          height: 15,
          color: '#94a3b8',
        },
      }));

    const layouted = getLayoutedElements(rawNodes, rawEdges, 'LR', horizSpacing, vertSpacing);
    return { initialNodesLayout: layouted.nodes, initialEdgesLayout: layouted.edges };
  }, [tasks, dependencies, selectedOptionModes, criticalityIndices, horizSpacing, vertSpacing]);

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
              * Hiển thị toàn bộ mạng lưới công việc của dự án
            </p>
          </Panel>
          
          <Panel position="top-right" className="bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-md border border-slate-200 text-xs m-4 z-10 w-60 space-y-3">
            <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
              <Sliders size={14} className="text-blue-600" />
              Cấu hình Giãn cách Node
            </h4>
            <div className="space-y-1">
              <div className="flex justify-between text-slate-600 font-medium">
                <span>Khoảng cách Ngang:</span>
                <span className="font-bold font-mono text-blue-600">{horizSpacing}px</span>
              </div>
              <input 
                type="range" 
                min="100" 
                max="600" 
                step="20"
                value={horizSpacing} 
                onChange={(e) => setHorizSpacing(Number(e.target.value))}
                className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-slate-600 font-medium">
                <span>Khoảng cách Dọc:</span>
                <span className="font-bold font-mono text-blue-600">{vertSpacing}px</span>
              </div>
              <input 
                type="range" 
                min="20" 
                max="300" 
                step="10"
                value={vertSpacing} 
                onChange={(e) => setVertSpacing(Number(e.target.value))}
                className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
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

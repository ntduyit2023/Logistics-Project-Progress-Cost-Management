import React, { useState, useCallback, useMemo } from 'react';
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
    nodesep: 50, 
    ranksep: 180, 
    edgesep: 20,
    ranker: 'network-simplex'
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 50 });
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
      x: nodeWithPosition.x - 180 / 2,
      y: nodeWithPosition.y - 50 / 2,
    };
    return node;
  });

  return { nodes, edges };
};

interface AirflowGraphProps {
  tasks: any[];
  dependencies: any[];
  onConnectEdge?: (source: string, target: string) => void;
  onDeleteTask?: (taskId: string) => void;
  onEditTask?: (task: any) => void;
}

const AirflowGraph: React.FC<AirflowGraphProps> = ({ tasks, dependencies, onConnectEdge, onDeleteTask, onEditTask }) => {
  const { initialNodesLayout, initialEdgesLayout } = useMemo(() => {
    const rawNodes = tasks.map((task: any) => ({
        id: String(task.id),
        type: 'taskNode',
        position: { x: 0, y: 0 },
        data: {
          task_label: task.id,
          wbs: task.wbs || task.id,
          task_name: task.task_name,
          duration: task.duration_days,
          baseline_start: task.baseline_start,
          baseline_end: null, // need to compute or pass
          total_cost: (task.internal_labor_cost || 0) + (task.equipment_cost || 0),
          optimistic_time: task.duration_days ? task.duration_days * 0.8 : 0,
          pessimistic_time: task.duration_days ? task.duration_days * 1.5 : 0,
          is_critical: task.duration_days > 50,
        },
      }));

    const rawEdges = dependencies.map((dep: any) => ({
      id: `e-${dep.predecessor_id}-${dep.successor_id}`,
      source: String(dep.predecessor_id),
      target: String(dep.successor_id),
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#94a3b8', strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 20,
        height: 20,
        color: '#94a3b8',
      },
    }));

    const layouted = getLayoutedElements(rawNodes, rawEdges);
    return { initialNodesLayout: layouted.nodes, initialEdgesLayout: layouted.edges };
  }, []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodesLayout);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdgesLayout);

  React.useEffect(() => {
    setNodes(initialNodesLayout);
    setEdges(initialEdgesLayout);
  }, [initialNodesLayout, initialEdgesLayout, setNodes, setEdges]);
  const [selectedTask, setSelectedTask] = useState<any>(null);

  const onNodeClick = useCallback((_: React.MouseEvent, node: any) => {
    setSelectedTask(node.data);
  }, []);

  const onConnect = useCallback((connection: any) => {
    if (onConnectEdge && connection.source && connection.target) {
      onConnectEdge(connection.source, connection.target);
    }
  }, [onConnectEdge]);

  return (
    <div className="w-full h-full bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden relative flex">
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
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.1}
        >
          <Background color="#cbd5e1" gap={16} />
          <Controls />
          <Panel position="top-left" className="bg-white p-3 rounded-lg shadow-md border border-slate-200 text-sm m-4 z-10">
            <h3 className="font-bold text-slate-800 text-lg mb-1">Nursing Home Noordhinder</h3>
            <p className="text-slate-500 mb-3">186 Tasks • 152 Dependencies</p>
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-red-500 rounded-sm mr-2"></div>
              <span className="text-slate-700 font-medium">Critical Path Task</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-slate-800 rounded-sm mr-2"></div>
              <span className="text-slate-700 font-medium">Standard Task</span>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Slide-out Task Details Drawer */}
      <div 
        className={`absolute top-0 right-0 h-full w-96 bg-white shadow-2xl border-l border-slate-200 transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          selectedTask ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {selectedTask && (
          <>
            {/* Drawer Header */}
            <div className={`p-4 flex justify-between items-start border-b ${selectedTask.is_critical ? 'bg-red-50 border-red-100' : 'bg-slate-50 border-slate-200'}`}>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-xs font-bold">
                    WBS {selectedTask.wbs}
                  </span>
                  {selectedTask.is_critical && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-600 rounded flex items-center text-xs font-bold border border-red-200">
                      <AlertTriangle size={12} className="mr-1" /> Critical Path
                    </span>
                  )}
                </div>
                <h2 className="text-lg font-bold text-slate-800 leading-tight pr-4">
                  {selectedTask.task_name}
                </h2>
              </div>
              <button 
                onClick={() => setSelectedTask(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-5 flex-1 overflow-y-auto">
              
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <div className="flex items-center text-slate-500 mb-1">
                    <Clock size={14} className="mr-1.5" />
                    <span className="text-xs font-medium uppercase tracking-wider">Duration</span>
                  </div>
                  <div className="text-xl font-bold text-slate-800">{selectedTask.duration?.toFixed(1) || 0} <span className="text-sm font-normal text-slate-500">days</span></div>
                </div>
                
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                  <div className="flex items-center text-emerald-600 mb-1">
                    <DollarSign size={14} className="mr-1.5" />
                    <span className="text-xs font-medium uppercase tracking-wider">Total Cost</span>
                  </div>
                  <div className="text-xl font-bold text-slate-800">${selectedTask.total_cost?.toLocaleString() || 0}</div>
                </div>
              </div>

              {/* Actions */}
              <div className="mb-6 flex gap-3">
                <button 
                  onClick={() => {
                    if (onEditTask) {
                      // find the raw task object from tasks list
                      const t = tasks.find(x => String(x.id) === selectedTask.task_label);
                      if (t) onEditTask(t);
                    }
                  }}
                  className="flex-1 bg-blue-50 hover:bg-blue-100 text-blue-600 font-bold py-2 rounded-lg border border-blue-200 transition-colors"
                >
                  Edit Node
                </button>
                <button 
                  onClick={async () => {
                    if (window.confirm("Delete this node?")) {
                      if (onDeleteTask) onDeleteTask(selectedTask.task_label);
                    }
                  }}
                  className="flex-1 bg-red-50 hover:bg-red-100 text-red-600 font-bold py-2 rounded-lg border border-red-200 transition-colors"
                >
                  Delete Node
                </button>
              </div>

              {/* PERT Estimates */}
              <div className="mb-6">
                <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
                  <Activity size={16} className="mr-2 text-indigo-500" /> 
                  PERT Time Estimates
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Optimistic (Best case)</span>
                    <span className="font-semibold text-emerald-600">{selectedTask.optimistic_time?.toFixed(1)} d</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Most Likely</span>
                    <span className="font-semibold text-blue-600">{selectedTask.duration?.toFixed(1)} d</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Pessimistic (Worst case)</span>
                    <span className="font-semibold text-red-500">{selectedTask.pessimistic_time?.toFixed(1)} d</span>
                  </div>
                  
                  {/* Visual Bar */}
                  <div className="w-full h-2 bg-slate-100 rounded-full mt-2 overflow-hidden flex">
                    <div className="bg-emerald-400 h-full" style={{ width: '33%' }}></div>
                    <div className="bg-blue-400 h-full" style={{ width: '34%' }}></div>
                    <div className="bg-red-400 h-full" style={{ width: '33%' }}></div>
                  </div>
                </div>
              </div>

              {/* Schedule Info */}
              <div className="mb-6">
                <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
                  <Calendar size={16} className="mr-2 text-blue-500" /> 
                  Baseline Schedule
                </h3>
                <div className="bg-white border border-slate-200 rounded-lg p-3 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Start Date</span>
                    <span className="font-medium text-slate-800">
                      {selectedTask.baseline_start ? new Date(selectedTask.baseline_start).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">End Date</span>
                    <span className="font-medium text-slate-800">
                      {selectedTask.baseline_end ? new Date(selectedTask.baseline_end).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
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

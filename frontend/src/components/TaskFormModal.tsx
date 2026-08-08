import React, { useState, useEffect } from 'react';
import { X, Save, Layers, DollarSign, Briefcase, ShieldAlert, Users, Leaf, ArrowRight, HardHat, Plus, Trash2, AlertTriangle, Clock } from 'lucide-react';
import { api } from '../services/api';
import { useParams } from 'react-router-dom';

interface TaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit?: (data: any) => void;
  initialData?: any | null;
  availableTasks?: any[];
  projectResources?: any[];
  constraintLogic?: any[];
  projectType?: string;
  onSave?: (data: any) => void;
  tasks?: any[];
  projectId?: number | string;
}

const TABS = [
  { id: 'basic', label: 'Basic & Schedule', icon: Layers },
  { id: 'resources', label: 'Resources & Logic', icon: HardHat },
  { id: 'g1_direct', label: 'Direct Resource Cost', icon: DollarSign },
  { id: 'g2_indirect', label: 'Overhead & Facility Cost', icon: Briefcase },
  { id: 'g3_time', label: 'Time-dependent Cost', icon: Clock },
  { id: 'g4_contractual', label: 'Risk & Legal Cost', icon: ShieldAlert },
  { id: 'g5_logistics', label: 'Supply Chain & Freight', icon: ArrowRight },
  { id: 'g6_financial', label: 'Financial & ESG Cost', icon: Leaf },
];

const FIELD_GROUPS = {
  g1_direct: [
    { key: 'labor', label: 'Labor' },
    { key: 'material', label: 'Material' },
    { key: 'equipment', label: 'Equipment' },
    { key: 'energy', label: 'Energy & Fuel' },
    { key: 'testing_inspection', label: 'Testing & Inspection' },
    { key: 'project_management', label: 'Project Management' },
  ],
  g2_indirect: [
    { key: 'facility', label: 'Facility Rent' },
    { key: 'utilities', label: 'Utilities' },
    { key: 'communication', label: 'Communication' },
    { key: 'training', label: 'Training' },
    { key: 'quality_management', label: 'Quality Assurance' },
  ],
  g3_time: [
    { key: 'overtime', label: 'Overtime' },
    { key: 'delay_penalty', label: 'Delay Penalty' },
    { key: 'inventory_holding', label: 'Inventory Holding' },
    { key: 'waiting_cost', label: 'Waiting Time' },
    { key: 'idle_resource', label: 'Idle Resource' },
    { key: 'revenue_delay', label: 'Revenue Delay' },
    { key: 'expediting', label: 'Expediting' },
  ],
  g4_contractual: [
    { key: 'insurance', label: 'Insurance' },
    { key: 'rework', label: 'Rework' },
    { key: 'warranty', label: 'Warranty Reserve' },
    { key: 'litigation', label: 'Litigation & Legal' },
    { key: 'regulatory_compliance', label: 'Regulatory Compliance' },
    { key: 'contingency_reserve', label: 'Contingency Reserve' },
    { key: 'management_reserve', label: 'Management Reserve' },
  ],
  g5_logistics: [
    { key: 'transportation', label: 'Transportation' },
    { key: 'ordering', label: 'Ordering' },
    { key: 'packaging', label: 'Packaging' },
    { key: 'reverse_logistics', label: 'Reverse Logistics' },
    { key: 'customs', label: 'Customs & Tariff' },
    { key: 'supplier_coordination', label: 'Supplier Coordination' },
  ],
  g6_financial: [
    { key: 'opportunity_cost', label: 'Opportunity Cost' },
    { key: 'capital_cost', label: 'Cost of Capital' },
    { key: 'financing_cost', label: 'Financing Interest' },
    { key: 'npv_loss', label: 'NPV Loss' },
    { key: 'esg_cost', label: 'ESG Compliance' },
    { key: 'carbon_tax', label: 'Carbon Tax' },
    { key: 'reputation_cost', label: 'Reputation Loss' },
  ]
};

export default function TaskFormModal({ isOpen, onClose, onSubmit, onSave, initialData, availableTasks = [], tasks = [], projectResources = [], constraintLogic = [], projectType, projectId }: TaskFormModalProps) {
  const finalOnSubmit = onSubmit || onSave || (() => { });
  const finalAvailableTasks = availableTasks.length > 0 ? availableTasks : tasks;
  const { projectId: routeProjectId } = useParams();
  const effectiveProjectId = projectId || routeProjectId;
  const [activeTab, setActiveTab] = useState('basic');
  const [formData, setFormData] = useState<any>({});
  const [predecessor, setPredecessor] = useState({ id: '', type: 'FS', lag: 0 });

  // Logic Assignment State
  const [existingPredecessors, setExistingPredecessors] = useState<any[]>([]);
  const [existingSuccessors, setExistingSuccessors] = useState<any[]>([]);

  // Resource Assignment State
  const [assignedResources, setAssignedResources] = useState<any[]>([]);
  const [selectedResId, setSelectedResId] = useState('');
  const [reqQty, setReqQty] = useState(1);
  const [loadingRes, setLoadingRes] = useState(false);
  const [stagedPredecessors, setStagedPredecessors] = useState<any[]>([]);

  // Cycle detection (DFS): Checks if there is a path from startId to targetId
  const hasPath = (startId: string, targetId: string, edges: any[]) => {
    if (!startId || !targetId) return false;
    const visited = new Set<string>();
    const stack = [startId];
    
    while (stack.length > 0) {
      const current = stack.pop()!;
      if (current === targetId) return true;
      if (!visited.has(current)) {
        visited.add(current);
        const successors = edges.filter(e => String(e.predecessor_id) === current).map(e => String(e.successor_id));
        for (const succ of successors) {
          if (!visited.has(succ)) {
            stack.push(succ);
          }
        }
      }
    }
    return false;
  };

  useEffect(() => {
    if (isOpen) {
      setActiveTab('basic');
      if (initialData) {
        setFormData({ ...initialData, baseline_start: initialData.baseline_start ? initialData.baseline_start.split('T')[0] : '' });

        // Find existing Predecessors and Successors using task_id field
        const taskIdVal = String(initialData.task_id || initialData.id || '');
        const preds = constraintLogic.filter(c => String(c.successor_id) === taskIdVal);
        const succs = constraintLogic.filter(c => String(c.predecessor_id) === taskIdVal);

        // Map names
        setExistingPredecessors(preds.map(p => {
          const t = finalAvailableTasks.find(x => String(x.task_id) === String(p.predecessor_id) || String(x.id) === String(p.predecessor_id));
          return { ...p, name: t ? t.task_name : p.predecessor_id };
        }));

        setExistingSuccessors(succs.map(s => {
          const t = finalAvailableTasks.find(x => String(x.task_id) === String(s.successor_id) || String(x.id) === String(s.successor_id));
          return { ...s, name: t ? t.task_name : s.successor_id };
        }));

        // Fetch assigned resources using string projectId and task_id
        const fetchResources = async () => {
          if (!effectiveProjectId) return;
          setLoadingRes(true);
          try {
            const taskIdForApi = initialData.task_id || initialData.id;
            const res = await api.getTaskResources(effectiveProjectId, String(taskIdForApi));
            setAssignedResources(res.data || []);
          } catch (err) {
            console.error("Failed to fetch task resources", err);
          } finally {
            setLoadingRes(false);
          }
        };
        fetchResources();

      } else {
        setFormData({ task_type: 'Construction', status: 'Pending', duration_hours: 1 });
        setAssignedResources([]);
        setExistingPredecessors([]);
        setExistingSuccessors([]);
        setPredecessor({ id: '', type: 'FS', lag: 0 });
        setSelectedResId('');
        setReqQty(1);
      }
    } else {
      // Reset when closed
      setAssignedResources([]);
      setStagedPredecessors([]);
      setPredecessor({ id: '', type: 'FS', lag: 0 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialData, effectiveProjectId]);

  if (!isOpen) return null;

  const handleChange = (key: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleAddResource = () => {
    if (!selectedResId) return;
    const resKey = String(selectedResId);

    const projRes = projectResources.find(r => String(r.id) === resKey || String(r.resource_id) === resKey || String(r.name) === resKey);
    const targetResId = projRes ? (projRes.resource_id || projRes.name || String(projRes.id)) : resKey;
    const targetResName = projRes ? (projRes.name || projRes.resource_name || projRes.resource_id) : resKey;
    const targetResType = projRes ? (projRes.type || projRes.resource_type || 'Human') : 'Human';
    
    const maxCap = projRes ? Number(projRes.max_availability ?? projRes.max_capacity ?? projRes.capacity) : null;
    if (maxCap != null && !isNaN(maxCap) && Number(reqQty) > maxCap) {
      alert(`Quantity cannot exceed maximum limit (${maxCap}) of this resource!`);
      return;
    }

    const existing = assignedResources.find(r => String(r.resource_id) === String(targetResId));
    if (existing) {
      setAssignedResources(prev => prev.map(r =>
        String(r.resource_id) === String(targetResId) ? { ...r, request_quantity: Number(reqQty) } : r
      ));
    } else {
      setAssignedResources([...assignedResources, {
        resource_id: targetResId,
        resource_name: targetResName,
        resource_type: targetResType,
        request_quantity: Number(reqQty),
        allocated_quantity: null
      }]);
    }
    setSelectedResId('');
    setReqQty(1);
  };

  const handleRemoveResource = (resId: any) => {
    setAssignedResources(prev => prev.filter(r => String(r.resource_id) !== String(resId)));
  };



  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.task_name?.trim()) {
      alert("Task Name is required!");
      return;
    }
    if (!formData.baseline_start) {
      alert("Baseline Start is required!");
      return;
    }
    
    const dur = formData.duration_hours != null ? Number(formData.duration_hours) : Number(formData.duration_days);
    if (isNaN(dur) || dur <= 0) {
      alert("Duration is required and must be greater than 0!");
      return;
    }

    const payload: any = { ...formData };

    // Convert all numeric string values back to numbers if needed
    for (const k of Object.keys(payload)) {
      if (payload[k] === '') payload[k] = null;
      else if (typeof payload[k] === 'string' && k !== 'task_name' && k !== 'task_type' && k !== 'status' && k !== 'calendar_type' && k !== 'baseline_start' && k !== 'id' && k !== 'metadata_json' && k !== 'type') {
        const num = Number(payload[k]);
        if (!isNaN(num)) payload[k] = num;
      }
    }

    if (payload.baseline_start) {
      payload.baseline_start = new Date(payload.baseline_start).toISOString();
    }

    let finalStaged = [...stagedPredecessors];
    if (predecessor.id) {
      finalStaged.push({
        predecessor_id: predecessor.id,
        dependency_type: predecessor.type,
        lag_hours: Number(predecessor.lag),
        isNew: true
      });
    }

    payload.stagedResources = assignedResources;
    payload.stagedPredecessors = finalStaged;

    finalOnSubmit(payload);
  };

  // Read-only cost keys (tính từ tài nguyên / nhiên liệu / tăng ca, không sửa trực tiếp)
  const READONLY_COST_KEYS = ['labor', 'equipment', 'energy', 'overtime'];

  const visibleTabIds = React.useMemo(() => {
    const baseTabs = ['basic', 'resources'];
    if (projectType === 'PRO') {
      return [...baseTabs, 'g1_direct', 'g2_indirect', 'g3_time', 'g4_contractual'];
    }
    return [...baseTabs, 'g1_direct', 'g2_indirect', 'g3_time', 'g4_contractual', 'g5_logistics', 'g6_financial'];
  }, [projectType]);

  const visibleTabs = TABS.filter(t => visibleTabIds.includes(t.id));

  const handleDeleteConstraint = async (predId: string, succId: string, type: 'pred' | 'succ', isStaged: boolean = false) => {
    if (!window.confirm('Are you sure you want to delete this logic constraint?')) return;
    if (isStaged) {
      setStagedPredecessors(prev => prev.filter(p => String(p.predecessor_id) !== String(predId)));
      return;
    }
    try {
      if (effectiveProjectId) {
        await api.deleteLogicConstraint(effectiveProjectId, predId, succId);
        if (type === 'pred') {
          setExistingPredecessors(prev => prev.filter(p => String(p.predecessor_id) !== String(predId)));
        } else {
          setExistingSuccessors(prev => prev.filter(s => String(s.successor_id) !== String(succId)));
        }
      }
    } catch (err) {
      alert("Failed to delete logic constraint: " + (err as Error).message);
    }
  };

  const handleAddConstraint = async () => {
    if (!predecessor.id) return;
    const t = finalAvailableTasks.find(x => String(x.task_id) === String(predecessor.id) || String(x.id) === String(predecessor.id));
    const newPred = {
      predecessor_id: predecessor.id,
      dependency_type: predecessor.type,
      lag_hours: Number(predecessor.lag),
      name: t ? t.task_name : predecessor.id,
      isNew: true
    };

    setStagedPredecessors([...stagedPredecessors, newPred]);
    setPredecessor({ id: '', type: 'FS', lag: 0 });
  };

  const renderNumberFields = (groupId: string) => {
    const displayFields = FIELD_GROUPS[groupId as keyof typeof FIELD_GROUPS] || [];
    
    // Hardcoded readonly fields for direct costs calculated by backend
    const READONLY_COST_KEYS = ['labor', 'equipment', 'energy'];
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-3">
        {displayFields.map(field => {
          const isReadOnly = READONLY_COST_KEYS.includes(field.key);
          return (
            <div key={field.key}>
              <label className="block text-xs font-semibold text-slate-600 mb-1 line-clamp-1" title={field.label}>
                {field.label}
              </label>
              <input
                type="number"
                step="0.01"
                value={formData[field.key] ?? 0}
                onChange={(e) => handleChange(field.key, e.target.value)}
                readOnly={isReadOnly}
                className={`w-full border rounded-md px-2 py-1.5 text-sm focus:outline-none transition-colors ${isReadOnly
                    ? 'bg-slate-100 border-slate-200 text-slate-500 cursor-not-allowed font-semibold'
                    : 'bg-white border-slate-300 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500'
                  }`}
                title={isReadOnly ? 'Calculated automatically from assigned resources - do not edit directly' : ''}
              />
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl overflow-hidden max-h-[95vh] flex flex-col animate-in fade-in zoom-in-95 duration-200">

        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 shrink-0">
          <div>
            <h2 className="text-xl font-bold text-slate-800">
              {initialData ? `Edit Node: ${initialData.task_name}` : 'Create New Node'}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Configure 60+ parameters across 12 Dimensions for Deep AI Simulation</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition p-1.5 rounded-md hover:bg-slate-200">
            <X size={22} />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="w-56 bg-slate-50 border-r border-slate-200 shrink-0 p-2 overflow-y-auto">
            {visibleTabs.map(tab => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium mb-1 transition-all ${activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                  }`}
              >
                <tab.icon size={16} className={`mr-2 ${activeTab === tab.id ? 'text-white' : 'text-slate-500'}`} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Form Content */}
          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
            <form id="task-form-mega" onSubmit={handleSubmit} className="space-y-6">

              {/* TAB 1: BASIC & SCHEDULE */}
              {activeTab === 'basic' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Core Attributes</h3>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="col-span-2">
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Task Name <span className="text-red-500">*</span></label>
                        <input
                          type="text"
                          value={formData.task_name || ''}
                          onChange={(e) => handleChange('task_name', e.target.value)}
                          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                          autoFocus
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Status</label>
                        <select
                          value={formData.status || 'Pending'}
                          onChange={(e) => handleChange('status', e.target.value)}
                          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white"
                        >
                          <option value="Pending">Pending</option>
                          <option value="Planning">Planning</option>
                          <option value="Execution">Execution</option>
                          <option value="Completed">Completed</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Scheduling & Total Cost</h3>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Baseline Start</label>
                        <input
                          type="date"
                          value={formData.baseline_start || ''}
                          onChange={(e) => handleChange('baseline_start', e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Duration (Hours)</label>
                        <input
                          type="number" step="0.5"
                          value={formData.duration_hours || ''}
                          onChange={(e) => handleChange('duration_hours', e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Total Cost ($)</label>
                        <input
                          type="number" step="0.01"
                          value={formData.total_cost ?? 0}
                          readOnly
                          className="w-full border border-slate-200 rounded-md px-2 py-1.5 text-sm bg-slate-100 text-slate-500 font-bold cursor-not-allowed"
                          title="Auto-calculated"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-slate-800 mb-2">Network Logic Constraints</h3>
                    <p className="text-xs text-slate-500 mb-3">Edges connecting this node. (Drag-and-drop on graph to add, or select below).</p>

                    {/* Existing Logic */}
                    {(existingPredecessors.length > 0 || existingSuccessors.length > 0 || stagedPredecessors.length > 0) && (
                      <div className="mb-4 bg-white border border-slate-200 rounded-lg overflow-hidden">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                            <tr>
                              <th className="px-3 py-1.5 font-bold">Direction</th>
                              <th className="px-3 py-1.5 font-bold">Node</th>
                              <th className="px-3 py-1.5 font-bold">Type</th>
                              <th className="px-3 py-1.5 font-bold">Lag (d)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {[...existingPredecessors, ...stagedPredecessors].map((p, idx) => {
                              const isStaged = idx >= existingPredecessors.length;
                              return (
                              <tr key={`p-${p.predecessor_id}-${idx}`} className="border-b border-slate-100 group">
                                <td className="px-3 py-1.5 text-amber-600 font-bold">← Predecessor {isStaged && <span className="text-[10px] bg-amber-100 text-amber-800 px-1 py-0.5 rounded ml-1">New</span>}</td>
                                <td className="px-3 py-1.5 font-medium">{p.name === p.predecessor_id ? p.name : `${p.name} (${p.predecessor_id})`}</td>
                                <td className="px-3 py-1.5">{p.dependency_type}</td>
                                <td className="px-3 py-1.5 flex items-center justify-between">
                                  <span>{p.lag_days}</span>
                                  <button type="button" onClick={() => handleDeleteConstraint(p.predecessor_id, initialData?.task_id || initialData?.id, 'pred', isStaged)} className="text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                                    <Trash2 size={14} />
                                  </button>
                                </td>
                              </tr>
                            )})}
                            {existingSuccessors.map(s => (
                              <tr key={`s-${s.successor_id}`} className="border-b border-slate-100 group">
                                <td className="px-3 py-1.5 text-blue-600 font-bold">→ Successor</td>
                                <td className="px-3 py-1.5 font-medium">{s.name === s.successor_id ? s.name : `${s.name} (${s.successor_id})`}</td>
                                <td className="px-3 py-1.5">{s.dependency_type}</td>
                                <td className="px-3 py-1.5 flex items-center justify-between">
                                  <span>{s.lag_days}</span>
                                  <button type="button" onClick={() => handleDeleteConstraint(initialData?.task_id || initialData?.id, s.successor_id, 'succ', false)} className="text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                                    <Trash2 size={14} />
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <div className="grid grid-cols-4 gap-3 items-end">
                      <div className="col-span-4 md:col-span-2">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">+ Add Predecessor</label>
                        <select
                          value={predecessor.id}
                          onChange={(e) => setPredecessor(p => ({ ...p, id: e.target.value }))}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white"
                        >
                          <option value="">None</option>
                          {finalAvailableTasks.filter((t: any) => {
                            const tTaskId = String(t.task_id || t.id);
                            const myTaskId = String(initialData?.task_id || initialData?.id || '');
                            return tTaskId !== myTaskId && !existingPredecessors.some(p => String(p.predecessor_id) === tTaskId);
                          }).map((t: any) => {
                            const tTaskId = String(t.task_id || t.id);
                            const myTaskId = String(initialData?.task_id || initialData?.id || '');
                            const createsCycle = myTaskId ? hasPath(myTaskId, tTaskId, constraintLogic) : false;
                            
                            return (
                              <option 
                                key={tTaskId} 
                                value={tTaskId}
                                disabled={createsCycle}
                              >
                                {t.task_name} ({tTaskId}) {createsCycle ? ' - [Vòng lặp]' : ''}
                              </option>
                            );
                          })}
                        </select>
                      </div>
                      <div className="col-span-1">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Dependency</label>
                        <select
                          value={predecessor.type}
                          onChange={(e) => setPredecessor(p => ({ ...p, type: e.target.value }))}
                          disabled={!predecessor.id}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white disabled:opacity-50"
                        >
                          <option value="FS">Finish-to-Start (FS)</option>
                          <option value="SS">Start-to-Start (SS)</option>
                          <option value="FF">Finish-to-Finish (FF)</option>
                          <option value="SF">Start-to-Finish (SF)</option>
                        </select>
                      </div>
                      <div className="col-span-1 flex gap-2">
                        <div className="flex-1">
                          <label className="block text-xs font-semibold text-slate-700 mb-1">Lag (h)</label>
                          <input
                            type="number"
                            value={predecessor.lag}
                            onChange={(e) => setPredecessor(p => ({ ...p, lag: Number(e.target.value) }))}
                            disabled={!predecessor.id}
                            className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-50"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={handleAddConstraint}
                          disabled={!predecessor.id}
                          className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center shrink-0"
                        >
                          <Plus size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: RESOURCES */}
              {activeTab === 'resources' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-slate-800 mb-3">Assign Project Resources to this Task</h3>

                    <div className="flex gap-3 items-end mb-4">
                      <div className="flex-1">
                        <label className="block text-xs font-semibold text-slate-600 mb-1">Select Resource</label>
                        <select
                          value={selectedResId}
                          onChange={(e) => setSelectedResId(e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500/20"
                        >
                          <option value="">-- Choose from Project Pool --</option>
                          {projectResources.map(r => (
                            <option key={r.id || r.resource_id} value={r.id || r.resource_id}>{r.name || r.resource_name || r.resource_id} ({r.type || r.resource_type || 'Unknown'})</option>
                          ))}
                        </select>
                      </div>
                      <div className="w-24">
                        <label className="block text-xs font-semibold text-slate-600 mb-1">Quantity</label>
                        <input
                          type="number" step="0.1" min="0" value={reqQty} onChange={e => setReqQty(Number(e.target.value))}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500/20"
                        />
                      </div>
                      <button
                        type="button" onClick={handleAddResource} disabled={!selectedResId}
                        className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-1.5 rounded-md text-sm font-bold flex items-center h-[34px] disabled:opacity-50"
                      >
                        <Plus size={16} className="mr-1" /> Add
                      </button>
                    </div>

                    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-600 bg-slate-50 border-b border-slate-200">
                          <tr>
                            <th className="px-4 py-2">Resource</th>
                            <th className="px-4 py-2">Type</th>
                            <th className="px-4 py-2 text-right">Qty</th>
                            <th className="px-4 py-2 text-center">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {loadingRes ? (
                            <tr><td colSpan={4} className="text-center py-4 text-slate-400">Loading...</td></tr>
                          ) : assignedResources.length === 0 ? (
                            <tr><td colSpan={4} className="text-center py-4 text-slate-400">No resources assigned yet.</td></tr>
                          ) : (
                            assignedResources.map(r => (
                              <tr key={r.resource_id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition">
                                <td className="px-4 py-2 font-medium text-slate-800">{r.resource_name}</td>
                                <td className="px-4 py-2">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.resource_type === 'Renewable' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                    {r.resource_type}
                                  </span>
                                </td>
                                <td className="px-4 py-2 text-right">
                                  <input
                                    type="number" step="0.1" min="0"
                                    value={r.request_quantity}
                                    onChange={(e) => {
                                      const newQty = Number(e.target.value);
                                      setAssignedResources(prev => prev.map(x => x.resource_id === r.resource_id ? { ...x, request_quantity: newQty } : x));
                                    }}
                                    className="w-20 border border-slate-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-right bg-white"
                                  />
                                </td>
                                <td className="px-4 py-2 text-center">
                                  <button
                                    type="button" onClick={() => handleRemoveResource(r.resource_id)}
                                    className="text-slate-400 hover:text-red-600 transition p-1 hover:bg-red-50 rounded"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                    <p className="text-xs text-amber-600 mt-3 font-medium bg-amber-50 p-2 rounded border border-amber-100">
                      * Resource assignments will be saved when you click "Save Changes" at the bottom.
                    </p>
                  </div>
                </div>
              )}

              {/* DYNAMIC TABS FOR EXTENDED FEATURES */}
              {['g1_direct', 'g2_indirect', 'g3_time', 'g4_contractual', 'g5_logistics', 'g6_financial'].includes(activeTab) && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                  {renderNumberFields(activeTab)}
                </div>
              )}

            </form>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 shrink-0 flex gap-3 justify-end bg-slate-50">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-300 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="task-form-mega"
            className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center shadow-md shadow-blue-500/20"
          >
            <Save size={16} className="mr-2" />
            {initialData ? 'Save Changes' : 'Create Task'}
          </button>
        </div>

      </div>
    </div>
  );
}

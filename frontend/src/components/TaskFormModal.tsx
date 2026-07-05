import React, { useState, useEffect } from 'react';
import { X, Save, Layers, DollarSign, Briefcase, ShieldAlert, Users, Leaf, ArrowRight, HardHat, Plus, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useParams } from 'react-router-dom';

interface TaskFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  initialData?: any | null;
  availableTasks?: any[];
  projectResources?: any[];
  constraintLogic?: any[];
}

const TABS = [
  { id: 'basic', label: 'Basic & Schedule', icon: Layers },
  { id: 'resources', label: 'Resources', icon: HardHat },
  { id: 'direct', label: 'G1: Direct Cost', icon: DollarSign },
  { id: 'indirect', label: 'G2 & G4: Indirect/Contract', icon: Briefcase },
  { id: 'logistics', label: 'G5 & G6: Logistics/Time', icon: ArrowRight },
  { id: 'risk_hr', label: 'G9 & G11: Risk/HR', icon: Users },
  { id: 'esg', label: 'G12: ESG', icon: Leaf },
];

const FIELD_GROUPS = {
  direct: [
    { key: 'internal_labor_cost', label: 'Internal Labor Cost' },
    { key: 'subcontracting_cost', label: 'Subcontracting Cost' },
    { key: 'overtime_crashing_cost', label: 'Overtime Crashing Cost' },
    { key: 'material_cost', label: 'Material Cost' },
    { key: 'equipment_cost', label: 'Equipment Cost' },
    { key: 'direct_transportation', label: 'Direct Transportation' },
    { key: 'energy_fuel_cost', label: 'Energy Fuel Cost' },
    { key: 'testing_and_inspection', label: 'Testing & Inspection' },
  ],
  indirect: [
    { key: 'pm_overhead', label: 'PM Overhead' },
    { key: 'facility_rent', label: 'Facility Rent' },
    { key: 'utilities', label: 'Utilities' },
    { key: 'communication_cost', label: 'Communication Cost' },
    { key: 'internal_training', label: 'Internal Training' },
    { key: 'quality_mgmt_overhead', label: 'Quality Mgmt Overhead' },
    { key: 'permits_and_licensing', label: 'Permits & Licensing (G4)' },
    { key: 'project_insurance', label: 'Project Insurance (G4)' },
    { key: 'warranty_and_after_sales', label: 'Warranty & After Sales (G4)' },
    { key: 'regulatory_compliance', label: 'Regulatory Compliance (G4)' },
  ],
  logistics: [
    { key: 'inventory_holding_cost', label: 'Inventory Holding Cost' },
    { key: 'ordering_cost', label: 'Ordering Cost' },
    { key: 'shortage_stockout', label: 'Shortage Stockout' },
    { key: 'obsolescence_cost', label: 'Obsolescence Cost' },
    { key: 'international_freight', label: 'International Freight' },
    { key: 'packaging_and_handling', label: 'Packaging & Handling' },
    { key: 'reverse_logistics', label: 'Reverse Logistics' },
    { key: 'wait_queue_time', label: 'Wait/Queue Time (G6)' },
    { key: 'setup_transition_time', label: 'Setup/Transition Time (G6)' },
    { key: 'induction_time', label: 'Induction Time (G6)' },
    { key: 'lead_time', label: 'Lead Time (G6)' },
    { key: 'pert_3_point_estimate', label: 'PERT Estimate (G6)' },
  ],
  risk_hr: [
    { key: 'technical_complexity', label: 'Technical Complexity (G9)' },
    { key: 'rework_probability', label: 'Rework Probability (G9)' },
    { key: 'external_dependency_level', label: 'External Dependency Level (G9)' },
    { key: 'contingency_reserve', label: 'Contingency Reserve (G9)' },
    { key: 'management_reserve', label: 'Management Reserve (G9)' },
    { key: 'weather_seasonal_risk', label: 'Weather Seasonal Risk (G9)' },
    { key: 'technology_risk', label: 'Technology Risk (G9)' },
    { key: 'required_skill_level', label: 'Required Skill Level (G11)' },
    { key: 'staff_experience', label: 'Staff Experience (G11)' },
    { key: 'learning_curve_effect', label: 'Learning Curve Effect (G11)' },
    { key: 'hr_stability_risk', label: 'HR Stability Risk (G11)' },
    { key: 'cross_functional_coordination', label: 'Cross-functional Coord (G11)' },
    { key: 'occupational_safety_risk', label: 'Safety Risk (G11)' },
  ],
  esg: [
    { key: 'environmental_impact', label: 'Environmental Impact' },
    { key: 'waste_disposal_cost', label: 'Waste Disposal Cost' },
    { key: 'community_social_impact', label: 'Community Social Impact' },
    { key: 'carbon_tax_credit', label: 'Carbon Tax Credit' },
    { key: 'esg_compliance', label: 'ESG Compliance' },
  ],
};

export default function TaskFormModal({ isOpen, onClose, onSubmit, initialData, availableTasks = [], projectResources = [], constraintLogic = [] }: TaskFormModalProps) {
  const { projectId } = useParams();
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

  useEffect(() => {
    if (isOpen) {
      setActiveTab('basic');
      if (initialData) {
        setFormData({ ...initialData, baseline_start: initialData.baseline_start ? initialData.baseline_start.split('T')[0] : '' });
        
        // Find existing Predecessors and Successors
        const preds = constraintLogic.filter(c => c.successor_id === initialData.id);
        const succs = constraintLogic.filter(c => c.predecessor_id === initialData.id);
        
        // Map names
        setExistingPredecessors(preds.map(p => {
          const t = availableTasks.find(x => x.id === p.predecessor_id);
          return { ...p, name: t ? t.task_name : p.predecessor_id };
        }));
        
        setExistingSuccessors(succs.map(s => {
          const t = availableTasks.find(x => x.id === s.successor_id);
          return { ...s, name: t ? t.task_name : s.successor_id };
        }));

        // Fetch assigned resources
        const fetchResources = async () => {
          setLoadingRes(true);
          try {
            const res = await api.getTaskResources(Number(projectId), initialData.id);
            setAssignedResources(res.data || []);
          } catch (err) {
            console.error("Failed to fetch task resources", err);
          } finally {
            setLoadingRes(false);
          }
        };
        fetchResources();

      } else {
        setFormData({ task_type: 'Construction', status: 'Pending', duration_days: 1 });
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
      setPredecessor({ id: '', type: 'FS', lag: 0 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialData, projectId]);

  if (!isOpen) return null;

  const handleChange = (key: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleAddResource = () => {
    if (!selectedResId) return;
    const resIdNum = Number(selectedResId);
    
    // Check if already assigned, if so just update qty
    const existing = assignedResources.find(r => r.resource_id === resIdNum);
    if (existing) {
      setAssignedResources(prev => prev.map(r => 
        r.resource_id === resIdNum ? { ...r, request_quantity: Number(reqQty) } : r
      ));
    } else {
      const projRes = projectResources.find(r => r.id === resIdNum);
      if (projRes) {
        setAssignedResources([...assignedResources, {
          resource_id: resIdNum,
          resource_name: projRes.resource_name,
          resource_type: projRes.resource_type,
          request_quantity: Number(reqQty),
          allocated_quantity: null
        }]);
      }
    }
    setSelectedResId('');
    setReqQty(1);
  };

  const handleRemoveResource = (resId: number) => {
    setAssignedResources(prev => prev.filter(r => r.resource_id !== resId));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.task_name?.trim()) {
      alert("Task Name is required!");
      return;
    }
    
    const payload: any = { ...formData };
    
    // Convert all numeric string values back to numbers if needed
    for (const k of Object.keys(payload)) {
      if (payload[k] === '') payload[k] = null;
      else if (k !== 'task_name' && k !== 'task_type' && k !== 'status' && k !== 'calendar_type' && k !== 'baseline_start' && k !== 'id' && k !== 'metadata_json') {
        const num = Number(payload[k]);
        if (!isNaN(num)) payload[k] = num;
      }
    }

    if (payload.baseline_start) {
      payload.baseline_start = new Date(payload.baseline_start).toISOString();
    }

    if (predecessor.id) {
      payload.predecessor_id = predecessor.id;
      payload.dependency_type = predecessor.type;
      payload.lag_days = Number(predecessor.lag);
    }

    payload.stagedResources = assignedResources;

    onSubmit(payload);
  };

  const renderNumberFields = (groupId: string) => (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-3">
      {FIELD_GROUPS[groupId as keyof typeof FIELD_GROUPS].map(field => (
        <div key={field.key}>
          <label className="block text-xs font-semibold text-slate-600 mb-1 line-clamp-1" title={field.label}>
            {field.label}
          </label>
          <input 
            type="number"
            step="0.01"
            value={formData[field.key] || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors bg-white"
          />
        </div>
      ))}
    </div>
  );

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
            {TABS.map(tab => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium mb-1 transition-all ${
                  activeTab === tab.id 
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
              
              {/* TAB 1: BASIC */}
              {activeTab === 'basic' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Core Attributes</h3>
                    <div className="grid grid-cols-2 gap-4">
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
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Task Type</label>
                        <select 
                          value={formData.task_type || 'Construction'}
                          onChange={(e) => handleChange('task_type', e.target.value)}
                          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white"
                        >
                          <option value="Construction">Construction</option>
                          <option value="Design">Design</option>
                          <option value="Procurement">Procurement</option>
                          <option value="Management">Management</option>
                          <option value="Other">Other</option>
                        </select>
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
                    <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Scheduling (Duration)</h3>
                    <div className="grid grid-cols-4 gap-4">
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
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Days (Required)</label>
                        <input 
                          type="number"
                          value={formData.duration_days || 1}
                          onChange={(e) => handleChange('duration_days', e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Months (Opt)</label>
                        <input 
                          type="number" step="0.1"
                          value={formData.duration_months || ''}
                          onChange={(e) => handleChange('duration_months', e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Hours (Opt)</label>
                        <input 
                          type="number" step="0.5"
                          value={formData.duration_hours || ''}
                          onChange={(e) => handleChange('duration_hours', e.target.value)}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <h3 className="text-sm font-bold text-slate-800 mb-2">Network Logic Constraints</h3>
                    <p className="text-xs text-slate-500 mb-3">Edges connecting this node. (Drag-and-drop on graph to add, or select below).</p>
                    
                    {/* Existing Logic */}
                    {(existingPredecessors.length > 0 || existingSuccessors.length > 0) && (
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
                            {existingPredecessors.map(p => (
                              <tr key={`p-${p.predecessor_id}`} className="border-b border-slate-100">
                                <td className="px-3 py-1.5 text-amber-600 font-bold">← Predecessor</td>
                                <td className="px-3 py-1.5 font-medium">{p.name} ({p.predecessor_id})</td>
                                <td className="px-3 py-1.5">{p.dependency_type}</td>
                                <td className="px-3 py-1.5">{p.lag_days}</td>
                              </tr>
                            ))}
                            {existingSuccessors.map(s => (
                              <tr key={`s-${s.successor_id}`} className="border-b border-slate-100">
                                <td className="px-3 py-1.5 text-blue-600 font-bold">→ Successor</td>
                                <td className="px-3 py-1.5 font-medium">{s.name} ({s.successor_id})</td>
                                <td className="px-3 py-1.5">{s.dependency_type}</td>
                                <td className="px-3 py-1.5">{s.lag_days}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-3 md:col-span-1">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">+ Add Predecessor</label>
                        <select 
                          value={predecessor.id}
                          onChange={(e) => setPredecessor(p => ({ ...p, id: e.target.value }))}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white"
                        >
                          <option value="">None</option>
                          {availableTasks.filter(t => t.id !== initialData?.id && !existingPredecessors.some(p => p.predecessor_id === t.id)).map(t => (
                            <option key={t.id} value={t.id}>{t.task_name} ({t.id})</option>
                          ))}
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
                      <div className="col-span-1">
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Lag (days)</label>
                        <input 
                          type="number"
                          value={predecessor.lag}
                          onChange={(e) => setPredecessor(p => ({ ...p, lag: Number(e.target.value) }))}
                          disabled={!predecessor.id}
                          className="w-full border border-slate-300 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-50"
                        />
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
                            <option key={r.id} value={r.id}>{r.resource_name} ({r.resource_type})</option>
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
              {activeTab === 'direct' && <div className="animate-in fade-in slide-in-from-right-4 duration-300">{renderNumberFields('direct')}</div>}
              {activeTab === 'indirect' && <div className="animate-in fade-in slide-in-from-right-4 duration-300">{renderNumberFields('indirect')}</div>}
              {activeTab === 'logistics' && <div className="animate-in fade-in slide-in-from-right-4 duration-300">{renderNumberFields('logistics')}</div>}
              {activeTab === 'risk_hr' && <div className="animate-in fade-in slide-in-from-right-4 duration-300">{renderNumberFields('risk_hr')}</div>}
              {activeTab === 'esg' && <div className="animate-in fade-in slide-in-from-right-4 duration-300">{renderNumberFields('esg')}</div>}

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

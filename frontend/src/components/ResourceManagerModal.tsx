import React, { useState, useEffect } from 'react';
import { X, Save, Trash2, Plus, HardHat, Package } from 'lucide-react';
import { api } from '../services/api';

interface ResourceManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
  initialResources: any[];
}

export default function ResourceManagerModal({ isOpen, onClose, projectId, initialResources }: ResourceManagerModalProps) {
  const [resources, setResources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // New resource form state
  const [name, setName] = useState('');
  const [type, setType] = useState('Renewable');
  const [maxAvail, setMaxAvail] = useState(1);
  const [costPerUse, setCostPerUse] = useState(0);
  const [costPerUnit, setCostPerUnit] = useState(0);

  useEffect(() => {
    if (isOpen) {
      setResources(initialResources || []);
    }
  }, [isOpen, initialResources]);

  if (!isOpen) return null;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    setLoading(true);
    try {
      const payload = {
        resource_name: name,
        resource_type: type,
        max_availability: Number(maxAvail),
        cost_per_use: Number(costPerUse),
        cost_per_unit: Number(costPerUnit)
      };
      const res = await api.createResourceConstraint(projectId, payload);
      
      // Update local state
      setResources([...resources, res.data]);
      
      // Reset form
      setName('');
      setMaxAvail(1);
      setCostPerUse(0);
      setCostPerUnit(0);
    } catch (err) {
      alert("Failed to add resource: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this resource?")) return;
    try {
      await api.deleteResourceConstraint(projectId, id);
      setResources(resources.filter(r => r.id !== id));
    } catch (err) {
      alert("Failed to delete resource");
    }
  };

  const handleFinish = () => {
    onClose();
    window.location.reload(); // Reload to fetch fresh data in Workspace
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 shrink-0">
          <div>
            <h2 className="text-xl font-bold text-slate-800 flex items-center">
              <HardHat className="mr-2 text-amber-600" size={24} />
              Project Resource Pool (Resource Constraints)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Manage global resources (Renewable: Labor/Equipment, Consumable: Materials) available for this project.</p>
          </div>
          <button onClick={handleFinish} className="text-slate-400 hover:text-slate-700 transition p-1.5 rounded-md hover:bg-slate-200">
            <X size={22} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
          
          {/* Add New Resource Form */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm mb-6">
            <h3 className="text-sm font-bold text-slate-800 mb-3">Add New Resource</h3>
            <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Resource Name</label>
                <input 
                  type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="e.g. Tower Crane"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div className="w-32">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Type</label>
                <select 
                  value={type} onChange={e => setType(e.target.value)}
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500/20"
                >
                  <option value="Renewable">Renewable</option>
                  <option value="Consumable">Consumable</option>
                </select>
              </div>
              <div className="w-24">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Max Avail</label>
                <input 
                  type="number" step="0.1" value={maxAvail} onChange={e => setMaxAvail(Number(e.target.value))} required min="0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div className="w-28">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Cost/Use</label>
                <input 
                  type="number" step="0.01" value={costPerUse} onChange={e => setCostPerUse(Number(e.target.value))} min="0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div className="w-28">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Cost/Unit</label>
                <input 
                  type="number" step="0.01" value={costPerUnit} onChange={e => setCostPerUnit(Number(e.target.value))} min="0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <button 
                type="submit" disabled={loading}
                className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-md text-sm font-bold flex items-center transition h-[38px]"
              >
                <Plus size={16} className="mr-1" /> Add
              </button>
            </form>
          </div>

          {/* Resource List Table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-600 bg-slate-50 uppercase font-bold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Resource Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3 text-right">Max Availability</th>
                  <th className="px-4 py-3 text-right">Cost / Use</th>
                  <th className="px-4 py-3 text-right">Cost / Unit</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {resources.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-400">
                      <Package size={32} className="mx-auto mb-2 opacity-50" />
                      No resources configured for this project yet.
                    </td>
                  </tr>
                ) : (
                  resources.map(r => (
                    <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-semibold text-slate-800">{r.resource_name}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${r.resource_type === 'Renewable' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}`}>
                          {r.resource_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700">{r.max_availability}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700">${r.cost_per_use}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700">${r.cost_per_unit}</td>
                      <td className="px-4 py-3 text-center">
                        <button 
                          onClick={() => handleDelete(r.id)}
                          className="text-slate-400 hover:text-red-600 transition p-1.5 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

        </div>

        <div className="p-4 border-t border-slate-200 shrink-0 flex justify-end bg-white">
          <button 
            onClick={handleFinish}
            className="px-6 py-2 text-sm font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
}

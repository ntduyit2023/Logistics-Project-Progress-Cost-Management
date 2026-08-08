import React, { useState, useEffect } from 'react';
import { X, Save, Trash2, Plus, HardHat, Package, Edit2, Check } from 'lucide-react';
import { api } from '../services/api';

interface ResourceManagerModalProps {
  isOpen: boolean;
  onClose: (refresh?: boolean) => void;
  projectId: number | string;
  initialResources: any[];
}

export default function ResourceManagerModal({ isOpen, onClose, projectId, initialResources }: ResourceManagerModalProps) {
  const [resources, setResources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // New resource form state
  const [name, setName] = useState('');
  const [resCategory, setResCategory] = useState('Human');
  const [maxAvail, setMaxAvail] = useState(10);
  const [unitCost, setUnitCost] = useState(25.0);
  const [energy, setEnergy] = useState(0.0);
  const [overtimeMulti, setOvertimeMulti] = useState(1.5);
  const [maxOtDay, setMaxOtDay] = useState(4.0);
  const [addresEff, setAddresEff] = useState(0.7);

  // Inline edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editRowData, setEditRowData] = useState<any>({});

  const fetchResources = async () => {
    if (!projectId) return;
    try {
      const res = await api.getResourceConstraints(projectId);
      if (res && res.data) {
        setResources(res.data);
      } else {
        setResources(initialResources || []);
      }
    } catch (err) {
      console.error("Failed to fetch fresh resource constraints", err);
      setResources(initialResources || []);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchResources();
    }
  }, [isOpen, projectId, initialResources]);

  if (!isOpen) return null;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    
    setLoading(true);
    try {
      const payload = {
        resource_id: String(Date.now()),
        name: name.trim(),
        type: resCategory,
        max_availability: Number(maxAvail),
        unit_cost: Number(unitCost),
        energy: Number(energy),
        overtime_multi: Number(overtimeMulti),
        max_overtime_per_day: Number(maxOtDay),
        addres_efficiency: Number(addresEff)
      };
      await api.createResourceConstraint(projectId, payload);
      
      // Refresh resource list
      await fetchResources();
      
      // Reset form
      setName('');
      setMaxAvail(10);
      setUnitCost(25.0);
      setEnergy(0.0);
      setOvertimeMulti(1.5);
      setMaxOtDay(4.0);
      setAddresEff(0.7);
    } catch (err) {
      alert("Failed to add resource: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (r: any) => {
    setEditingId(r.id);
    setEditRowData({
      id: r.id,
      resource_id: r.resource_id || String(r.id),
      name: r.name || r.resource_name || r.resource_id || '',
      type: r.type || r.resource_type || 'Human',
      max_availability: r.max_availability ?? 1,
      unit_cost: r.unit_cost ?? 0,
      energy: r.energy ?? 0,
      overtime_multi: r.overtime_multi ?? 1.5,
      max_overtime_per_day: r.max_overtime_per_day ?? 4.0,
      addres_efficiency: r.addres_efficiency ?? 0.7
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditRowData({});
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    try {
      const payload = {
        resource_id: editRowData.resource_id || String(editingId),
        name: editRowData.name,
        type: editRowData.type,
        max_availability: Number(editRowData.max_availability),
        unit_cost: Number(editRowData.unit_cost),
        energy: Number(editRowData.energy),
        overtime_multi: Number(editRowData.overtime_multi),
        max_overtime_per_day: Number(editRowData.max_overtime_per_day),
        addres_efficiency: Number(editRowData.addres_efficiency)
      };
      await api.updateResourceConstraint(projectId, editingId, payload);
      await fetchResources();
      setEditingId(null);
    } catch (err) {
      alert("Failed to update resource: " + (err as Error).message);
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
    onClose(true);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-slate-200 bg-slate-50 shrink-0">
          <div>
            <h2 className="text-lg font-black text-slate-800 flex items-center">
              <Users size={20} className="mr-2 text-blue-600" />
              Project Resource Pool
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Manage project resource inventory (Type, Unit Cost/hr, Energy Rate, Overtime Multiplier).</p>
          </div>
          <button onClick={handleFinish} className="text-slate-400 hover:text-slate-700 transition p-1.5 rounded-md hover:bg-slate-200">
            <X size={22} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
          
          {/* Add New Resource Form */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm mb-6">
            <h3 className="text-sm font-bold text-slate-800 mb-3">Add New Resource</h3>
            <form onSubmit={handleAdd} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 items-end">
              <div className="col-span-1 sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Resource Name</label>
                <input 
                  type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="e.g., Civil Engineer / Excavator"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Type</label>
                <select 
                  value={resCategory} onChange={e => {
                    setResCategory(e.target.value);
                    if (e.target.value !== 'Machine') setEnergy(0.0);
                  }}
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500/20"
                >
                  <option value="Human">Human</option>
                  <option value="Machine">Machine</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Capacity</label>
                <input 
                  type="number" step="1" value={maxAvail} onChange={e => setMaxAvail(Number(e.target.value))} required min="1"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Unit Cost ($/hr)</label>
                <input 
                  type="number" step="0.5" value={unitCost} onChange={e => setUnitCost(Number(e.target.value))} required min="0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Energy Rate (kWh or L/h)</label>
                <input 
                  type="number" step="0.1" value={energy} onChange={e => setEnergy(Number(e.target.value))} min="0"
                  disabled={resCategory !== 'Machine'}
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 disabled:bg-slate-100 disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">OT Multiplier</label>
                <input 
                  type="number" step="0.1" value={overtimeMulti} onChange={e => setOvertimeMulti(Number(e.target.value))} min="1.0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Max OT (hrs/day)</label>
                <input 
                  type="number" step="0.5" value={maxOtDay} onChange={e => setMaxOtDay(Number(e.target.value))} min="0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Efficiency</label>
                <input 
                  type="number" step="0.1" value={addresEff} onChange={e => setAddresEff(Number(e.target.value))} min="0.1" max="1.0"
                  className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                />
              </div>

              <div className="col-span-1 sm:col-span-2 md:col-span-4 flex justify-end mt-2">
                <button 
                  type="submit" disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-md text-sm font-bold flex items-center transition shadow-sm"
                >
                  <Plus size={16} className="mr-1" /> Add Resource
                </button>
              </div>
            </form>
          </div>

          {/* Resource List Table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-600 bg-slate-50 uppercase font-bold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Resource Name</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3 text-right">Max Capacity</th>
                  <th className="px-4 py-3 text-right">Unit Cost ($/h)</th>
                  <th className="px-4 py-3 text-right">Energy / Fuel</th>
                  <th className="px-4 py-3 text-right">OT Multi / Max OT</th>
                  <th className="px-4 py-3 text-right">AddRes Eff</th>
                  <th className="px-4 py-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {resources.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-slate-400">
                      <Package size={32} className="mx-auto mb-2 opacity-50" />
                      No resources configured for this project yet.
                    </td>
                  </tr>
                ) : (
                  resources.map(r => {
                    const isEditing = editingId === r.id;
                    const resName = r.name || r.resource_name || r.resource_id;
                    const resType = r.type || r.resource_type || 'Human';
                    const maxCapacity = r.max_availability ?? 1;
                    const costVal = r.unit_cost ?? 0;
                    const energyVal = r.energy ?? 0;
                    const otMulti = r.overtime_multi ?? 1.5;
                    const maxOt = r.max_overtime_per_day ?? 4;
                    const eff = r.addres_efficiency ?? 0.7;

                    if (isEditing) {
                      return (
                        <tr key={r.id} className="bg-amber-50/60 border-b border-amber-200">
                          <td className="px-3 py-2">
                            <input 
                              type="text"
                              value={editRowData.name}
                              onChange={e => setEditRowData({ ...editRowData, name: e.target.value })}
                              className="w-full border border-amber-400 rounded px-2 py-1 text-sm bg-white font-medium focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            <select 
                              value={editRowData.type}
                              onChange={e => {
                                const newType = e.target.value;
                                setEditRowData({ ...editRowData, type: newType, energy: newType !== 'Machine' ? 0 : editRowData.energy });
                              }}
                              className="border border-amber-400 rounded px-2 py-1 text-xs bg-white font-medium focus:outline-none"
                            >
                              <option value="Human">Human</option>
                              <option value="Machine">Machine</option>
                            </select>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <input 
                              type="number" step="1" min="1"
                              value={editRowData.max_availability}
                              onChange={e => setEditRowData({ ...editRowData, max_availability: e.target.value })}
                              className="w-20 border border-amber-400 rounded px-2 py-1 text-sm text-right bg-white focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2 text-right">
                            <input 
                              type="number" step="0.5" min="0"
                              value={editRowData.unit_cost}
                              onChange={e => setEditRowData({ ...editRowData, unit_cost: e.target.value })}
                              className="w-24 border border-amber-400 rounded px-2 py-1 text-sm text-right bg-white focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2 text-right">
                            <input 
                              type="number" step="0.1" min="0"
                              value={editRowData.energy}
                              onChange={e => setEditRowData({ ...editRowData, energy: e.target.value })}
                              disabled={editRowData.type !== 'Machine'}
                              className="w-20 border border-amber-400 rounded px-2 py-1 text-sm text-right bg-white focus:outline-none disabled:bg-slate-100 disabled:opacity-60 disabled:cursor-not-allowed"
                            />
                          </td>
                          <td className="px-3 py-2 text-right flex items-center justify-end gap-1">
                            <input 
                              type="number" step="0.1" min="1.0" title="OT Multiplier"
                              value={editRowData.overtime_multi}
                              onChange={e => setEditRowData({ ...editRowData, overtime_multi: e.target.value })}
                              className="w-14 border border-amber-400 rounded px-1 py-1 text-xs text-right bg-white focus:outline-none"
                            />
                            <span className="text-xs text-slate-500">x /</span>
                            <input 
                              type="number" step="0.5" min="0" title="Max OT hours/day"
                              value={editRowData.max_overtime_per_day}
                              onChange={e => setEditRowData({ ...editRowData, max_overtime_per_day: e.target.value })}
                              className="w-14 border border-amber-400 rounded px-1 py-1 text-xs text-right bg-white focus:outline-none"
                            />
                            <span className="text-xs text-slate-500">h</span>
                          </td>
                          <td className="px-3 py-2 text-right">
                            <input 
                              type="number" step="0.1" min="0.1" max="1.0"
                              value={editRowData.addres_efficiency}
                              onChange={e => setEditRowData({ ...editRowData, addres_efficiency: e.target.value })}
                              className="w-16 border border-amber-400 rounded px-2 py-1 text-sm text-right bg-white focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <button 
                                onClick={handleSaveEdit}
                                title="Save"
                                className="bg-emerald-600 hover:bg-emerald-700 text-white p-1 rounded transition"
                              >
                                <Check size={16} />
                              </button>
                              <button 
                                onClick={cancelEdit}
                                title="Cancel"
                                className="bg-slate-300 hover:bg-slate-400 text-slate-700 p-1 rounded transition"
                              >
                                <X size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    }

                    return (
                      <tr key={r.id || r.resource_id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                        <td className="px-4 py-3 font-semibold text-slate-800">{resName}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${resType === 'Human' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'}`}>
                            {resType}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-slate-700">{maxCapacity}</td>
                        <td className="px-4 py-3 text-right font-medium text-slate-700">${costVal}</td>
                        <td className="px-4 py-3 text-right font-medium text-slate-700">{energyVal}</td>
                        <td className="px-4 py-3 text-right font-medium text-slate-700">{otMulti}x ({maxOt}h/day)</td>
                        <td className="px-4 py-3 text-right font-medium text-slate-700">{eff}</td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <button 
                              onClick={() => startEdit(r)}
                              title="Edit Resource"
                              className="text-slate-400 hover:text-blue-600 transition p-1.5 hover:bg-blue-50 rounded"
                            >
                              <Edit2 size={15} />
                            </button>
                            <button 
                              onClick={() => handleDelete(r.id)}
                              title="Delete Resource"
                              className="text-slate-400 hover:text-red-600 transition p-1.5 hover:bg-red-50 rounded"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
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

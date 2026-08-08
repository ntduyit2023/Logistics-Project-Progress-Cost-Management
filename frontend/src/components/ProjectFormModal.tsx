import React, { useState, useEffect } from 'react';
import { X, Save, FolderPlus, FolderEdit } from 'lucide-react';

interface ProjectFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { id?: string; project_name: string; status: string; type?: string }) => void;
  initialData?: { id?: string; project_name: string; status: string; type?: string } | null;
}

export default function ProjectFormModal({ isOpen, onClose, onSubmit, initialData }: ProjectFormModalProps) {
  const [projectId, setProjectId] = useState('');
  const [projectName, setProjectName] = useState('');
  const [status, setStatus] = useState('Planning');
  const [projectType, setProjectType] = useState('ITLG');

  useEffect(() => {
    if (initialData) {
      setProjectId(initialData.id || '');
      setProjectName(initialData.project_name);
      setStatus(initialData.status || 'Planning');
      setProjectType(initialData.type || 'ITLG');
    } else {
      setProjectId('');
      setProjectName('');
      setStatus('Planning');
      setProjectType('ITLG');
    }
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) return;
    if (projectName.trim().length < 3) {
      alert("Project name must be at least 3 characters long.");
      return;
    }
    onSubmit({ id: projectId.trim() || undefined, project_name: projectName, status, type: projectType });
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${initialData ? 'bg-blue-100 text-blue-600' : 'bg-violet-100 text-violet-600'}`}>
              {initialData ? <FolderEdit size={20} /> : <FolderPlus size={20} />}
            </div>
            <h2 className="text-lg font-bold text-slate-800">
              {initialData ? 'Edit Project Details' : 'Create New Project'}
            </h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition p-1.5 rounded-lg hover:bg-slate-200/50">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Project ID (Optional)</label>
              <input 
                type="text" 
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="e.g. PRJ-2024-01"
                disabled={!!initialData}
                className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-slate-50 focus:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1.5">Project Name <span className="text-red-500">*</span></label>
              <input 
                type="text" 
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Alpha Tower Construction"
                className="w-full border border-slate-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-slate-50 focus:bg-white"
                autoFocus
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1.5">Project Type</label>
                <select 
                  value={projectType}
                  onChange={(e) => setProjectType(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-slate-50 focus:bg-white"
                >
                  <option value="ITLG">IT & Logistics (ITLG)</option>
                  <option value="CON">Civil Construction (CON)</option>
                  <option value="PRO">Professional Services (PRO)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1.5">Status</label>
                <select 
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-slate-50 focus:bg-white"
                >
                  <option value="Planning">Planning</option>
                  <option value="Execution">Execution</option>
                  <option value="Completed">Completed</option>
                  <option value="On Hold">On Hold</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="mt-8 pt-5 border-t border-slate-100 flex gap-3 justify-end">
            <button 
              type="button" 
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-bold text-slate-600 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-all"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={!projectName.trim()}
              className="px-5 py-2.5 text-sm font-bold text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all flex items-center shadow-sm hover:shadow"
            >
              <Save size={16} className="mr-2" />
              {initialData ? 'Save Changes' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';

interface ProjectFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { project_name: string; status: string }) => void;
  initialData?: { project_name: string; status: string } | null;
}

export default function ProjectFormModal({ isOpen, onClose, onSubmit, initialData }: ProjectFormModalProps) {
  const [projectName, setProjectName] = useState('');
  const [status, setStatus] = useState('Planning');

  useEffect(() => {
    if (initialData) {
      setProjectName(initialData.project_name);
      setStatus(initialData.status || 'Planning');
    } else {
      setProjectName('');
      setStatus('Planning');
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
    onSubmit({ project_name: projectName, status });
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-800">
            {initialData ? 'Edit Project' : 'Create New Project'}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition p-1 rounded-md hover:bg-slate-200/50">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Project Name</label>
              <input 
                type="text" 
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Alpha Tower Construction"
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-colors"
                autoFocus
              />
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Status</label>
              <select 
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-colors bg-white"
              >
                <option value="Planning">Planning</option>
                <option value="Execution">Execution</option>
                <option value="Completed">Completed</option>
                <option value="On Hold">On Hold</option>
              </select>
            </div>
          </div>
          
          <div className="mt-6 flex gap-3 justify-end">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={!projectName.trim()}
              className="px-4 py-2 text-sm font-semibold text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-50 rounded-lg transition-colors flex items-center"
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

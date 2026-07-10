import React from 'react';
import { Trash2, Edit2, Activity, Layers, DollarSign, Zap } from 'lucide-react';

interface ProjectCardProps {
  project: any;
  onClick: (id: number) => void;
  onEdit: (e: React.MouseEvent, project: any) => void;
  onDelete: (e: React.MouseEvent, id: number) => void;
  onRunAI: (e: React.MouseEvent, id: number) => void;
}

export default function ProjectCard({ project: p, onClick, onEdit, onDelete, onRunAI }: ProjectCardProps) {
  return (
    <div 
      onClick={() => onClick(p.id)}
      className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-violet-300 transition-all cursor-pointer group flex flex-col"
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold text-slate-800 line-clamp-1 group-hover:text-violet-700 transition-colors">
          {p.project_name}
        </h3>
        <div className="flex gap-1 transition-opacity">
          <button 
            onClick={(e) => onRunAI(e, p.id)}
            className="p-1.5 text-slate-400 hover:text-amber-500 hover:bg-amber-50 rounded-md transition-colors"
            title="Run AI Simulation"
          >
            <Zap size={16} />
          </button>
          <button 
            onClick={(e) => onEdit(e, p)}
            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
            title="Edit"
          >
            <Edit2 size={16} />
          </button>
          <button 
            onClick={(e) => onDelete(e, p.id)}
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
            title="Delete"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
          p.status === 'Execution' ? 'bg-emerald-100 text-emerald-700' :
          p.status === 'Planning' ? 'bg-amber-100 text-amber-700' :
          p.status === 'Completed' ? 'bg-blue-100 text-blue-700' :
          'bg-slate-100 text-slate-700'
        }`}>
          {p.status || 'Planning'}
        </span>
        {p.type && (
          <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-indigo-100 text-indigo-700">
            {p.type}
          </span>
        )}
      </div>

      <div className="mt-auto grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 mb-3">
        <div className="flex items-center text-slate-500">
          <Layers size={16} className="mr-2 text-slate-400" />
          <span className="text-sm font-semibold">{p.num_tasks || 0} Tasks</span>
        </div>
        <div className="flex items-center text-slate-500">
          <Activity size={16} className="mr-2 text-slate-400" />
          <span className="text-sm font-semibold">{p.num_edges || 0} Edges</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-3">
        <div className="flex flex-col">
          <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Base Cost</span>
          <div className="flex items-center text-slate-700 font-semibold">
            <DollarSign size={14} className="text-emerald-500 mr-1" />
            {p.base_cost ? p.base_cost.toLocaleString() : '0'}
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-1">Final Cost</span>
          <div className="flex items-center text-slate-700 font-semibold">
            <DollarSign size={14} className="text-rose-500 mr-1" />
            {p.total_cost ? p.total_cost.toLocaleString() : '0'}
          </div>
        </div>
      </div>
    </div>
  );
}

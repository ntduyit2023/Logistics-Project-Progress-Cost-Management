import React from 'react';
import { Handle, Position } from 'reactflow';
import { Calendar, Clock, DollarSign, Users } from 'lucide-react';

const TaskNode = ({ data }: any) => {
  const isCritical = Boolean(data.is_critical);
  const isAiOptimized = Boolean(data.is_ai_optimized);

  // Determine border and background based on Option 1 state
  let cardClass = 'bg-white border-slate-300 text-slate-900 hover:border-slate-400';
  
  if (isCritical && isAiOptimized) {
    // Both Critical Path & AI Optimized (Option 1: Emerald bg + Red border)
    cardClass = 'bg-emerald-50/90 border-2 border-rose-500 text-slate-900 shadow-md shadow-rose-100 hover:shadow-rose-200 ring-1 ring-rose-300';
  } else if (isAiOptimized) {
    // AI Optimized only
    cardClass = 'bg-emerald-50 border-emerald-500 text-emerald-950 shadow-emerald-100 hover:shadow-emerald-200';
  } else if (isCritical) {
    // Critical Path only
    cardClass = 'bg-rose-50 border-rose-500 text-rose-950 shadow-rose-100 hover:shadow-rose-200';
  }

  return (
    <div 
      className={`rounded-lg shadow-sm ${cardClass} w-56 h-20 flex items-center px-3 transition-all hover:shadow-md cursor-pointer`}
      title={`${data.wbs} - ${data.task_name}\nDuration: ${data.duration}h | Cost: $${Number(data.total_cost).toLocaleString()}`}
    >
      <Handle type="target" position={Position.Left} className="w-1.5 h-1.5 bg-blue-600 border-none" />
      
      <div className="flex flex-col w-full min-w-0">
        <div className="flex justify-between items-center mb-0.5">
          <span className="text-[10px] font-bold text-slate-500 leading-none flex items-center gap-1">
            WBS {data.wbs} {isCritical && <span className="text-rose-500 animate-pulse">🔥</span>}
          </span>
          {isCritical && isAiOptimized && (
            <span className="text-[7.5px] font-black bg-rose-500 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm flex items-center gap-0.5">
              CRITICAL • AI
            </span>
          )}
          {isAiOptimized && !isCritical && (
            <span className="text-[8px] font-extrabold bg-emerald-600 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              AI OPTIMIZED
            </span>
          )}
          {isCritical && !isAiOptimized && (
            <span className="text-[8px] font-extrabold bg-rose-600 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              CRITICAL
            </span>
          )}
        </div>
        <span className="text-[12px] font-bold truncate text-slate-800 leading-tight my-0.5" title={data.task_name}>
          {data.task_name || 'Unnamed Task'}
        </span>
        <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium border-t border-slate-100 pt-1">
          <div className="flex items-center gap-0.5" title="Start Date">
            <Calendar size={10} className="text-slate-400" />
            <span>{data.baseline_start ? new Date(data.baseline_start).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'TBD'}</span>
          </div>
          <div className="flex items-center gap-0.5" title="Duration">
            <Clock size={10} className="text-slate-400" />
            <span>{data.duration}h</span>
          </div>
          <div className="flex items-center gap-0.5" title="Cost">
            <DollarSign size={10} className="text-slate-400" />
            <span>{(Number(data.total_cost)/1000).toFixed(1)}k</span>
          </div>
          {data.resources && data.resources.length > 0 && (
            <div className="flex items-center gap-0.5 text-blue-600 bg-blue-50 px-1 rounded border border-blue-100/60" title={data.mode === 2 ? "Công việc thuê ngoài - Giải phóng nhân sự nội bộ" : data.resources.map((r: any) => `${r.resource_id}: ${r.quantity}`).join(', ')}>
              <Users size={10} />
              <span>{data.mode === 2 ? 0 : data.resources[0].quantity}</span>
            </div>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-1.5 h-1.5 bg-blue-600 border-none" />
    </div>
  );
};

export default React.memo(TaskNode);

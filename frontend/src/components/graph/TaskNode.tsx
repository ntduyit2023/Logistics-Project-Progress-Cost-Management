import React from 'react';
import { Handle, Position } from 'reactflow';
import { Calendar, Clock, DollarSign, Wrench, Hammer, FileText, Zap } from 'lucide-react';

const TaskNode = ({ data }: any) => {

  const isAiOptimized = Boolean(data.is_ai_optimized);
  const mode = data.mode || 0; 
  
  const otHours = data.overtime_hours_per_day || data.overtime_hours ? parseFloat(data.overtime_hours_per_day || data.overtime_hours) : 0;
  const otCost = data.overtime_cost || data.overtime ? parseFloat(data.overtime_cost || data.overtime) : 0;
  const durDiff = data.base_duration && data.duration && (data.base_duration > data.duration + 0.01) ? Math.round((data.base_duration - data.duration) * 10) / 10 : 0;
  
  const addedResCost = parseFloat(data.added_resources_cost || 0);
  const otPremium = parseFloat(data.labor_ot_premium || 0) + parseFloat(data.equipment_ot_extra || 0) + parseFloat(data.energy_ot_extra || 0);
  
  let costDiff = (data.total_cost || 0) - (data.base_cost || 0);
  if (costDiff <= 0 && (addedResCost > 0 || otPremium > 0)) {
    costDiff = addedResCost + otPremium;
  }
  const displayBaseCost = parseFloat(data.base_cost || 0);
  const displayTotalCost = displayBaseCost + costDiff;
  
  const isCrashedTask = durDiff > 0 || otHours > 0 || otCost > 0 || (isAiOptimized && data.mode === 1);
  const crashStrategy = data.crashing_strategy || (isCrashedTask ? (otHours > 0 ? 'OT' : 'AddRes') : 'Normal');

  let actualMode = data.mode !== undefined ? data.mode : 0;
  if (data.mode === undefined) {
    if (crashStrategy === 'OT') actualMode = 1;
    else if (crashStrategy === 'AddRes') actualMode = 2;
    else if (crashStrategy === 'Hybrid') actualMode = 3;
    else actualMode = 0;
  }

  // Determine border and background based on Mode
  let cardClass = 'bg-white border border-slate-300 shadow-md text-slate-800 hover:border-indigo-400 hover:shadow-lg';
  if (actualMode === 1) {
    cardClass = 'bg-amber-50 border-2 border-amber-400 text-slate-900 shadow-md';
  } else if (actualMode === 2) {
    cardClass = 'bg-purple-50 border-2 border-purple-500 text-purple-950 shadow-md';
  } else if (actualMode === 3) {
    cardClass = 'bg-rose-50 border-2 border-rose-400 text-slate-900 shadow-md';
  }
  


  const formatShortDate = (dateStr: any) => {
    if (!dateStr) return 'TBD';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'TBD';
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
  };

  const startDateStr = formatShortDate(data.baseline_start);
  const endDateStr = formatShortDate(data.baseline_end);

  const tooltipText = `${data.wbs} - ${data.task_name}\nTime: ${startDateStr} - ${endDateStr}\nDuration: ${data.duration}h\nTotal Cost: $${Number(data.total_cost).toLocaleString()}`;

  return (
    <div 
      className={`rounded-xl shadow-sm ${cardClass} w-[240px] p-3 transition-all hover:shadow-md cursor-pointer relative group flex flex-col gap-2`}
      title={tooltipText}
    >
      <Handle type="target" position={Position.Left} className="w-2 h-2 bg-slate-400 border-2 border-white rounded-full -ml-1" />
      
      {/* Header: WBS and Type */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-black text-slate-600 font-mono tracking-tight bg-slate-100 px-1.5 py-0.5 rounded">
            {data.wbs}
          </span>
        </div>
        <div className="flex items-center gap-1">

          {actualMode === 1 && (
            <span className="text-[10px] font-black bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded flex items-center gap-0.5 border border-amber-200">
              <Zap size={10} /> OT
            </span>
          )}
          {actualMode === 2 && (
            <span className="text-[10px] font-black bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded flex items-center gap-0.5 border border-purple-200">
              <Zap size={10} /> Add resource
            </span>
          )}
          {actualMode === 3 && (
            <span className="text-[10px] font-black bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded flex items-center gap-0.5 border border-rose-200">
              <Zap size={10} /> Hybrid
            </span>
          )}
        </div>
      </div>

      {/* Body: Task Name */}
      <div className="text-[12px] font-bold leading-tight line-clamp-2 min-h-[30px]" title={data.task_name}>
        {data.task_name || 'Unnamed Task'}
      </div>

      {/* Footer: Metrics */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100/50 mt-1">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500">
            <Clock size={12} className="text-indigo-400" />
            {durDiff > 0 ? (
              <div className="flex items-center gap-1">
                <span className="line-through text-slate-400">{data.base_duration}h</span>
                <span className="text-amber-600 font-bold">➔ {data.duration}h</span>
              </div>
            ) : (
              <span>{data.duration}h</span>
            )}
          </div>
          {costDiff > 0 && actualMode > 0 && (
             <div className="flex items-center gap-1 text-[10px] font-medium text-rose-500">
               <DollarSign size={10} />
               <div className="flex items-center gap-1">
                 <span className="line-through text-rose-300">${Math.round(displayBaseCost).toLocaleString()}</span>
                 <span className="font-bold">➔ ${Math.round(displayTotalCost).toLocaleString()}</span>
               </div>
             </div>
          )}
          {data.extra_workers > 0 && (
            <div className="flex items-center gap-1 text-[10px] font-bold text-purple-600 bg-purple-50 px-1 py-0.5 rounded w-fit">
              + {data.extra_workers} workers
            </div>
          )}
          {otHours > 0 && (
            <div className="flex items-center gap-1 text-[10px] font-bold text-amber-600 bg-amber-50 px-1 py-0.5 rounded w-fit mt-0.5">
              + {otHours}h OT/day
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 text-[9.5px] font-semibold text-slate-500">
          <div className="flex items-center gap-1">
            <span className="text-slate-400">S:</span> {startDateStr}
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-400">F:</span> {endDateStr}
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-2 h-2 bg-slate-400 border-2 border-white rounded-full -mr-1" />
    </div>
  );
};

export default TaskNode;

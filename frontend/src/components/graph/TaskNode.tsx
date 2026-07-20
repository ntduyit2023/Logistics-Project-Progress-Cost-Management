import React from 'react';
import { Handle, Position } from 'reactflow';
import { Calendar, Clock, DollarSign, Users } from 'lucide-react';

const TaskNode = ({ data }: any) => {
  // Determine border and background based on state
  let cardClass = 'bg-white border-slate-300 text-slate-900 hover:border-slate-400';
  if (data.is_critical) {
    cardClass = 'bg-rose-50 border-rose-500 text-rose-950 shadow-rose-100 hover:shadow-rose-200';
  } else if (data.mode === 1) {
    cardClass = 'bg-amber-50 border-amber-500 text-amber-950 shadow-amber-100 hover:shadow-amber-200';
  } else if (data.mode === 2) {
    cardClass = 'bg-violet-50 border-violet-500 text-violet-950 shadow-violet-100 hover:shadow-violet-200';
  }

  const getAdjustmentExplanation = () => {
    if (data.mode === 1) {
      const diffDur = (data.base_duration || 0) - (data.duration || 0);
      const diffCost = (data.total_cost || 0) - (data.base_cost || 0);
      return `Rút ngắn -${diffDur}h (Tăng +$${(diffCost/1000).toFixed(1)}k)`;
    }
    if (data.mode === 2) {
      const diffDur = (data.base_duration || 0) - (data.duration || 0);
      const diffCost = (data.total_cost || 0) - (data.base_cost || 0);
      const releasedRes = data.resources && data.resources.length > 0 ? data.resources[0].quantity : 0;
      return releasedRes > 0 
        ? `Thuê ngoài: -${diffDur}h | Bớt ${releasedRes} NS (+$${(diffCost/1000).toFixed(1)}k)`
        : `Thuê ngoài: -${diffDur}h (+$${(diffCost/1000).toFixed(1)}k)`;
    }
    return null;
  };

  return (
    <div 
      className={`rounded-lg shadow-sm border-2 ${cardClass} w-52 h-20 flex items-center px-3 transition-all hover:shadow-md cursor-pointer`}
      title={`${data.wbs} - ${data.task_name}\nDuration: ${data.duration}h | Cost: $${Number(data.total_cost).toLocaleString()}${data.resources && data.resources.length > 0 ? `\nResources: ${data.resources.map((r: any) => `${r.resource_id}: ${r.quantity}`).join(', ')}` : ''}`}
    >
      <Handle type="target" position={Position.Left} className="w-1.5 h-1.5 bg-blue-600 border-none" />
      
      <div className="flex flex-col w-full min-w-0">
        <div className="flex justify-between items-center mb-0.5">
          <span className="text-[10px] font-bold text-slate-500 leading-none flex items-center gap-1">
            WBS {data.wbs} {data.is_critical && <span className="text-rose-500 animate-pulse">🔥</span>}
          </span>
          {data.mode === 1 && (
            <span className="text-[8px] font-extrabold bg-amber-500 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              TĂNG TỐC (CRASH)
            </span>
          )}
          {data.mode === 2 && (
            <span className="text-[8px] font-extrabold bg-violet-600 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              THUÊ NGOÀI
            </span>
          )}
        </div>
        <span className="text-[12px] font-bold truncate text-slate-800 leading-tight my-0.5" title={data.task_name}>
          {data.task_name || 'Unnamed Task'}
        </span>
        {getAdjustmentExplanation() && (
          <div className={`text-[8px] font-semibold leading-none mb-1 truncate ${
            data.mode === 1 ? 'text-amber-700' : 'text-violet-700'
          }`}>
            {getAdjustmentExplanation()}
          </div>
        )}
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

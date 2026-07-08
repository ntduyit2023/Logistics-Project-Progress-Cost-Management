import React from 'react';
import { Handle, Position } from 'reactflow';

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

  return (
    <div 
      className={`rounded-lg shadow-sm border-2 ${cardClass} w-52 h-16 flex items-center px-3 transition-all hover:shadow-md cursor-pointer`}
      title={`${data.wbs} - ${data.task_name}\nDuration: ${data.duration}h | Cost: $${Number(data.total_cost).toLocaleString()}${data.resources && data.resources.length > 0 ? `\nResources: ${data.resources.map((r: any) => `${r.resource_id}: ${r.quantity}`).join(', ')}` : ''}`}
    >
      <Handle type="target" position={Position.Left} className="w-1.5 h-1.5 bg-blue-600 border-none" />
      
      <div className="flex flex-col w-full min-w-0">
        <div className="flex justify-between items-center mb-0.5">
          <span className="text-[10px] font-bold text-slate-500 leading-none">
            WBS {data.wbs} {data.is_critical && '🔥'}
          </span>
          {data.mode === 1 && (
            <span className="text-[8px] font-extrabold bg-amber-500 text-white px-1 py-0.5 rounded leading-none">CRASH</span>
          )}
          {data.mode === 2 && (
            <span className="text-[8px] font-extrabold bg-violet-600 text-white px-1 py-0.5 rounded leading-none">OUTSOURCE</span>
          )}
        </div>
        <span className="text-[12px] font-bold truncate text-slate-800 leading-tight" title={data.task_name}>
          {data.task_name || 'Unnamed Task'}
        </span>
        <div className="flex justify-between items-center mt-1 text-[9px] text-slate-400 font-medium">
          <span>{data.duration}h | ${Number(data.total_cost).toLocaleString()}</span>
          {data.resources && data.resources.length > 0 && (
            <span className="font-bold text-blue-600 bg-blue-50/50 px-1 rounded border border-blue-100/60" title={data.mode === 2 ? "Công việc thuê ngoài - Giải phóng nhân sự nội bộ" : data.resources.map((r: any) => `${r.resource_id}: ${r.quantity}`).join(', ')}>
              👥 {data.mode === 2 ? 0 : data.resources[0].quantity}
            </span>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-1.5 h-1.5 bg-blue-600 border-none" />
    </div>
  );
};

export default TaskNode;

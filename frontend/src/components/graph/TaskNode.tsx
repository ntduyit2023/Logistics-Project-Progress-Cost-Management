import React from 'react';
import { Handle, Position } from 'reactflow';

const TaskNode = ({ data }: any) => {
  return (
    <div 
      className={`rounded-lg shadow-sm border-2 ${
        data.is_critical 
          ? 'bg-red-50 border-red-500 text-red-950' 
          : 'bg-white border-blue-500 text-slate-900'
      } w-48 h-14 flex items-center px-3 transition-all hover:shadow-lg cursor-pointer`}
      title={`${data.wbs} - ${data.task_name}\nDuration: ${data.duration}d | Cost: $${data.total_cost}`}
    >
      <Handle type="target" position={Position.Left} className="w-2 h-2 bg-blue-600 border-none" />
      
      <div className="flex flex-col w-full min-w-0">
        <span className="text-[11px] font-bold text-slate-600 mb-0.5 truncate leading-none">
          WBS: {data.wbs} {data.is_critical && '🔥'}
        </span>
        <span className="text-[13px] font-bold truncate leading-tight">
          {data.task_name || 'Unnamed Task'}
        </span>
      </div>

      <Handle type="source" position={Position.Right} className="w-2 h-2 bg-blue-600 border-none" />
    </div>
  );
};

export default TaskNode;

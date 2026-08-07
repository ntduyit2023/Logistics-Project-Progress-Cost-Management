import React from 'react';
import { Handle, Position } from 'reactflow';
import { Calendar, Clock, DollarSign } from 'lucide-react';

const TaskNode = ({ data }: any) => {
  const isCritical = Boolean(data.is_critical);
  const isAiOptimized = Boolean(data.is_ai_optimized);
  const mode = data.mode || 0; // 0: Standard, 1: Crashed, 2: Outsourced

  const otHours = data.overtime_hours_per_day || data.overtime_hours ? parseFloat(data.overtime_hours_per_day || data.overtime_hours) : 0;
  const otCost = data.overtime_cost || data.overtime ? parseFloat(data.overtime_cost || data.overtime) : 0;
  const durDiff = data.base_duration && data.duration && (data.base_duration > data.duration + 0.01) ? Math.round((data.base_duration - data.duration) * 10) / 10 : 0;
  
  const isCrashedTask = durDiff > 0 || otHours > 0 || otCost > 0 || (isAiOptimized && mode === 1);
  const isOutsourced = mode === 2;

  const baseEffort = parseFloat(data.base_effort_hours || data.duration || 0);
  const extraWorkers = parseInt(data.extra_workers || 0);
  const crashStrategy = data.crashing_strategy || 'Normal';
  const laborOtPremium = parseFloat(data.labor_ot_premium || 0);
  const equipOtExtra = parseFloat(data.equipment_ot_extra || 0);
  const energyOtExtra = parseFloat(data.energy_ot_extra || 0);
  const addedResCost = parseFloat(data.added_resources_cost || 0);

  // Determine border and background based on Legend categories
  let cardClass = 'bg-white border-slate-300 text-slate-900 hover:border-slate-400';
  
  if (isCritical && isCrashedTask) {
    cardClass = 'bg-amber-50/90 border-2 border-rose-500 text-slate-900 shadow-md shadow-amber-200 ring-2 ring-rose-300';
  } else if (isOutsourced) {
    cardClass = 'bg-purple-50 border-2 border-purple-500 text-purple-950 shadow-purple-100 hover:shadow-purple-200';
  } else if (isCrashedTask) {
    cardClass = 'bg-amber-50 border-2 border-amber-500 text-amber-950 shadow-amber-100 hover:shadow-amber-200';
  } else if (isCritical) {
    cardClass = 'bg-rose-50 border-2 border-rose-500 text-rose-950 shadow-rose-100 hover:shadow-rose-200';
  }

  const formatDateTimeShort = (dateStr: any) => {
    if (!dateStr) return 'TBD';
    let d = new Date(dateStr);
    
    // Fallback for old DD/MM/YYYY HH:MM format if Invalid Date
    if (isNaN(d.getTime()) && typeof dateStr === 'string' && dateStr.includes('/')) {
      const parts = dateStr.split(' ');
      const dateParts = parts[0].split('/');
      if (dateParts.length === 3) {
        // Rearrange to YYYY-MM-DD
        const timePart = parts[1] || '00:00';
        d = new Date(`${dateParts[2]}-${dateParts[1]}-${dateParts[0]}T${timePart}:00`);
      }
    }
    
    if (isNaN(d.getTime())) return 'TBD';
    
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yy = String(d.getFullYear()).slice(-2);
    const hh = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yy} ${hh}:${min}`;
  };

  const startDateStr = formatDateTimeShort(data.baseline_start);
  const endDateStr = formatDateTimeShort(data.baseline_end);

  const otBreakdown = data.ot_resource_breakdown || [];
  let otBreakdownText = '';
  if (otBreakdown.length > 0) {
    otBreakdownText = otBreakdown.map((r: any) => `    - ${r.resource_name} (${r.ot_hours}h): +$${Number(r.ot_cost).toFixed(0)}`).join('\n') + '\n';
  }

  const tooltipText = `${data.wbs} - ${data.task_name}\n` +
    `• Thời gian: ${startDateStr} ➔ ${endDateStr}\n` +
    `• Khối lượng (Effort): ${baseEffort}h (Không đổi)\n` +
    `• Thời lượng (Duration): ${data.duration}h ${durDiff > 0 ? `(Rút ngắn -${durDiff}h)` : ''}\n` +
    (crashStrategy !== 'Normal' ? `• Chiến lược: ${crashStrategy}\n` : '') +
    (laborOtPremium > 0 ? `• OT Premium (Nhân công): +$${laborOtPremium.toFixed(0)}\n${otBreakdownText}` : '') +
    (equipOtExtra > 0 ? `• Equipment tăng thêm: +$${equipOtExtra.toFixed(0)}\n` : '') +
    (energyOtExtra > 0 ? `• Energy tăng thêm: +$${energyOtExtra.toFixed(0)}\n` : '') +
    (addedResCost > 0 ? `• Thuê thêm nhân sự: +$${addedResCost.toFixed(0)}\n` : '') +
    (extraWorkers > 0 ? `• Thêm ${extraWorkers} nhân sự\n` : '') +
    `• Tổng chi phí: $${Number(data.total_cost).toLocaleString()}`;

  return (
    <div 
      className={`rounded-lg shadow-sm ${cardClass} w-60 h-22 flex items-center px-3 py-1.5 transition-all hover:shadow-md cursor-pointer relative group`}
      title={tooltipText}
    >
      <Handle type="target" position={Position.Left} className="w-1.5 h-1.5 bg-blue-600 border-none" />
      
      <div className="flex flex-col w-full min-w-0">
        <div className="flex justify-between items-center mb-0.5">
          <span className="text-[10px] font-bold text-slate-500 leading-none flex items-center gap-1">
            WBS {data.wbs} {isCritical && <span className="text-rose-500 animate-pulse">🔥</span>}
          </span>
          {isCritical && isCrashedTask && (
            <span className="text-[7.5px] font-black bg-rose-500 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm flex items-center gap-0.5">
              GĂNG • {crashStrategy === 'AddRes' ? 'THÊM THỢ' : crashStrategy === 'Hybrid' ? 'HYBRID' : 'TĂNG CA'}
            </span>
          )}
          {isCrashedTask && !isCritical && (
            <span className="text-[8px] font-extrabold bg-amber-500 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              {crashStrategy === 'AddRes' ? '➕ THÊM THỢ' : 
               crashStrategy === 'Hybrid' ? '🔥 HYBRID' : 
               '⚡ TĂNG CA (OT)'}
            </span>
          )}
          {isOutsourced && (
            <span className="text-[8px] font-extrabold bg-purple-600 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              💼 THUÊ NGOÀI
            </span>
          )}
          {isCritical && !isCrashedTask && (
            <span className="text-[8px] font-extrabold bg-rose-600 text-white px-1.5 py-0.5 rounded leading-none tracking-wide shadow-sm">
              🔥 GĂNG
            </span>
          )}
        </div>
        <span className="text-[12px] font-bold truncate text-slate-800 leading-tight my-0.5" title={data.task_name}>
          {data.task_name || 'Unnamed Task'}
        </span>

        {/* Real AI Optimization Details Badge Line */}
        {isCrashedTask && (
          <div className="flex items-center gap-1.5 text-[8.5px] font-extrabold text-amber-900 bg-amber-100/90 px-1.5 py-0.5 rounded border border-amber-200/80 my-0.5">
            <span>⚡ {crashStrategy !== 'Normal' ? `Chiến lược: ${crashStrategy}` : 'Tối ưu AI'}</span>
            {durDiff > 0 && <span>| Giảm {durDiff}h</span>}
            {otHours > 0 && <span>| OT {otHours}h/ngày</span>}
            {extraWorkers > 0 && <span>+{extraWorkers} thợ</span>}
            {(laborOtPremium + equipOtExtra + energyOtExtra + addedResCost) > 0 && (
              <span>• +${(laborOtPremium + equipOtExtra + energyOtExtra + addedResCost).toFixed(0)}</span>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mt-0.5 text-[9px] text-slate-400 font-medium border-t border-slate-100 pt-1">
          <div className="flex items-center gap-0.5 text-[8px]" title={`Start: ${startDateStr}\nEnd: ${endDateStr}`}>
            <Calendar size={10} className="text-slate-400 shrink-0" />
            <span className="truncate max-w-[130px]">
              {startDateStr}➔{endDateStr}
            </span>
          </div>
          <div className="flex items-center gap-0.5" title="Duration">
            <Clock size={10} className="text-slate-400" />
            <span className={durDiff > 0 ? "font-bold text-emerald-600" : ""}>{data.duration}h</span>
          </div>
          <div className="flex items-center gap-0.5" title="Cost">
            <DollarSign size={10} className="text-slate-400" />
            <span>{(Number(data.total_cost)/1000).toFixed(1)}k</span>
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-1.5 h-1.5 bg-blue-600 border-none" />
    </div>
  );
};

export default React.memo(TaskNode);

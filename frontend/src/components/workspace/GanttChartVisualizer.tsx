import React from 'react';

interface GanttChartVisualizerProps {
  ganttData: any[];
  maxEndHour: number;
}

const GanttChartVisualizer: React.FC<GanttChartVisualizerProps> = ({ ganttData, maxEndHour }) => {
  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm mt-6">
      <div className="mb-4 shrink-0">
        <h3 className="text-sm font-bold text-slate-800">Biểu đồ Gantt Phân bổ (Gantt Allocation)</h3>
        <p className="text-xs text-slate-500">Tiến độ chi tiết từng công việc sau tối ưu (Dựa trên Pydantic Model)</p>
      </div>
      <div className="overflow-x-auto relative w-full border border-slate-100 rounded-lg bg-slate-50 p-4">
        <div className="min-w-[800px] relative" style={{ height: `${ganttData.length * 40 + 40}px` }}>
          {/* Time scale */}
          <div className="absolute top-0 left-0 right-0 h-6 border-b border-slate-200 flex text-[10px] text-slate-400">
            {[...Array(11)].map((_, i) => (
              <div key={i} className="flex-1 border-l border-slate-200/50 pl-1">
                {Math.round((maxEndHour / 10) * i)}h
              </div>
            ))}
          </div>
          {/* Render Bars */}
          <div className="mt-8">
            {ganttData.map((task: any) => {
              const leftPercent = maxEndHour ? (task.start / maxEndHour) * 100 : 0;
              const widthPercent = maxEndHour ? (task.duration / maxEndHour) * 100 : 0;
              return (
                <div key={task.id} className={`relative h-8 mb-2 flex items-center group ${task.isOptimized ? 'bg-amber-50/60 rounded-lg border-l-4 border-l-amber-500' : ''}`}>
                  <div className={`w-32 shrink-0 text-xs truncate pr-2 font-medium ${task.isOptimized ? 'text-amber-800 font-bold' : 'text-slate-600'}`} title={task.name}>
                    {task.isOptimized && <span className="mr-0.5">⚡</span>}{task.name}
                  </div>
                  <div className="flex-1 relative h-full bg-slate-200/50 rounded-md">
                    <div
                      className={`absolute top-1 bottom-1 rounded shadow-sm flex items-center justify-center text-[10px] font-bold overflow-hidden cursor-pointer transition-all hover:brightness-110 ${
                        task.isOptimized
                          ? 'bg-amber-500 text-white ring-1 ring-amber-400'
                          : task.isCritical
                            ? 'bg-rose-500 text-white'
                            : 'bg-blue-500 text-white'
                      }`}
                      style={{ left: `${leftPercent}%`, width: `${Math.max(widthPercent, 1)}%` }}
                    >
                      {widthPercent > 5 && <span className="text-[10px] truncate">{task.duration.toFixed(1)}h</span>}
                    </div>
                  </div>

                  {/* Enhanced Tooltip with AI Optimization Details */}
                  <div className="absolute left-32 top-full mt-1 bg-slate-800 text-white text-xs px-3 py-2 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                    <strong className="text-sm">{task.name}</strong>
                    {task.isOptimized && <span className="ml-2 text-amber-300 font-bold">⚡ AI Optimized</span>}<br />
                    
                    <div className="mt-1 border-t border-slate-600 pt-1">
                      <span className="text-slate-300">Start:</span> {task.start.toFixed(1)}h | <span className="text-slate-300">End:</span> {task.end.toFixed(1)}h
                    </div>

                    {task.optimizedDetail && (
                      <div className="mt-1 border-t border-slate-600 pt-1 space-y-0.5">
                        <div className="text-indigo-300">
                          Baseline: {task.optimizedDetail.old_duration}h ➔ <span className="font-bold text-white">{task.optimizedDetail.new_duration}h</span>
                        </div>
                        {task.optimizedDetail.crashing_strategy && (
                          <div className="text-amber-300">
                            ⚙️ Strategy: {task.optimizedDetail.crashing_strategy}
                          </div>
                        )}
                        {task.optimizedDetail.extra_workers > 0 && (
                          <div className="text-emerald-300">
                            👥 Extra Workers: +{task.optimizedDetail.extra_workers}
                          </div>
                        )}
                        {task.optimizedDetail.base_effort_hours && (
                          <div className="text-slate-300">
                            ⏱️ Base Effort: {task.optimizedDetail.base_effort_hours}h
                          </div>
                        )}
                        {task.optimizedDetail.overtime_hours_per_day > 0 && (
                          <div className="text-rose-300">
                            🔥 OT: +{task.optimizedDetail.overtime_hours_per_day}h/ngày
                          </div>
                        )}
                        {task.optimizedDetail.overtime_cost > 0 && (
                          <div className="text-rose-400">
                            💰 Chi phí OT: ${task.optimizedDetail.overtime_cost.toFixed(0)}
                          </div>
                        )}
                        {task.optimizedDetail.added_resources_cost > 0 && (
                          <div className="text-rose-400">
                            💵 Chi phí Thuê thêm: ${task.optimizedDetail.added_resources_cost.toFixed(0)}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GanttChartVisualizer;

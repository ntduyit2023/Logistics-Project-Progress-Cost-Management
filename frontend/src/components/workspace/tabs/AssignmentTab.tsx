import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';
import AirflowGraph from '../../../pages/AirflowGraph'; // We will move this later if needed

export const AssignmentTab = ({ 
  tasks, 
  dependencies, 
  projectData, 
  projectId, 
  optionLabel, 
  selectedOptionModes, 
  currentOption, 
  criticalityIndices,
  ganttData,
  maxEndHour,
  api,
  setEditingTask,
  setIsTaskModalOpen
}: any) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Lọc task cho biểu đồ Gantt
  const filteredGantt = ganttData.filter((t: any) => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    t.task_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Tìm kiếm công việc (Tên, Mã WBS)..." 
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-semibold transition">
            <Filter size={16} /> Lọc trạng thái
          </button>
        </div>
      </div>

      {/* Airflow Graph */}
      <div className="w-full h-[500px] bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col relative overflow-hidden">
        <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex justify-between items-center z-10 shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-700">Project Network Graph (Digital Twin DAG)</span>
            <span className="text-[10px] bg-blue-100 text-blue-700 font-extrabold px-2 py-0.5 rounded uppercase">
              {optionLabel}
            </span>
          </div>
        </div>
        <div className="flex-1 relative min-h-0">
          <div className="absolute inset-0">
            <AirflowGraph
              projectId={projectData?.project_name}
              tasks={tasks}
              dependencies={dependencies}
              selectedOptionModes={selectedOptionModes}
              selectedGlpoData={currentOption?.tasks_schedule || currentOption?.tasks || {}}
              criticalityIndices={criticalityIndices}
              appliedTaskIds={projectData?.metadata_json?.applied_task_ids || []}
              appliedTaskDetails={projectData?.metadata_json?.applied_task_details || {}}
              searchHighlight={searchTerm}
              onConnectEdge={async (source: string, target: string) => {
                try {
                  if (!projectId) return;
                  await api.createLogicConstraint(projectId, {
                    predecessor_id: source,
                    successor_id: target,
                    dependency_type: "FS"
                  });
                  window.location.reload();
                } catch (err: any) {
                  alert("Failed to connect nodes: " + err.message);
                }
              }}
              onDeleteTask={async (taskId: string) => {
                try {
                  if (!projectId) return;
                  await api.deleteTask(projectId, taskId);
                  window.location.reload();
                } catch (err: any) {
                  alert("Failed to delete task: " + err.message);
                }
              }}
              onEditTask={(task: any) => {
                setEditingTask(task);
                setIsTaskModalOpen(true);
              }}
            />
          </div>
        </div>
      </div>

      {/* Gantt Chart Section */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="mb-4 shrink-0 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-slate-800">Project Gantt Chart</h3>
            <p className="text-xs text-slate-500">Tiến độ thời gian thực hiện công việc</p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-600 px-3 py-1 rounded-full font-bold">
            Hiển thị {filteredGantt.length} công việc
          </span>
        </div>
        <div className="overflow-x-auto relative w-full border border-slate-100 rounded-lg bg-slate-50 p-4">
          <div className="min-w-[800px] relative" style={{ height: `${Math.max(200, filteredGantt.length * 40 + 40)}px` }}>
            {/* X-axis ticks */}
            <div className="absolute top-0 left-0 right-0 h-6 border-b border-slate-200 flex text-[10px] text-slate-400">
              {[0, 0.25, 0.5, 0.75, 1].map(ratio => (
                <div key={ratio} className="absolute border-l border-slate-200 pl-1 h-full" style={{ left: `${ratio * 100}%` }}>
                  {(maxEndHour * ratio).toFixed(0)}h
                </div>
              ))}
            </div>

            {/* Render Bars */}
            <div className="mt-8">
              {filteredGantt.map((task: any) => {
                const leftPercent = maxEndHour ? (task.start / maxEndHour) * 100 : 0;
                const widthPercent = maxEndHour ? (task.duration / maxEndHour) * 100 : 0;
                return (
                  <div key={task.id} className={`relative h-8 mb-2 flex items-center group ${task.isOptimized ? 'bg-amber-50/60 rounded-lg border-l-4 border-l-amber-500' : ''}`}>
                    <div className={`w-48 shrink-0 text-xs truncate pr-2 font-medium ${task.isOptimized ? 'text-amber-800 font-bold' : 'text-slate-600'}`} title={task.name}>
                      {task.isOptimized && <span className="mr-0.5">⚡</span>}{task.name}
                    </div>
                    <div className="flex-1 relative h-full bg-slate-200/50 rounded-md">
                      <div
                        className={`absolute top-1 bottom-1 rounded-md shadow-sm transition-all duration-300 flex items-center px-2 overflow-hidden ${
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

                    {/* Tooltip */}
                    <div className="absolute left-48 top-full mt-1 bg-slate-800 text-white text-xs px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                      <strong>{task.name}</strong>{task.isOptimized && <span className="ml-1 text-amber-300 font-bold">⚡ AI Optimized</span>}<br />
                      Start: {task.start.toFixed(1)}h | End: {task.end.toFixed(1)}h
                      {task.optimizedDetail && (
                        <><br />Baseline: {task.optimizedDetail.old_duration}h → {task.optimizedDetail.new_duration}h
                        {task.optimizedDetail.overtime_hours_per_day > 0 && <> | OT: +{task.optimizedDetail.overtime_hours_per_day}h/ngày</>}
                        {task.optimizedDetail.overtime_cost > 0 && <> | Chi phí OT: ${task.optimizedDetail.overtime_cost.toFixed(0)}</>}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

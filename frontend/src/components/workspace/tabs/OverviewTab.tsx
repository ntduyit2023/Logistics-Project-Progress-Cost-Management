import React from 'react';
import { Layers, GitCommit, Clock, Activity } from 'lucide-react';
import GanttChartVisualizer from '../GanttChartVisualizer';

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center transition-all hover:shadow-md">
    <div className={`p-3 rounded-lg mr-4 ${color}`}>
      <Icon size={20} className="text-white" />
    </div>
    <div>
      <p className="text-xs font-semibold text-slate-400 mb-0.5 uppercase tracking-wider">{title}</p>
      <h3 className="text-xl font-black text-slate-800">{value}</h3>
    </div>
  </div>
);

export const OverviewTab = ({ tasks, dependencies, displayMakespan, displayCost, projectData, ganttData, maxEndHour }: any) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Số lượng Công việc" value={`${tasks?.length || 0} công việc`} icon={Layers} color="bg-blue-500" />
        <StatCard title="Ràng buộc Phụ thuộc" value={`${dependencies?.length || 0} liên kết`} icon={GitCommit} color="bg-emerald-500" />
        <StatCard title="Thời gian Hoàn thành (Makespan)" value={`${(displayMakespan || 0).toFixed(0)}h`} icon={Clock} color="bg-amber-500" />
        <StatCard title="Tổng Chi phí Dự án (TGC)" value={`$${((displayCost || 0) / 1000).toFixed(1)}k`} icon={Activity} color="bg-purple-500" />
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mt-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">Thông tin Dự án</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
          <div>
            <p className="text-slate-500 font-semibold mb-1">Tên Dự án</p>
            <p className="font-bold text-slate-800">{projectData?.project_name || "N/A"}</p>
          </div>
          <div>
            <p className="text-slate-500 font-semibold mb-1">Mã Dự án</p>
            <p className="font-bold text-slate-800">{projectData?.id || "N/A"}</p>
          </div>
          <div>
            <p className="text-slate-500 font-semibold mb-1">Loại</p>
            <p className="font-bold text-slate-800">{projectData?.type || "Standard"}</p>
          </div>
          <div>
            <p className="text-slate-500 font-semibold mb-1">Trạng thái</p>
            <p className="font-bold text-slate-800">
              <span className={`px-2 py-1 rounded-md text-xs ${projectData?.status === 'Simulating' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                {projectData?.status || "Ready"}
              </span>
            </p>
          </div>
        </div>
      </div>

      {ganttData && ganttData.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mt-6 overflow-x-auto">
          <GanttChartVisualizer ganttData={ganttData} maxEndHour={maxEndHour} />
        </div>
      )}
    </div>
  );
};

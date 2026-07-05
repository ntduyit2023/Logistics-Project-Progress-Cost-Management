import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Folder, Trash2, Edit2, Activity, Layers } from 'lucide-react';
import { api } from '../services/api';
import ProjectFormModal from '../components/ProjectFormModal';

export default function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<any | null>(null);

  const navigate = useNavigate();

  const fetchProjects = useCallback(async (query: string = '') => {
    try {
      setIsLoading(true);
      const res = await api.getProjects({ q: query });
      setProjects(res.data?.items || []);
    } catch (err) {
      console.error('Failed to fetch projects', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProjects(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, fetchProjects]);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project? All tasks and constraints will be lost.')) return;
    try {
      await api.deleteProject(id);
      fetchProjects(searchQuery);
    } catch (err) {
      alert('Failed to delete project');
    }
  };

  const handleEdit = (e: React.MouseEvent, project: any) => {
    e.stopPropagation();
    setEditingProject(project);
    setIsModalOpen(true);
  };

  const handleSaveProject = async (data: { project_name: string; status: string }) => {
    try {
      if (editingProject) {
        await api.updateProject(editingProject.id, data);
      } else {
        await api.createProject(data);
      }
      setIsModalOpen(false);
      fetchProjects(searchQuery);
    } catch (err: any) {
      alert('Failed to save project: ' + err.message);
    }
  };

  const openProjectModal = () => {
    setEditingProject(null);
    setIsModalOpen(true);
  };

  const openWorkspace = (id: number) => {
    navigate(`/projects/${id}/workspace`);
  };

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50/50">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-black text-slate-800 tracking-tight flex items-center">
            <Folder className="mr-3 text-violet-600" size={32} />
            Projects
          </h1>
          <p className="text-slate-500 mt-2 font-medium">Manage your construction projects and schedules</p>
        </div>
        
        <div className="flex gap-4 items-center">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-violet-500 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Search projects..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all shadow-sm"
            />
          </div>
          <button 
            onClick={openProjectModal}
            className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm shadow-violet-200 transition-all flex items-center"
          >
            <Plus size={18} className="mr-1" /> New Project
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div>
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
            <Folder size={48} className="mb-4 opacity-50" />
            <p className="text-lg font-medium">No projects found</p>
            {searchQuery && <p className="text-sm mt-1">Try adjusting your search query</p>}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-6">
            {projects.map((p) => (
              <div 
                key={p.id} 
                onClick={() => openWorkspace(p.id)}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-violet-300 transition-all cursor-pointer group flex flex-col"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-slate-800 line-clamp-1 group-hover:text-violet-700 transition-colors">
                    {p.project_name}
                  </h3>
                  <div className="flex gap-1 transition-opacity">
                    <button 
                      onClick={(e) => handleEdit(e, p)}
                      className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                      title="Edit"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      onClick={(e) => handleDelete(e, p.id)}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-6">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                    p.status === 'Execution' ? 'bg-emerald-100 text-emerald-700' :
                    p.status === 'Planning' ? 'bg-amber-100 text-amber-700' :
                    p.status === 'Completed' ? 'bg-blue-100 text-blue-700' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {p.status || 'Planning'}
                  </span>
                </div>

                <div className="mt-auto grid grid-cols-2 gap-4 border-t border-slate-100 pt-4">
                  <div className="flex items-center text-slate-500">
                    <Layers size={16} className="mr-2 text-slate-400" />
                    <span className="text-sm font-semibold">{p.num_tasks || 0} Tasks</span>
                  </div>
                  <div className="flex items-center text-slate-500">
                    <Activity size={16} className="mr-2 text-slate-400" />
                    <span className="text-sm font-semibold">{p.num_edges || 0} Edges</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ProjectFormModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSubmit={handleSaveProject} 
        initialData={editingProject} 
      />
    </div>
  );
}

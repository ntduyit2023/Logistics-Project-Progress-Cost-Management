import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Folder, Trash2, Edit2, Activity, Layers, DollarSign, Zap } from 'lucide-react';
import { api } from '../services/api';
import ProjectFormModal from '../components/ProjectFormModal';
import ProjectCard from '../components/ProjectCard';

export default function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<any | null>(null);

  const navigate = useNavigate();

  const fetchProjects = useCallback(async (query: string = '', status: string = '', type: string = '') => {
    try {
      setIsLoading(true);
      const res = await api.getProjects({ q: query, status: status || undefined, projectType: type || undefined });
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
      fetchProjects(searchQuery, filterStatus, filterType);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, filterStatus, filterType, fetchProjects]);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this project? All tasks and constraints will be lost.')) return;
    try {
      await api.deleteProject(id);
      fetchProjects(searchQuery, filterStatus, filterType);
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
      fetchProjects(searchQuery, filterStatus, filterType);
    } catch (err) {
      alert('Failed to save project');
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
          <select 
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="py-2 px-3 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all shadow-sm"
          >
            <option value="">All Statuses</option>
            <option value="Planning">Planning</option>
            <option value="Execution">Execution</option>
            <option value="Completed">Completed</option>
            <option value="On Hold">On Hold</option>
          </select>
          <select 
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="py-2 px-3 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all shadow-sm"
          >
            <option value="">All Types</option>
            <option value="ITLG">IT & Logistics (ITLG)</option>
            <option value="CON">Civil Construction (CON)</option>
            <option value="PRO">Professional Services (PRO)</option>
          </select>
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
              <ProjectCard 
                key={p.id}
                project={p}
                onClick={openWorkspace}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
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

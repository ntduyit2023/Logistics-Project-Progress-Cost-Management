import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Folder, Trash2, Edit2, Activity, Layers, DollarSign, Zap } from 'lucide-react';
import { api } from '../services/api';
import ProjectFormModal from '../components/ProjectFormModal';
import ProjectCard from '../components/ProjectCard';

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
    } catch (err) {
      alert('Failed to save project');
    }
  };

  const handleRunAI = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      // Create a temporary state for loading on the specific project button
      // For simplicity, we just use global loading here, but you can refine it
      setIsLoading(true);
      await api.runAISimulation(id);
      fetchProjects(searchQuery); // Refresh to get the new costs
    } catch (err) {
      alert('Failed to run AI Simulation');
      setIsLoading(false);
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
              <ProjectCard 
                key={p.id}
                project={p}
                onClick={openWorkspace}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onRunAI={handleRunAI}
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

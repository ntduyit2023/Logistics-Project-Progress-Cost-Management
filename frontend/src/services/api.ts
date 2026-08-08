const API_BASE_URL = `http://${window.location.hostname}:8000/api/v1`;

export const api = {
  // --- PROJECTS ---
  async getProjects(params?: { q?: string; status?: string; projectType?: string }) {
    let url = `${API_BASE_URL}/projects`;
    const searchParams = new URLSearchParams();
    if (params?.q) searchParams.append('q', params.q);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.projectType) searchParams.append('project_type', params.projectType);
    
    if (searchParams.toString()) {
      url += `?${searchParams.toString()}`;
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(id: number | string) {
    const res = await fetch(`${API_BASE_URL}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project detail');
    return res.json();
  },

  async createProject(data: { id?: string; project_name: string; status?: string; metadata_json?: any }) {
    const res = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to create project: ${text}`);
    }
    return res.json();
  },

  async updateProject(id: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to update project: ${text}`);
    }
    return res.json();
  },

  async deleteProject(id: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete project');
    return res.json();
  },

  // --- AI SIMULATION ---
  async runAISimulation(projectId: number | string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/run-simulation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to run AI simulation: ${text}`);
    }
    return res.json();
  },

  // --- GLPO AI + OR + MC-CPM OPTIMIZATION ---
  async runGLPOOptimization(projectCode: string, params?: { 
    mc_iterations?: number; 
    pareto_count?: number; 
    overtime_multiplier?: number;
    penalty_per_day?: number;
    bonus_per_day?: number;
    target_deadline?: string;
    pareto_sort?: string;
  }) {
    const url = new URL(`${API_BASE_URL}/ai/${projectCode}/glpo-optimize`);
    if (params) {
      if (params.mc_iterations !== undefined) url.searchParams.append('mc_iterations', params.mc_iterations.toString());
      if (params.pareto_count !== undefined) url.searchParams.append('pareto_count', params.pareto_count.toString());
      if (params.overtime_multiplier !== undefined) url.searchParams.append('overtime_multiplier', params.overtime_multiplier.toString());
      if (params.penalty_per_day !== undefined) url.searchParams.append('penalty_per_day', params.penalty_per_day.toString());
      if (params.bonus_per_day !== undefined) url.searchParams.append('bonus_per_day', params.bonus_per_day.toString());
      if (params.target_deadline) url.searchParams.append('target_deadline', params.target_deadline);
      if (params.pareto_sort) url.searchParams.append('pareto_sort', params.pareto_sort);
    }
    const res = await fetch(url.toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to run GLPO optimization: ${text}`);
    }
    return res.json();
  },

  async applyParetoOption(projectId: string | number, optionIndex: number, optionData: any) {
    const res = await fetch(`${API_BASE_URL}/ai/${projectId}/apply-pareto`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        option_index: optionIndex,
        option_name: optionData.option_name,
        makespan_hours: optionData.makespan_hours,
        total_cost: optionData.total_cost || optionData.cost || 0,
        tasks_schedule: optionData.tasks_schedule || optionData.tasks || {}
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to apply Pareto option: ${text}`);
    }
    return res.json();
  },

  async restoreBaseline(projectId: string | number) {
    const res = await fetch(`${API_BASE_URL}/ai/${projectId}/restore-baseline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Failed to restore baseline: ${text}`);
    }
    return res.json();
  },

  // --- TASKS ---
  async createTask(projectId: number | string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create task');
    return res.json();
  },

  async updateTask(projectId: number | string, taskId: string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update task');
    return res.json();
  },

  async deleteTask(projectId: number | string, taskId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete task');
    return res.json();
  },

  // --- TASK RESOURCES (ASSIGNMENTS) ---
  async getTaskResources(projectId: number | string, taskId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources`);
    if (!res.ok) throw new Error('Failed to fetch task resources');
    return res.json();
  },

  async assignTaskResource(projectId: number | string, taskId: string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to assign task resource');
    return res.json();
  },

  async removeTaskResource(projectId: number | string, taskId: string, resourceId: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources/${resourceId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove task resource');
    return res.json();
  },

  // --- LOGIC CONSTRAINTS (EDGES) ---
  async createLogicConstraint(projectId: number | string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/logic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create logic constraint');
    return res.json();
  },

  async deleteLogicConstraint(projectId: number | string, predecessorId: string, successorId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/logic/${predecessorId}/${successorId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete logic constraint');
    return res.json();
  },

  // --- TIME CONSTRAINTS ---
  async createTimeConstraint(projectId: number | string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/time`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to create time constraint: ${text}`);
    }
    return res.json();
  },

  async updateTimeConstraint(projectId: number | string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/time`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to update time constraint: ${text}`);
    }
    return res.json();
  },

  // --- RESOURCE CONSTRAINTS ---
  async getResourceConstraints(projectId: number | string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources`);
    if (!res.ok) throw new Error('Failed to fetch resource constraints');
    return res.json();
  },

  async createResourceConstraint(projectId: number | string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create resource constraint');
    return res.json();
  },

  async updateResourceConstraint(projectId: number | string, resourceId: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources/${resourceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update resource constraint');
    return res.json();
  },

  async deleteResourceConstraint(projectId: number | string, resourceId: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources/${resourceId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete resource constraint');
    return res.json();
  }
};

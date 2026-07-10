const API_BASE_URL = `http://${window.location.hostname}:8000/api/v1`;

export const api = {
  // --- PROJECTS ---
  async getProjects(params?: { q?: string; skip?: number; limit?: number }) {
    const url = new URL(`${API_BASE_URL}/projects`);
    if (params) {
      if (params.q) url.searchParams.append('q', params.q);
      if (params.skip !== undefined) url.searchParams.append('skip', params.skip.toString());
      if (params.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async getProject(id: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project detail');
    return res.json();
  },

  async createProject(data: { project_name: string; status?: string; metadata_json?: any }) {
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
  async runAISimulation(projectId: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Failed to run AI simulation: ${text}`);
    }
    return res.json();
  },

  // --- TASKS ---
  async createTask(projectId: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create task');
    return res.json();
  },

  async updateTask(projectId: number, taskId: string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update task');
    return res.json();
  },

  async deleteTask(projectId: number, taskId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete task');
    return res.json();
  },

  // --- TASK RESOURCES (ASSIGNMENTS) ---
  async getTaskResources(projectId: number, taskId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources`);
    if (!res.ok) throw new Error('Failed to fetch task resources');
    return res.json();
  },

  async assignTaskResource(projectId: number, taskId: string, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to assign task resource');
    return res.json();
  },

  async removeTaskResource(projectId: number, taskId: string, resourceId: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}/resources/${resourceId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove task resource');
    return res.json();
  },

  // --- LOGIC CONSTRAINTS (EDGES) ---
  async createLogicConstraint(projectId: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/logic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create logic constraint');
    return res.json();
  },

  async deleteLogicConstraint(projectId: number, predecessorId: string, successorId: string) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/logic/${predecessorId}/${successorId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete logic constraint');
    return res.json();
  },

  // --- TIME CONSTRAINTS ---
  async createTimeConstraint(projectId: number, data: any) {
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

  async updateTimeConstraint(projectId: number, data: any) {
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
  async createResourceConstraint(projectId: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create resource constraint');
    return res.json();
  },

  async updateResourceConstraint(projectId: number, resourceId: number, data: any) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources/${resourceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update resource constraint');
    return res.json();
  },

  async deleteResourceConstraint(projectId: number, resourceId: number) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/constraints/resources/${resourceId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete resource constraint');
    return res.json();
  }
};

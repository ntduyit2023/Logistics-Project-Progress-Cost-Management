import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';

// Placeholder Pages
const TaskTable = () => <div className="glass-panel p-6 rounded-xl h-full flex items-center justify-center text-slate-500">Task Table Page (Coming Soon)</div>;

import Workspace from './pages/Workspace';
import ProjectList from './pages/ProjectList';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<ProjectList />} />
          <Route path="settings" element={<Navigate to="/" replace />} />
        </Route>
        <Route path="/projects/:projectId/workspace" element={<Workspace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

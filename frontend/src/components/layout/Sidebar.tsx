import React from 'react';
import { ListTodo, Settings, Columns } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const menuItems = [
    { name: 'Workspace', icon: <Columns size={20} />, path: '/workspace' },
    { name: 'Tasks', icon: <ListTodo size={20} />, path: '/tasks' },
    { name: 'Settings', icon: <Settings size={20} />, path: '/settings' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 h-screen flex flex-col shadow-sm">
      <div className="h-16 flex items-center px-6 border-b border-slate-200">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
          <span className="text-white font-bold text-lg">G</span>
        </div>
        <h1 className="font-bold text-xl text-slate-800 tracking-tight">GLPO AI</h1>
      </div>
      
      <div className="flex-1 py-6 px-4 space-y-1">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-2">
          Project Noordhinder
        </div>
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-blue-50 text-blue-700' 
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`
            }
          >
            <span className="mr-3">{item.icon}</span>
            {item.name}
          </NavLink>
        ))}
      </div>
      
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-medium">
            AD
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-slate-700">Admin User</p>
            <p className="text-xs text-slate-500">Project Manager</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

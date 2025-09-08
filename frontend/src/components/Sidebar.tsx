import React, { useState, useEffect } from 'react';
import { 
  Bars3Icon, 
  XMarkIcon,
  DocumentTextIcon,
  StarIcon,
  Cog6ToothIcon,
  HomeIcon
} from '@heroicons/react/24/outline';

interface SidebarProps {
  currentView: 'survey' | 'golden-examples' | 'rules' | 'surveys';
  onViewChange: (view: 'survey' | 'golden-examples' | 'rules' | 'surveys') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebar-collapsed');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const navigationItems = [
    {
      id: 'survey' as const,
      name: 'Survey Generator',
      icon: HomeIcon,
      href: null
    },
    {
      id: 'surveys' as const,
      name: 'Surveys',
      icon: DocumentTextIcon,
      href: null
    },
    {
      id: 'golden-examples' as const,
      name: 'Golden Examples',
      icon: StarIcon,
      href: null
    }
  ];

  const externalLinks = [
    {
      id: 'rules',
      name: 'Rules',
      icon: Cog6ToothIcon,
      href: '/rules'
    }
  ];

  return (
    <>
      {/* Mobile overlay */}
      {!isCollapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white border-r border-gray-300 z-50 transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-64'}
        lg:translate-x-0 ${isCollapsed ? 'lg:w-16' : 'lg:w-64'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!isCollapsed && (
            <div className="flex-1">
              <h1 className="text-lg font-bold text-gray-900 truncate">Survey Engine</h1>
              <p className="text-xs text-gray-500 truncate">AI-Powered Surveys</p>
            </div>
          )}
          
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md hover:bg-gray-100 transition-colors"
          >
            {isCollapsed ? (
              <Bars3Icon className="h-5 w-5 text-gray-600" />
            ) : (
              <XMarkIcon className="h-5 w-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {/* Internal Navigation */}
          {navigationItems.map((item) => {
            const isActive = currentView === item.id;
            const Icon = item.icon;
            
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.id === 'surveys') {
                    window.location.href = '/surveys';
                  } else {
                    onViewChange(item.id);
                  }
                }}
                className={`
                  group w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                  ${isActive 
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <Icon className={`
                  flex-shrink-0 h-5 w-5 mr-3
                  ${isActive ? 'text-blue-700' : 'text-gray-400 group-hover:text-gray-500'}
                `} />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </button>
            );
          })}

          {/* External Links */}
          {externalLinks.map((item) => {
            const Icon = item.icon;
            
            return (
              <a
                key={item.id}
                href={item.href}
                className="group flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-md transition-colors"
              >
                <Icon className="flex-shrink-0 h-5 w-5 mr-3 text-gray-400 group-hover:text-gray-500" />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </a>
            );
          })}
        </nav>

        {/* Footer */}
        {!isCollapsed && (
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="h-5 w-5 text-white" />
              </div>
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-900">AI Survey Engine</p>
                <p className="text-xs text-gray-500">v1.0.0</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

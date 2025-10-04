import React, { useState } from 'react';
import { 
  Bars3BottomLeftIcon, 
  XMarkIcon,
  DocumentTextIcon,
  StarIcon,
  Cog6ToothIcon,
  HomeIcon,
  InformationCircleIcon,
  DocumentCheckIcon
} from '@heroicons/react/24/outline';
import AIEngineInfoModal from './AIEngineInfoModal';
import { useSidebar } from '../contexts/SidebarContext';

interface SidebarProps {
  currentView: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings';
  onViewChange: (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const { isCollapsed, toggleSidebar, setCollapsed } = useSidebar();
  const [showAIInfoModal, setShowAIInfoModal] = useState(false);

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
      name: 'Reference Examples',
      icon: StarIcon,
      href: null
    }
  ];

  const externalLinks = [
    {
      id: 'rules',
      name: 'Rules',
      icon: DocumentCheckIcon,
      href: '/rules'
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: Cog6ToothIcon,
      href: '/settings'
    }
  ];

  return (
    <>
      {/* Mobile overlay */}
      {!isCollapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setCollapsed(true)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-gray-800 border-r border-gray-700 z-50 transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-64'}
        lg:translate-x-0 ${isCollapsed ? 'lg:w-16' : 'lg:w-64'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          {!isCollapsed && (
            <div className="flex-1">
              <h1 className="text-lg font-bold text-white truncate">Survey Engine</h1>
              <p className="text-xs text-gray-400 truncate">AI-Powered Surveys</p>
            </div>
          )}
          
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md hover:bg-gray-700 transition-colors group relative"
            title={isCollapsed ? "Open sidebar" : "Close sidebar"}
          >
            {isCollapsed ? (
              <Bars3BottomLeftIcon className="h-5 w-5 text-gray-300 group-hover:text-white transition-colors" />
            ) : (
              <XMarkIcon className="h-5 w-5 text-gray-300 group-hover:text-white transition-colors" />
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
                  } else if (item.id === 'golden-examples') {
                    window.location.href = '/golden-examples';
                  } else {
                    onViewChange(item.id);
                  }
                }}
                className={`
                  group w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                  ${isActive 
                    ? 'bg-yellow-500 text-white border-r-2 border-yellow-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }
                `}
              >
                <Icon className={`
                  flex-shrink-0 h-5 w-5 mr-3
                  ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'}
                `} />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </button>
            );
          })}

          {/* External Links */}
          {externalLinks.map((item) => {
            const isActive = currentView === item.id;
            const Icon = item.icon;
            
            return (
              <a
                key={item.id}
                href={item.href}
                className={`
                  group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                  ${isActive 
                    ? 'bg-yellow-500 text-white border-r-2 border-yellow-400' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }
                `}
              >
                <Icon className={`
                  flex-shrink-0 h-5 w-5 mr-3
                  ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'}
                `} />
                {!isCollapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </a>
            );
          })}
        </nav>

        {/* Footer */}
        {!isCollapsed && (
          <div className="p-4 border-t border-gray-700">
            <div 
              className="flex items-center cursor-pointer hover:bg-gray-700 rounded-lg p-2 transition-colors group relative"
              onClick={() => setShowAIInfoModal(true)}
            >
              <div className="w-8 h-8 bg-gradient-to-r from-yellow-500 to-amber-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="h-5 w-5 text-white" />
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center space-x-2">
                  <p className="text-xs font-medium text-white">AI Survey Engine</p>
                  <InformationCircleIcon className="h-4 w-4 text-yellow-400 group-hover:text-yellow-300 transition-colors" />
                </div>
                <p className="text-xs text-gray-400">v1.0.0 - Click to learn more</p>
              </div>
              {/* Animated indicator */}
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        )}
        
        {/* Collapsed footer */}
        {isCollapsed && (
          <div className="p-4 border-t border-gray-700">
            <div 
              className="w-8 h-8 bg-gradient-to-r from-yellow-500 to-amber-600 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gradient-to-r hover:from-yellow-600 hover:to-amber-700 transition-colors group relative mx-auto"
              onClick={() => setShowAIInfoModal(true)}
              title="AI Survey Engine - Click to learn more"
            >
              <DocumentTextIcon className="h-5 w-5 text-white" />
              {/* Animated indicator */}
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        )}
      </div>
      
      {/* AI Engine Info Modal */}
      <AIEngineInfoModal 
        isOpen={showAIInfoModal} 
        onClose={() => setShowAIInfoModal(false)} 
      />
    </>
  );
};

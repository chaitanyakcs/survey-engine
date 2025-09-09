import { useSidebar } from '../contexts/SidebarContext';

export const useSidebarLayout = () => {
  const { isCollapsed } = useSidebar();
  
  // Return responsive margin classes based on sidebar state
  const getMainContentClasses = () => {
    if (isCollapsed) {
      return 'lg:ml-16 xl:ml-16'; // Collapsed sidebar is 64px (w-16)
    } else {
      return 'lg:ml-64 xl:ml-64'; // Expanded sidebar is 256px (w-64)
    }
  };
  
  return {
    isCollapsed,
    mainContentClasses: getMainContentClasses()
  };
};

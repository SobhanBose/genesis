import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faChartPie,
  faDatabase,
  faRobot,
  faSyncAlt,
  faCog,
  faChevronLeft,
  faChevronRight,
  faTable
} from '@fortawesome/free-solid-svg-icons';
import { Link, useLocation } from 'react-router-dom';

// Import your logo (adjust the path as needed)
import genesisLogo from '../assets/GenesisLogo.svg';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(true);
  const location = useLocation();
  
  // Set active item based on current path
  const getActiveItem = () => {
    const path = location.pathname;
    if (path.includes('dashboard')) return 'Dashboard';
    if (path.includes('data-training')) return 'Data Training';
    if (path.includes('inference')) return 'Inference';
    if (path.includes('federated-rounds')) return 'Model Information';
    if (path.includes('settings')) return 'Settings';
    if (path.includes('dataset')) return 'DataSet Management';
    return 'Dashboard';
  };
  
  const [activeItem, setActiveItem] = useState(getActiveItem());

  const menuItems = [
    { name: 'Dashboard', icon: faChartPie, path: '/dashboard' },
    { name: 'Data Training', icon: faDatabase, path: '/data-training' },
    { name: 'Inference', icon: faRobot, path: '/inference' },
    { name: 'Model Information', icon: faSyncAlt, path: '/federated-rounds' },
    { name: 'DataSet Management', icon: faTable, path: '/dataset' },
  ];

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className={`flex flex-col justify-between h-screen bg-gradient-to-b from-[#0098B0] to-[#0A7E94] text-white transition-all duration-300 ${isOpen ? 'w-64' : 'w-20'} shadow-2xl relative overflow-hidden group`}>
      {/* Top section with logo and toggle */}
      <div className="p-4 border-b border-white/20 bg-[#0098B0]">
        <div className="flex items-center justify-between">
          <div className="flex items-center overflow-hidden">
            {isOpen ? (
              // Expanded logo - full width with proper background
              <div className="h-20 flex items-center justify-center bg-[#0098B0] p-2 rounded-lg transition-all duration-300">
                <img 
                  src={genesisLogo} 
                  alt="GENESIS Logo" 
                  className="h-22 w-auto object-contain"
                />
              </div>
            ) : (
              // Collapsed state - show minimal logo indicator
              <div className="h-20 w-10 flex items-center justify-center bg-[#0098B0] rounded-lg transition-all duration-300">
                <img 
                  src={genesisLogo} 
                  alt="GENESIS Logo" 
                  className="h-6 w-auto object-contain opacity-80"
                />
              </div>
            )}
          </div>
          {isOpen && (
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-xl bg-white/10 hover:bg-white/20 transition-all duration-200 backdrop-blur-sm flex-shrink-0 hover:scale-110"
              aria-label="Collapse sidebar"
            >
              <FontAwesomeIcon 
                icon={faChevronLeft} 
                className="h-3 w-3" 
              />
            </button>
          )}
        </div>
      </div>

      {/* Navigation links with gradient background */}
      <div className="flex-grow bg-gradient-to-b from-[#0098B0] to-[#0d748b] p-2 overflow-y-auto">
        <nav>
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.name} className="relative">
                <Link
                  to={item.path}
                  onClick={() => setActiveItem(item.name)}
                  className={`w-full flex items-center p-3 rounded-xl transition-all duration-200 group-hover:group/item ${
                    activeItem === item.name 
                      ? 'bg-white/90 text-[#0098B0] shadow-lg transform scale-[1.02]' 
                      : 'hover:bg-white/10 hover:shadow-md'
                  } ${isOpen ? 'justify-start' : 'justify-center'}`}
                >
                  <div className={`rounded-lg transition-all duration-200 ${activeItem === item.name ? 'bg-[#0098B0]/20' : 'bg-white/10 group-hover:bg-white/20'} ${isOpen ? 'w-10 h-10 flex items-center justify-center' : 'w-10 h-10 flex items-center justify-center'}`}>
                    <FontAwesomeIcon 
                      icon={item.icon} 
                      className={`h-5 w-5 ${activeItem === item.name ? 'text-[#0098B0]' : 'text-white'}`} 
                    />
                  </div>
                  {isOpen && <span className="font-medium ml-3">{item.name}</span>}
                </Link>
                
                {/* Tooltip for collapsed state */}
                {!isOpen && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 min-w-max">
                    {item.name}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Bottom settings with same gradient background */}
      <div className="bg-gradient-to-b from-[#0098B0] to-[#0d748b] border-t border-white/20 p-2">
        <div className="relative">
          <Link 
            to="/settings"
            className={`w-full flex items-center p-3 rounded-xl transition-all duration-200 ${
              activeItem === 'Settings' 
                ? 'bg-white/90 text-[#0098B0] shadow-lg transform scale-[1.02]' 
                : 'hover:bg-white/10 hover:shadow-md'
            } ${isOpen ? 'justify-start' : 'justify-center'}`}
            onClick={() => setActiveItem('Settings')}
          >
            <div className={`rounded-lg transition-all duration-200 ${activeItem === 'Settings' ? 'bg-[#0098B0]/20' : 'bg-white/10 group-hover:bg-white/20'} ${isOpen ? 'w-10 h-10 flex items-center justify-center' : 'w-10 h-10 flex items-center justify-center'}`}>
              <FontAwesomeIcon 
                icon={faCog} 
                className={`h-5 w-5 ${activeItem === 'Settings' ? 'text-[#0098B0]' : 'text-white'}`} 
              />
            </div>
            {isOpen && <span className="font-medium ml-3">Settings</span>}
          </Link>
          
          {/* Tooltip for collapsed state */}
          {!isOpen && (
            <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 min-w-max">
              Settings
            </div>
          )}
        </div>
      </div>
      
      {/* Toggle button when sidebar is closed */}
      {!isOpen && (
        <button
          onClick={toggleSidebar}
          className="absolute top-7 right-3.5 p-4 rounded-xl bg-white/10 hover:bg-white/20 transition-all duration-200 backdrop-blur-sm hover:scale-110"
          aria-label="Expand sidebar"
        >
          <FontAwesomeIcon 
            icon={faChevronRight} 
            className="h-3 w-3" 
          />
        </button>
      )}
      
      {/* Subtle animated elements for modern feel */}
      {isOpen && (
        <>
          <div className="absolute top-1/4 -left-2 w-4 h-4 rounded-full bg-white/30 animate-pulse"></div>
          <div className="absolute bottom-1/3 -left-1 w-2 h-2 rounded-full bg-white/20 animate-pulse delay-500"></div>
        </>
      )}
    </div>
  );
};

export default Sidebar;
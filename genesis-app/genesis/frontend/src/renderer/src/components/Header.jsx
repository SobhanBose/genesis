import React, { useState, useRef, useEffect } from 'react';
import { FaUserCircle, FaSignOutAlt, FaCog, FaUser, FaQuestionCircle } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

const Header = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Check authentication status on component mount
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    
    if (token && userData) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userData));
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogin = () => {
    navigate('/login');
    setDropdownOpen(false);
  };

  const handleSignup = () => {
    navigate('/signup');
    setDropdownOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    setIsAuthenticated(false);
    setUser(null);
    setDropdownOpen(false);
    navigate('/login');
  };

  const handleProfile = () => {
    navigate('/profile-setup');
    setDropdownOpen(false);
  };

  return (
    <div className="flex justify-end items-start p-4 fixed top-6 right-8 z-50">
      {/* User icon and dropdown */}
      <div className="relative" ref={dropdownRef}>
        <div 
          className="flex items-center justify-center w-12 h-12 rounded-full bg-[#0097B2] cursor-pointer transition-all duration-200 hover:bg-[#008299] hover:scale-105 shadow-lg"
          onClick={() => setDropdownOpen(!dropdownOpen)}
        >
          {isAuthenticated && user?.avatar ? (
            <img 
              src={user.avatar} 
              alt="Profile" 
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <FaUserCircle className="text-3xl text-white" />
          )}
        </div>

        {/* Dropdown menu - modern transparent design */}
        {dropdownOpen && (
          <div className="absolute right-0 mt-3 w-64 bg-white/95 backdrop-blur-sm rounded-xl shadow-2xl overflow-hidden border border-white/20">
            {isAuthenticated && user ? (
              <>
                {/* User Info Section */}
                <div className="p-4 bg-gradient-to-r from-[#0097B2]/10 to-[#0097B2]/5 border-b border-white/20">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-[#0097B2] flex items-center justify-center">
                      {user.avatar ? (
                        <img src={user.avatar} alt="Profile" className="w-10 h-10 rounded-full" />
                      ) : (
                        <FaUser className="text-white text-lg" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-[#0097B2] truncate">
                        {user.name || user.email}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{user.email}</p>
                    </div>
                  </div>
                </div>

                <div className="p-2">
                  <ul className="space-y-1">
                    <li>
                      <button
                        className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-[#0097B2]/10 group flex items-center"
                        onClick={handleProfile}
                      >
                        <FaUser className="text-[#0097B2] mr-3 group-hover:text-[#008299]" />
                        <div>
                          <div className="font-medium text-[#0097B2] group-hover:text-[#008299]">Profile</div>
                          <div className="text-xs text-gray-500 group-hover:text-[#008299]/80">Manage your account</div>
                        </div>
                      </button>
                    </li>
                    <li>
                      <button
                        className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-[#0097B2]/10 group flex items-center"
                        onClick={() => {
                          console.log('Settings clicked');
                          setDropdownOpen(false);
                        }}
                      >
                        <FaCog className="text-[#0097B2] mr-3 group-hover:text-[#008299]" />
                        <div className="font-medium text-[#0097B2] group-hover:text-[#008299]">Settings</div>
                      </button>
                    </li>
                    <li>
                      <button
                        className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-[#0097B2]/10 group flex items-center"
                        onClick={() => {
                          console.log('Help clicked');
                          setDropdownOpen(false);
                        }}
                      >
                        <FaQuestionCircle className="text-[#0097B2] mr-3 group-hover:text-[#008299]" />
                        <div className="font-medium text-[#0097B2] group-hover:text-[#008299]">Help & Support</div>
                      </button>
                    </li>
                  </ul>
                  
                  <div className="my-2 border-t border-gray-200/50"></div>
                  
                  <button
                    className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-red-500/10 group flex items-center text-red-600"
                    onClick={handleLogout}
                  >
                    <FaSignOutAlt className="mr-3" />
                    <div className="font-medium">Sign Out</div>
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="p-3 bg-gradient-to-r from-[#0097B2]/10 to-[#0097B2]/5">
                  <div className="px-3 py-1 text-xs font-semibold text-[#0097B2]">
                    ACCOUNT
                  </div>
                </div>
                <div className="p-2">
                  <ul className="space-y-1">
                    <li>
                      <button
                        className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-[#0097B2]/10 group"
                        onClick={handleLogin}
                      >
                        <div className="font-medium text-[#0097B2] group-hover:text-[#008299]">Login</div>
                        <div className="text-xs text-gray-500 group-hover:text-[#008299]/80">Access your account</div>
                      </button>
                    </li>
                    <li>
                      <button
                        className="w-full text-left px-4 py-3 text-sm rounded-lg transition-all duration-200 hover:bg-[#0097B2]/10 group"
                        onClick={handleSignup}
                      >
                        <div className="font-medium text-[#0097B2] group-hover:text-[#008299]">Sign Up</div>
                        <div className="text-xs text-gray-500 group-hover:text-[#008299]/80">Create new account</div>
                      </button>
                    </li>
                  </ul>
                </div>
              </>
            )}
            
            {/* Footer with user status */}
            <div className="p-3 bg-gray-50/50 border-t border-gray-200/30">
              <div className="flex items-center px-2 py-1">
                <div className="w-2 h-2 rounded-full bg-green-500 mr-2"></div>
                <span className="text-xs text-gray-500">
                  {isAuthenticated ? `Welcome, ${user?.name || user?.email}` : 'System status: Operational'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Header;
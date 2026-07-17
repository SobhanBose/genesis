// Header.jsx
import React, { useState, useRef, useEffect } from 'react';
import Logo from '../assets/GenesisLogo.svg';

const Header = () => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const notificationRef = useRef(null);

  // Mock notifications data
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'success',
      title: 'Training Completed',
      message: 'Round 3 training completed successfully',
      time: '2 minutes ago',
      read: false
    },
    {
      id: 2,
      type: 'warning',
      title: 'Client Disconnected',
      message: 'Client Gamma lost connection during training',
      time: '15 minutes ago',
      read: false
    },
    {
      id: 3,
      type: 'info',
      title: 'New Client Connected',
      message: 'Client Zeta has joined the training session',
      time: '1 hour ago',
      read: true
    },
    {
      id: 4,
      type: 'error',
      title: 'Model Sync Failed',
      message: 'Failed to sync model with 2 clients',
      time: '2 hours ago',
      read: true
    }
  ]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setIsNotificationsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const profileMenuItems = [
    { label: 'My Profile', href: '/profile' },
    { label: 'Settings', href: '/settings' },
    { label: 'Notifications', href: '/notifications' },
    { label: 'Help & Support', href: '/support' },
    { label: 'Logout', href: '/logout' },
  ];

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id) => {
    setNotifications(notifications.map(notification =>
      notification.id === id ? { ...notification, read: true } : notification
    ));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(notification => ({
      ...notification,
      read: true
    })));
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'warning':
        return (
          <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  return (
    <header className="bg-[#0098AF] shadow-lg border-b border-[#00869B]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo Section */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <img 
                src={Logo} 
                alt="Genesis Logo" 
                className="h-20 w-32 transition-transform hover:scale-105"
              />
            </div>
          </div>

          {/* Navigation - Hidden on mobile, visible on medium screens and up */}
          {/* <nav className="hidden md:flex items-center space-x-1">
            <a 
              href="/dashboard" 
              className="relative px-4 py-2 text-white/90 hover:text-white font-medium rounded-lg transition-all duration-200 hover:bg-white/10 group"
            >
              Dashboard
              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-3/4"></span>
            </a>
            <a 
              href="/data-training" 
              className="relative px-4 py-2 text-white font-semibold bg-white/15 rounded-lg transition-all duration-200"
            >
              Data Training
              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-3/4 h-0.5 bg-white"></span>
            </a>
            <a 
              href="/clients" 
              className="relative px-4 py-2 text-white/90 hover:text-white font-medium rounded-lg transition-all duration-200 hover:bg-white/10 group"
            >
              Clients
              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-3/4"></span>
            </a>
            <a 
              href="/settings" 
              className="relative px-4 py-2 text-white/90 hover:text-white font-medium rounded-lg transition-all duration-200 hover:bg-white/10 group"
            >
              Settings
              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-white transition-all duration-200 group-hover:w-3/4"></span>
            </a>
          </nav> */}

          {/* Mobile Menu Button */}
          {/* <div className="md:hidden flex items-center space-x-3">
            <button className="text-white p-2 hover:bg-white/10 rounded-lg transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div> */}

          {/* Profile Section */}
          {/* <div className="flex items-center space-x-4">

            <div className="relative" ref={notificationRef}>
              <button
                onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                className="relative p-2 text-white/90 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200 group"
              >
                <svg 
                  className="w-5 h-5 transform group-hover:scale-110 transition-transform duration-200" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14V11c0-3.07-1.64-5.64-4.5-6.32V4a1.5 1.5 0 10-3 0v.68C7.64 5.36 6 7.92 6 11v3c0 .386-.149.735-.395 1.01L4 17h5m6 0a3 3 0 11-6 0h6z" />
                </svg>
                
                {unreadCount > 0 && (
                  <>
                    <span className="absolute -top-1 -right-1 min-w-[18px] h-4.5 bg-gradient-to-br from-red-500 to-red-600 rounded-full border-2 border-[#0098AF] flex items-center justify-center shadow-lg px-1">
                      <span className="text-[10px] font-bold text-white">{unreadCount}</span>
                    </span>
                    <span className="absolute -top-1 -right-1 min-w-[18px] h-4.5 bg-red-500 rounded-full animate-ping opacity-40"></span>
                  </>
                )}
              </button>

              {isNotificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-200 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  
                  <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-800">Notifications</h3>
                    <div className="flex items-center gap-2">
                      {unreadCount > 0 && (
                        <button
                          onClick={markAllAsRead}
                          className="text-xs text-[#0098AF] hover:text-[#007E95] font-medium transition-colors"
                        >
                          Mark all as read
                        </button>
                      )}
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {notifications.length}
                      </span>
                    </div>
                  </div>

                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-8 text-center">
                        <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-5 5v-5zM10.24 8.56a5.97 5.97 0 01-4.66-7.5 1 1 0 00-1.14-1.14 7.97 7.97 0 00-5.38 12.86l5.38 5.38a7.97 7.97 0 0012.86-5.38 1 1 0 00-1.14-1.14 5.97 5.97 0 01-7.5-4.66z" />
                        </svg>
                        <p className="text-gray-500 text-sm">No notifications</p>
                      </div>
                    ) : (
                      <div className="py-2">
                        {notifications.map((notification) => (
                          <div
                            key={notification.id}
                            className={`px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer border-l-2 ${
                              !notification.read ? 'border-l-[#0098AF] bg-blue-50/50' : 'border-l-transparent'
                            }`}
                            onClick={() => markAsRead(notification.id)}
                          >
                            <div className="flex items-start gap-3">
                              {getNotificationIcon(notification.type)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                  <h4 className="text-sm font-semibold text-gray-800 truncate">
                                    {notification.title}
                                  </h4>
                                  {!notification.read && (
                                    <div className="w-2 h-2 bg-[#0098AF] rounded-full flex-shrink-0 mt-1.5"></div>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                  {notification.message}
                                </p>
                                <p className="text-xs text-gray-400 mt-1">
                                  {notification.time}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 rounded-b-xl">
                    <a
                      href="/notifications"
                      className="text-sm text-[#0098AF] hover:text-[#007E95] font-medium text-center block py-2 transition-colors"
                      onClick={() => setIsNotificationsOpen(false)}
                    >
                      View all notifications
                    </a>
                  </div>
                </div>
              )}
            </div>

            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-3 p-1 rounded-lg hover:bg-white/10 transition-all duration-200 group"
              >
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-semibold text-white">Admin User</p>
                  <p className="text-xs text-white/70">Administrator</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-white to-gray-100 flex items-center justify-center text-[#0098AF] font-bold shadow-inner border-2 border-white/20 group-hover:border-white/30 transition-colors">
                  AU
                </div>
                <svg 
                  className={`w-4 h-4 text-white/70 transition-transform duration-200 ${isProfileOpen ? 'rotate-180' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  
                  <div className="px-4 py-3 border-b border-gray-100">
                    <div className="flex items-center space-x-3">
                      <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[#0098AF] to-[#00B4D8] flex items-center justify-center text-white font-bold text-lg">
                        AU
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">Admin User</p>
                        <p className="text-xs text-gray-500">admin@genesis.com</p>
                      </div>
                    </div>
                  </div>

                  <div className="py-2">
                    {profileMenuItems.map((item, index) => (
                      <a
                        key={index}
                        href={item.href}
                        className="flex items-center px-4 py-2.5 text-sm text-gray-700 hover:bg-[#0098AF]/5 hover:text-[#0098AF] transition-all duration-200 group"
                        onClick={() => setIsProfileOpen(false)}
                      >
                        <span className="flex-1">{item.label}</span>
                        <svg className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </a>
                    ))}
                  </div>

                  <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 rounded-b-xl">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Version 2.1.0</span>
                      <span>© 2024 Genesis</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div> */}
        </div>

        <div className="md:hidden border-t border-[#00869B] pt-3 pb-2">
          <nav className="flex justify-around items-center">
            <a 
              href="/dashboard" 
              className="flex flex-col items-center text-white/80 hover:text-white transition-colors px-3 py-1"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span className="text-xs">Dashboard</span>
            </a>
            <a 
              href="/data-training" 
              className="flex flex-col items-center text-white font-semibold bg-white/15 rounded-lg px-3 py-1"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-xs">Training</span>
            </a>
            <a 
              href="/clients" 
              className="flex flex-col items-center text-white/80 hover:text-white transition-colors px-3 py-1"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
              <span className="text-xs">Clients</span>
            </a>
            <a 
              href="/settings" 
              className="flex flex-col items-center text-white/80 hover:text-white transition-colors px-3 py-1"
            >
              <svg className="w-5 h-5 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-xs">Settings</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
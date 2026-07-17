import React, { useState, useEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MainRouter from './router/MainRouter';

// Component to handle route-based layout
const LayoutHandler = ({ children }) => {
  const [showSidebarAndHeader, setShowSidebarAndHeader] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const path = location.pathname;
    const isAuthRoute = ['/login', '/signup', '/profile-setup'].includes(path);
    setShowSidebarAndHeader(!isAuthRoute);
  }, [location]);

  if (showSidebarAndHeader) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex flex-col flex-1">
          <Header />
          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full">
      {children}
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <LayoutHandler>
        <MainRouter />
      </LayoutHandler>
    </BrowserRouter>
  );
}

export default App;
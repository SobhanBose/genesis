import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('authToken');
  const userData = localStorage.getItem('userData');
  const profileCompleted = userData ? JSON.parse(userData).profileCompleted : false;

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to profile setup if profile is not completed
  if (!profileCompleted && window.location.pathname !== '/profile-setup') {
    return <Navigate to="/profile-setup" replace />;
  }

  return children;
};

export default ProtectedRoute;
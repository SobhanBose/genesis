import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard/Dashboard';
import DataTraining from '../pages/DataTraining/DataTraining';
import Inference from '../pages/Inference/Inference';
import FederatedRounds from '../pages/FederatedRounds/FederatedRounds';
import Login from '../pages/Auth/Login';
import Signup from '../pages/Auth/Signup';
import ProfileSetup from '../pages/Auth/ProfileSetup';
import ProtectedRoute from '../components/ProtectedRoute';
import DatasetManager from '../pages/DataSet/DataSet';

const MainRouter = () => {
  return (
    <div className="flex">
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        
        {/* Protected Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/profile-setup" element={
          <ProtectedRoute>
            <ProfileSetup />
          </ProtectedRoute>
        } />
        <Route path="/data-training" element={
          <ProtectedRoute>
            <DataTraining />
          </ProtectedRoute>
        } />
        <Route path="/inference" element={
          <ProtectedRoute>
            <Inference />
          </ProtectedRoute>
        } />
        <Route path="/federated-rounds" element={
          <ProtectedRoute>
            <FederatedRounds />
          </ProtectedRoute>
        } />
        <Route path="/dataset" element={
          <ProtectedRoute>
            <DatasetManager />
          </ProtectedRoute>
        } />
        
        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </div>
  );
};

export default MainRouter;
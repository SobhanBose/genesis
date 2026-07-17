// Enhanced LogContext.jsx
import React, { createContext, useState, useEffect } from 'react';

export const LogContext = createContext();

export const LogProvider = ({ children }) => {
  const [logs, setLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [logHistory, setLogHistory] = useState([]);

  // Enhanced mock data with realistic training logs
  useEffect(() => {
    const generateMockLogs = () => {
      const mockLogs = [
        '2024-01-15 10:30:25 - [INFO] Training round 1 initialized',
        '2024-01-15 10:31:42 - [INFO] Federated learning session started',
        '2024-01-15 10:32:15 - [INFO] Connected to 12 client nodes',
        '2024-01-15 10:33:28 - [INFO] Model distribution completed',
        '2024-01-15 10:35:42 - [INFO] Client Alpha - Training started (1.2GB dataset)',
        '2024-01-15 10:36:15 - [INFO] Client Beta - Training started (0.8GB dataset)',
        '2024-01-15 10:37:33 - [INFO] Epoch 1/100 - Global accuracy: 45.2%',
        '2024-01-15 10:39:18 - [INFO] Epoch 2/100 - Global accuracy: 58.7%',
        '2024-01-15 10:41:05 - [INFO] Epoch 3/100 - Global accuracy: 67.3%',
        '2024-01-15 10:43:22 - [INFO] Model aggregation in progress',
      ];

      const mockErrors = [
        '2024-01-15 10:31:12 - [WARN] Client Gamma - Connection timeout, retrying...',
        '2024-01-15 10:34:05 - [ERROR] Client Delta - Model synchronization failed',
        '2024-01-15 10:38:47 - [WARN] Client Epsilon - Slow response detected',
      ];

      // Store initial logs in history
      setLogHistory([{
        timestamp: new Date().toISOString(),
        logs: mockLogs,
        errors: mockErrors,
        round: 1
      }]);

      setLogs(mockLogs);
      setErrors(mockErrors);
    };

    generateMockLogs();
  }, []);

  const addLog = (log, type = 'info') => {
    const timestamp = new Date().toLocaleString();
    const formattedLog = `${timestamp} - [${type.toUpperCase()}] ${log}`;
    
    setLogs(prev => {
      const newLogs = [...prev, formattedLog];
      // Keep only last 1000 logs for performance
      return newLogs.slice(-1000);
    });
  };

  const addError = (error, severity = 'error') => {
    const timestamp = new Date().toLocaleString();
    const formattedError = `${timestamp} - [${severity.toUpperCase()}] ${error}`;
    
    setErrors(prev => {
      const newErrors = [...prev, formattedError];
      // Keep only last 500 errors for performance
      return newErrors.slice(-500);
    });
  };

  const clearLogs = () => {
    setLogs([]);
    setErrors([]);
  };

  const exportLogs = () => {
    const allLogs = [...logs, ...errors];
    const logText = allLogs.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `training-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLogStats = () => {
    return {
      totalLogs: logs.length + errors.length,
      infoLogs: logs.length,
      errorLogs: errors.length,
      lastUpdated: new Date().toISOString()
    };
  };

  return (
    <LogContext.Provider value={{
      logs,
      errors,
      logHistory,
      addLog,
      addError,
      clearLogs,
      exportLogs,
      getLogStats
    }}>
      {children}
    </LogContext.Provider>
  );
};
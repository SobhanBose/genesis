import React, { createContext, useState, useEffect } from "react";

export const LogContext = createContext();

export const LogProvider = ({ children }) => {
  const [logs, setLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [isTraining, setIsTraining] = useState(false);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const listener = (_, event) => {
      if (event.type === "log") {
        setLogs((prev) => [...prev, event.message]);
      }
      if (event.type === "error") {
        setErrors((prev) => [...prev, event.message]);
      }
      if (event.type === "training-start") {
        setIsTraining(true);
        setMetrics(null);
        setLogs([]);
        setErrors([]);
      }
      if(event.type === "training-stop"){
        setIsTraining(false);
        setMetrics(null);
      }
      if (event.type === "metrics-update") {
        setMetrics(event.data);
      }
      if (event.type === "exit") {
        setLogs((prev) => [...prev, `Process exited with code ${event.code}`]);
        setIsTraining(false);
      }
    };

    window.electron.ipcRenderer.on("training-event", listener);

    return () => {
      window.electron.ipcRenderer.removeListener("training-event", listener);
    };
  }, []);

  return (
    <LogContext.Provider value={{ logs, errors, metrics, isTraining }}>
      {children}
    </LogContext.Provider>
  );
};

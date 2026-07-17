// App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LogProvider } from './context/LogContext';
import Header from './components/Header';
import DataTraining from './pages/DataTraining';

function App() {
  return (
    <LogProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main>
            <Routes>
              <Route path="/" element={<DataTraining />} />
              <Route path="/data-training" element={<DataTraining />} />
              <Route path="/dashboard" element={<DataTraining />} />
              {/* Add other routes as needed */}
            </Routes>
          </main>
        </div>
      </Router>
    </LogProvider>
  );
}

export default App;
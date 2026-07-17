import "./assets/base.css"

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { LogProvider } from "./context/LogContext"

createRoot(document.getElementById('root')).render(
  <LogProvider>
    <App />
  </LogProvider>
)

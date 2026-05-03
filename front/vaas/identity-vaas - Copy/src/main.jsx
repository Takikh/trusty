import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../design/shared.css'
import '../../design/identity-vaas.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

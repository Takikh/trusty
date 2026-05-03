import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { UploadPage } from './pages/UploadPage'
import { ProcessingPage } from './pages/ProcessingPage'
import { QuizPage } from './pages/QuizPage'
import { InterviewPage } from './pages/InterviewPage'
import { StatusPage } from './pages/StatusPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/processing" element={<ProcessingPage />} />
        <Route path="/quiz" element={<QuizPage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

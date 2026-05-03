import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { UploadPage } from './pages/UploadPage'
import { QuizPage } from './pages/QuizPage'
import { WaitingPage } from './pages/WaitingPage'
import { InterviewPage } from './pages/InterviewPage'
import { CompletionPage } from './pages/CompletionPage'
import { NetworkErrorToast } from './components/NetworkErrorToast'

function App() {
  return (
    <BrowserRouter>
      <NetworkErrorToast />
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/quiz" element={<QuizPage />} />
        <Route path="/waiting" element={<WaitingPage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/complete" element={<CompletionPage />} />
        {/* Legacy routes redirect */}
        <Route path="/processing" element={<Navigate to="/waiting" replace />} />
        <Route path="/status" element={<Navigate to="/complete" replace />} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

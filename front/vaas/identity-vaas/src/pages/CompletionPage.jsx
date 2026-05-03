import { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { StepIndicator } from '../components/StepIndicator'
import { notifyPipelineComplete, CLIENT_PLATFORM_URL } from '../api'

export function CompletionPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'doctor@example.com'
  const notified = useRef(false)

  // Notify the backend that the pipeline is complete for this doctor
  useEffect(() => {
    if (!notified.current) {
      notified.current = true
      notifyPipelineComplete(email).catch(() => {
        // Silently handled — backend can detect completion via polling
      })
    }
  }, [email])

  const handleClose = () => {
    // Attempt to close the window; if it was opened by script it will close,
    // otherwise redirect to the client platform.
    if (window.opener || window.history.length <= 1) {
      window.close()
    } else {
      window.location.assign(`${CLIENT_PLATFORM_URL}/dashboard?email=${encodeURIComponent(email)}`)
    }
  }

  return (
    <div className="vaas-page">
      <Navbar />
      <div className="vaas-container">
        <StepIndicator current={5} />
        <div className="vaas-card vaas-text-center">

          <div className="vaas-status-icon-wrap is-success" style={{ margin: '8px auto 24px' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="5" width="18" height="14" rx="2" />
              <path d="M3 7l9 6 9-6" />
            </svg>
          </div>

          <h1 className="vaas-title" style={{ textAlign: 'center' }}>Interview Complete</h1>
          <p className="vaas-subtitle" style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto 24px' }}>
            We are finalizing your evaluation. Your final verification status will be sent to your email shortly.
          </p>

          <div className="vaas-info-row" style={{ maxWidth: 420, margin: '0 auto 24px', justifyContent: 'center' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 12l2 2 4-4" />
              <circle cx="12" cy="12" r="10" />
            </svg>
            All pipeline stages have been completed for {email}
          </div>

          <button className="vaas-button" type="button" onClick={handleClose} style={{ margin: '0 auto' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            Close Window
          </button>
        </div>
      </div>
    </div>
  )
}

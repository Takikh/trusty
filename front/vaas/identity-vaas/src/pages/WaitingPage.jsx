import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { StepIndicator } from '../components/StepIndicator'
import { EmailBanner } from '../components/EmailBanner'
import { getJobDecision } from '../api'

export function WaitingPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'doctor@example.com'
  const [statusText, setStatusText] = useState('Verifying documents...')
  const pollingRef = useRef(null)

  useEffect(() => {
    const jobId = sessionStorage.getItem('vaas_job_id')
    if (!jobId) {
      // If no job ID, we shouldn't be here, but for demo we can wait 10s then advance
      console.warn('No vaas_job_id found in sessionStorage')
    }

    const poll = async () => {
      try {
        if (!jobId) return

        const data = await getJobDecision(jobId)
        console.log('[Waiting] Poll data:', data)

        if (data.job_status === 'succeeded' || data.job_status === 'failed') {
          clearInterval(pollingRef.current)
          navigate(`/interview?email=${encodeURIComponent(email)}`)
        } else if (data.job_status === 'processing') {
          setStatusText('AI analysis in progress...')
        }
      } catch (err) {
        console.error('[Waiting] Polling error:', err)
      }
    }

    // Initial poll
    poll()

    // Setup interval
    pollingRef.current = setInterval(poll, 3000)

    // Fallback: auto-advance after 60s if backend is slow
    const fallback = setTimeout(() => {
      clearInterval(pollingRef.current)
      navigate(`/interview?email=${encodeURIComponent(email)}`)
    }, 60000)

    return () => {
      clearInterval(pollingRef.current)
      clearTimeout(fallback)
    }
  }, [navigate, email])

  return (
    <div className="vaas-page">
      <Navbar />
      <div className="vaas-container">
        <StepIndicator current={3} />
        <div className="vaas-card vaas-text-center">
          <EmailBanner email={email} />

          <div className="vaas-status-icon-wrap" style={{ margin: '12px auto 24px' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
          </div>

          <h1 className="vaas-title" style={{ textAlign: 'center' }}>Documents and Answers Received</h1>
          <p className="vaas-subtitle" style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto 16px' }}>
            Your credentials are being verified by our automated pipeline. Please wait — you will receive an email with your interview link shortly.
          </p>

          <div className="vaas-spinner" />

          <div className="vaas-info-row" style={{ maxWidth: 400, margin: '0 auto 20px', justifyContent: 'center' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            {statusText}
          </div>

          {/* Hidden dev button — triple-click to skip */}
          <button
            className="vaas-mock-btn vaas-button"
            type="button"
            onClick={() => navigate(`/interview?email=${encodeURIComponent(email)}`)}
            style={{ opacity: import.meta.env.DEV ? 1 : 0, pointerEvents: import.meta.env.DEV ? 'auto' : 'none' }}
          >
            [DEV] Skip to Interview
          </button>
        </div>
      </div>
    </div>
  )
}

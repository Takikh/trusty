import { useSearchParams } from 'react-router-dom'

export function StatusPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'

  const handleClose = () => {
    const target = `http://localhost:5173/dashboard?email=${encodeURIComponent(email)}`
    window.location.assign(target)
  }

  return (
    <div className="vaas-page">
      <div className="vaas-container">
        <div className="vaas-card">
          <div className="vaas-status-icons">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v5l3 2" />
            </svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
              <rect x="3" y="5" width="18" height="14" rx="2" />
              <path d="M4 7l8 6 8-6" />
            </svg>
          </div>

          <h1 className="vaas-title">Interview Complete</h1>
          <p className="vaas-subtitle">
            Interview Complete. We are finalizing your evaluation. Your final verification status will
            be sent to your email shortly.
          </p>

          <button className="vaas-button" type="button" onClick={handleClose}>
            Close Window
          </button>
        </div>
      </div>
    </div>
  )
}

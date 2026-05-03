import { useNavigate, useSearchParams } from 'react-router-dom'

export function ProcessingPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'

  return (
    <div className="vaas-page">
      <div className="vaas-container">
        <div className="vaas-card">
          <h1 className="vaas-title">Documents Received</h1>
          <p className="vaas-subtitle">
            Documents Received. We are currently verifying your credentials. You will receive an email
            with your interview link within 15 minutes.
          </p>

          {import.meta.env.DEV && (
            <button
              className="vaas-button vaas-mock-btn"
              type="button"
              onClick={() => navigate(`/quiz?email=${encodeURIComponent(email)}`)}
            >
              [Simulate Email Link Click]
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

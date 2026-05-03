import { useSearchParams } from 'react-router-dom'

export function IdentityHandoffPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'
  const targetUrl = `http://localhost:5174/upload?email=${encodeURIComponent(email)}`

  return (
    <div className="tele-page">
      <div className="tele-container">
        <div className="tele-auth-wrap">
          <div className="tele-card">
            <h1 className="tele-title">Action Required: Verify Your Medical Credentials</h1>
            <p className="tele-subtitle">
              We need to confirm your credentials before account activation. You will be redirected to
              our verification partner.
            </p>

            <div className="tele-handoff-actions">
              <button
                className="tele-button"
                type="button"
                onClick={() => window.location.assign(targetUrl)}
              >
                Start Verification Process
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

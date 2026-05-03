import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import * as api from '../api'

export function RegisterPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((previous) => ({ ...previous, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.register(formData)
      const email = formData.email
      navigate(`/verify-email?email=${encodeURIComponent(email)}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="tele-page">
      <div className="tele-container">
        <div className="tele-auth-wrap">
          <div className="tele-card">
            <h1 className="tele-title">Doctor Registration</h1>
            <p className="tele-subtitle">
              Create your practitioner account to access the client portal.
            </p>

            {error && (
              <div className="tele-alert tele-alert-error" id="register-error">
                {error}
              </div>
            )}

            <form className="tele-form-grid" onSubmit={handleSubmit}>
              <label className="tele-label">
                First Name
                <input
                  className="tele-input"
                  name="firstName"
                  required
                  value={formData.firstName}
                  onChange={handleChange}
                  id="register-first-name"
                />
              </label>

              <label className="tele-label">
                Last Name
                <input
                  className="tele-input"
                  name="lastName"
                  required
                  value={formData.lastName}
                  onChange={handleChange}
                  id="register-last-name"
                />
              </label>

              <label className="tele-label">
                Email Address
                <input
                  className="tele-input"
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  id="register-email"
                />
              </label>

              <label className="tele-label">
                Password
                <input
                  className="tele-input"
                  type="password"
                  name="password"
                  required
                  minLength={6}
                  value={formData.password}
                  onChange={handleChange}
                  id="register-password"
                />
              </label>

              <button
                className="tele-button"
                type="submit"
                disabled={loading}
                id="register-submit"
              >
                {loading ? 'Creating Account…' : 'Create Account'}
              </button>
            </form>

            <p className="tele-footer-link">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

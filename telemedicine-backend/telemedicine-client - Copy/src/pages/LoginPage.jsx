import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import * as api from '../api'

export function LoginPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await api.login(formData)
      api.saveAuth(res)

      // Route based on role
      if (res.user.role === 'admin') {
        navigate('/admin')
      } else {
        navigate('/dashboard')
      }
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
            <h1 className="tele-title">Welcome Back</h1>
            <p className="tele-subtitle">
              Sign in to your practitioner account.
            </p>

            {error && (
              <div className="tele-alert tele-alert-error" id="login-error">
                {error}
              </div>
            )}

            <form className="tele-form-grid" onSubmit={handleSubmit}>
              <label className="tele-label">
                Email Address
                <input
                  className="tele-input"
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  id="login-email"
                />
              </label>

              <label className="tele-label">
                Password
                <input
                  className="tele-input"
                  type="password"
                  name="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  id="login-password"
                />
              </label>

              <button
                className="tele-button"
                type="submit"
                disabled={loading}
                id="login-submit"
              >
                {loading ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <p className="tele-footer-link">
              Don&apos;t have an account?{' '}
              <Link to="/register">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

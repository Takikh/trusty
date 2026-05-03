import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api'

export function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(api.getStoredUser())
  const token = api.getToken()

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }
    // Refresh user data from backend
    api.getMe(token)
      .then((data) => {
        setUser(data)
        localStorage.setItem('user', JSON.stringify(data))
      })
      .catch(() => {
        api.clearAuth()
        navigate('/login')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleLogout = () => {
    api.clearAuth()
    navigate('/login')
  }

  if (!user) return null

  return (
    <div className="tele-dashboard">
      <aside className="tele-sidebar">
        <h2>Telemedicine Portal</h2>
        <a className="tele-nav-item active" href="#">
          Dashboard
        </a>
        <a className="tele-nav-item" href="#">
          Appointments
        </a>
        <a className="tele-nav-item" href="#">
          Patients
        </a>
        <a className="tele-nav-item" href="#">
          Settings
        </a>
        <button
          className="tele-nav-item tele-logout-btn"
          onClick={handleLogout}
        >
          Logout
        </button>
      </aside>

      <main className="tele-main">
        <div className="tele-banner">Welcome, Dr. {user.name}</div>

        <section className="tele-status-card">
          <span className="tele-check">✓</span>
          <div>
            <h3>Profile Status</h3>
            <p>
              <strong>
                Status:{' '}
                {user.admin_approved
                  ? 'Verified Practitioner'
                  : 'Pending Approval'}
              </strong>
            </p>
            <p className="tele-muted">
              {user.admin_approved
                ? 'Your identity checks are complete and your practitioner profile is now active.'
                : 'Your account is awaiting administrative approval. You will be notified once approved.'}
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}

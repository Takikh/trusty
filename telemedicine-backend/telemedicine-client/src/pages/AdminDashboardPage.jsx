import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api'

const STATUS_COLORS = {
  // Pipeline status
  pending: { bg: '#fef3c7', color: '#92400e', label: 'Pending' },
  processing_a: { bg: '#dbeafe', color: '#1e40af', label: 'Processing A' },
  processing_b: { bg: '#dbeafe', color: '#1e40af', label: 'Processing B' },
  scraping: { bg: '#e0e7ff', color: '#3730a3', label: 'Scraping' },
  ingesting: { bg: '#e0e7ff', color: '#3730a3', label: 'Ingesting' },
  ready_for_interview: { bg: '#fef9c3', color: '#854d0e', label: 'Ready for Interview' },
  interview_done: { bg: '#f3e8ff', color: '#6b21a8', label: 'Interview Done' },
  verdict_ready: { bg: '#ecfdf5', color: '#065f46', label: 'Verdict Ready' },
}

const VERDICT_COLORS = {
  VERIFIED: { bg: '#d1fae5', color: '#065f46', label: '✓ Verified' },
  NEEDS_MANUAL_REVIEW: { bg: '#fef3c7', color: '#92400e', label: '⚠ Manual Review' },
  REJECTED: { bg: '#fee2e2', color: '#991b1b', label: '✕ Rejected' },
}

function Badge({ config }) {
  if (!config) return <span className="tele-badge tele-badge-neutral">—</span>
  return (
    <span
      className="tele-badge"
      style={{ background: config.bg, color: config.color }}
    >
      {config.label}
    </span>
  )
}

export function AdminDashboardPage() {
  const navigate = useNavigate()
  const [doctors, setDoctors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const token = api.getToken()
  const user = api.getStoredUser()

  useEffect(() => {
    if (!token || user?.role !== 'admin') {
      navigate('/login')
      return
    }
    fetchDoctors()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const fetchDoctors = async () => {
    setLoading(true)
    try {
      const data = await api.getAdminDoctors(token)
      setDoctors(data)
    } catch (err) {
      if (err.status === 401 || err.status === 403) {
        api.clearAuth()
        navigate('/login')
        return
      }
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleApproval = async (doctorId, currentApproval) => {
    try {
      await api.updateDoctorApproval(token, doctorId, !currentApproval)
      await fetchDoctors()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleLogout = () => {
    api.clearAuth()
    navigate('/login')
  }

  return (
    <div className="tele-dashboard">
      <aside className="tele-sidebar">
        <h2>Admin Portal</h2>
        <a className="tele-nav-item active" href="#">
          Doctor Management
        </a>
        <button
          className="tele-nav-item tele-logout-btn"
          onClick={handleLogout}
        >
          Logout
        </button>
      </aside>

      <main className="tele-main">
        <div className="tele-banner">
          <span>Doctor Management Dashboard</span>
          <span className="tele-banner-sub">
            Review and approve registered practitioners
          </span>
        </div>

        {error && (
          <div className="tele-alert tele-alert-error">{error}</div>
        )}

        {loading ? (
          <div className="tele-loading">Loading doctors…</div>
        ) : doctors.length === 0 ? (
          <div className="tele-empty-state">
            <p>No registered doctors yet.</p>
          </div>
        ) : (
          <div className="tele-table-wrap">
            <table className="tele-table" id="admin-doctors-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Email Verified</th>
                  <th>Pipeline Status</th>
                  <th>Service Verdict</th>
                  <th>Score</th>
                  <th>Admin Approved</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((doc) => (
                  <tr key={doc.id}>
                    <td className="tele-cell-name">{doc.name}</td>
                    <td>{doc.email}</td>
                    <td>
                      {doc.email_verified ? (
                        <span className="tele-badge" style={{ background: '#d1fae5', color: '#065f46' }}>
                          ✓ Yes
                        </span>
                      ) : (
                        <span className="tele-badge" style={{ background: '#fee2e2', color: '#991b1b' }}>
                          ✕ No
                        </span>
                      )}
                    </td>
                    <td>
                      <Badge config={STATUS_COLORS[doc.pipeline_status]} />
                    </td>
                    <td>
                      <Badge config={VERDICT_COLORS[doc.verdict]} />
                    </td>
                    <td>
                      {doc.final_score != null
                        ? `${(doc.final_score * 100).toFixed(0)}%`
                        : '—'}
                    </td>
                    <td>
                      {doc.admin_approved ? (
                        <span className="tele-badge" style={{ background: '#d1fae5', color: '#065f46' }}>
                          ✓ Approved
                        </span>
                      ) : (
                        <span className="tele-badge" style={{ background: '#fef3c7', color: '#92400e' }}>
                          ⏳ Pending
                        </span>
                      )}
                    </td>
                    <td>
                      <button
                        className={`tele-action-btn ${doc.admin_approved ? 'tele-action-revoke' : 'tele-action-approve'}`}
                        onClick={() => toggleApproval(doc.id, doc.admin_approved)}
                        id={`approve-btn-${doc.id}`}
                      >
                        {doc.admin_approved ? 'Revoke' : 'Approve'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}

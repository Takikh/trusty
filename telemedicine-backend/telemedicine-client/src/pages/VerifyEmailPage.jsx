import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import * as api from '../api'

const OTP_LENGTH = 6

export function VerifyEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'
  const [digits, setDigits] = useState(Array(OTP_LENGTH).fill(''))
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleOtpChange = (index, value) => {
    if (!/^\d?$/.test(value)) {
      return
    }

    const next = [...digits]
    next[index] = value
    setDigits(next)

    if (value && index < OTP_LENGTH - 1) {
      const nextInput = document.querySelector(`input[data-otp-index="${index + 1}"]`)
      nextInput?.focus()
    }
  }

  const handleOtpKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !digits[index] && index > 0) {
      const previousInput = document.querySelector(`input[data-otp-index="${index - 1}"]`)
      previousInput?.focus()
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    const code = digits.join('')
    if (code.length !== OTP_LENGTH) {
      setError('Please enter all 6 digits.')
      setLoading(false)
      return
    }

    try {
      await api.verifyEmail({ email, code })
      navigate(`/identity-handoff?email=${encodeURIComponent(email)}`)
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
            <h1 className="tele-title">Verify Email</h1>
            <p className="tele-subtitle">Enter the 6-digit OTP sent to {email}</p>

            {error && (
              <div className="tele-alert tele-alert-error" id="verify-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="tele-otp">
                {digits.map((digit, index) => (
                  <input
                    key={index}
                    data-otp-index={index}
                    value={digit}
                    onChange={(event) => handleOtpChange(index, event.target.value)}
                    onKeyDown={(event) => handleOtpKeyDown(index, event)}
                    maxLength={1}
                    inputMode="numeric"
                    required
                  />
                ))}
              </div>
              <button
                className="tele-button"
                type="submit"
                disabled={loading}
                id="verify-submit"
              >
                {loading ? 'Verifying…' : 'Confirm Email'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

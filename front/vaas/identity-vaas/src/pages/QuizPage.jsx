import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { StepIndicator } from '../components/StepIndicator'
import { EmailBanner } from '../components/EmailBanner'

const QUESTIONS = [
  {
    id: 'clinical-role',
    label: 'Describe your primary clinical role and day-to-day responsibilities.',
    placeholder: 'e.g., I am a board-certified cardiologist specializing in…',
  },
  {
    id: 'confidential-data',
    label: 'Explain your standard procedure for handling confidential patient data.',
    placeholder: 'e.g., All patient records are stored in an encrypted EHR system…',
  },
  {
    id: 'medical-records',
    label: 'What steps do you follow to fulfill a medical record request?',
    placeholder: 'e.g., Upon receiving a request, I first verify the identity of the requester…',
  },
]

const QUIZ_SECONDS = 5 * 60

export function QuizPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'doctor@example.com'
  const [timeLeft, setTimeLeft] = useState(QUIZ_SECONDS)
  const [answers, setAnswers] = useState(['', '', ''])

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const formattedTime = useMemo(() => {
    const minutes = Math.floor(timeLeft / 60)
    const seconds = timeLeft % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }, [timeLeft])

  const allAnswered = answers.every((a) => a.trim().length > 0)
  const isLow = timeLeft <= 60

  const handleSubmit = (event) => {
    event.preventDefault()
    if (allAnswered && timeLeft > 0) {
      navigate(`/waiting?email=${encodeURIComponent(email)}`)
    }
  }

  return (
    <div className="vaas-page">
      <Navbar />
      <div className="vaas-container">
        <StepIndicator current={2} />
        <div className="vaas-card">
          <EmailBanner email={email} />
          <div className="vaas-card-header">
            <div>
              <h1 className="vaas-title">Gatekeeper Quiz</h1>
              <p className="vaas-subtitle" style={{ marginBottom: 0 }}>
                Answer each question thoroughly. Your responses will be evaluated by our AI system.
              </p>
            </div>
            <div className={`vaas-timer ${isLow ? 'is-low' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              {formattedTime}
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <form onSubmit={handleSubmit}>
              {QUESTIONS.map((q, index) => (
                <div className="vaas-quiz-q" key={q.id}>
                  <label className="vaas-drop-label" htmlFor={`quiz-${q.id}`}>
                    {index + 1}. {q.label}
                  </label>
                  <textarea
                    id={`quiz-${q.id}`}
                    className="vaas-textarea"
                    placeholder={q.placeholder}
                    value={answers[index]}
                    onChange={(event) =>
                      setAnswers((prev) => {
                        const next = [...prev]
                        next[index] = event.target.value
                        return next
                      })
                    }
                  />
                </div>
              ))}

              <button
                className="vaas-button vaas-button-full"
                type="submit"
                disabled={!allAnswered || timeLeft === 0}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
                Submit Answers &amp; Start Interview
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

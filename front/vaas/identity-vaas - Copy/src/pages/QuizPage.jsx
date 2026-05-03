import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const QUESTIONS = [
  'Describe your current clinical specialization and your primary duties.',
  'How do you protect patient privacy and confidential records in your practice?',
  'What steps do you take before prescribing treatment for a new patient case?',
]

const QUIZ_SECONDS = 5 * 60

export function QuizPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'
  const [timeLeft, setTimeLeft] = useState(QUIZ_SECONDS)
  const [answers, setAnswers] = useState(['', '', ''])

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((previous) => (previous > 0 ? previous - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const formattedTime = useMemo(() => {
    const minutes = Math.floor(timeLeft / 60)
    const seconds = timeLeft % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }, [timeLeft])

  const allAnswered = answers.every((answer) => answer.trim().length > 0)

  const handleSubmit = (event) => {
    event.preventDefault()
    if (allAnswered && timeLeft > 0) {
      navigate(`/interview?email=${encodeURIComponent(email)}`)
    }
  }

  return (
    <div className="vaas-page">
      <div className="vaas-container">
        <div className="vaas-card">
          <h1 className="vaas-title">Gatekeeper Quiz</h1>
          <div className="vaas-timer">Time Remaining: {formattedTime}</div>

          <form onSubmit={handleSubmit}>
            {QUESTIONS.map((question, index) => (
              <div className="vaas-quiz-q" key={question}>
                <label className="vaas-drop-label" htmlFor={`quiz-answer-${index}`}>
                  {index + 1}. {question}
                </label>
                <textarea
                  id={`quiz-answer-${index}`}
                  className="vaas-textarea"
                  value={answers[index]}
                  onChange={(event) =>
                    setAnswers((previous) => {
                      const next = [...previous]
                      next[index] = event.target.value
                      return next
                    })
                  }
                />
              </div>
            ))}

            <button className="vaas-button" type="submit">
              Submit Answers &amp; Start Interview
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

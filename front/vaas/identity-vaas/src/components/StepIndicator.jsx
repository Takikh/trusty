const STEPS = [
  { num: 1, label: 'Upload' },
  { num: 2, label: 'Quiz' },
  { num: 3, label: 'Review' },
  { num: 4, label: 'Interview' },
  { num: 5, label: 'Complete' },
]

export function StepIndicator({ current = 1 }) {
  return (
    <div className="vaas-steps">
      {STEPS.map((step, index) => {
        const isActive = step.num === current
        const isComplete = step.num < current

        return (
          <div key={step.num} style={{ display: 'contents' }}>
            <div
              className={`vaas-step ${isActive ? 'is-active' : ''} ${isComplete ? 'is-complete' : ''}`}
            >
              <span className="vaas-step-num">
                {isComplete ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step.num
                )}
              </span>
              <span>{step.label}</span>
            </div>
            {index < STEPS.length - 1 && (
              <div className={`vaas-step-connector ${isComplete ? 'is-done' : ''}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

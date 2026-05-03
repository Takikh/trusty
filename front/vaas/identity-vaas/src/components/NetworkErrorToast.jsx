import { useEffect, useState } from 'react'
import { onConnectionError, offConnectionError } from '../api'

/**
 * Global network error toast.
 * Renders a dismissible banner when the API is unreachable.
 * Automatically subscribes to the api.js connection-error bus.
 */
export function NetworkErrorToast() {
  const [error, setError] = useState(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    onConnectionError((err) => {
      setError(err)
      setVisible(true)
    })
    return () => offConnectionError()
  }, [])

  if (!visible || !error) return null

  return (
    <div className="vaas-network-toast" role="alert">
      <div className="vaas-network-toast-inner">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
        <div>
          <strong>Connection Error</strong>
          <span>{error.message}</span>
        </div>
        <button
          type="button"
          className="vaas-network-toast-close"
          onClick={() => setVisible(false)}
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

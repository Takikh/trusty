import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const DOT_SIZE = 14

export function InterviewPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'
  const videoRef = useRef(null)
  const videoContainerRef = useRef(null)
  const [cameraError, setCameraError] = useState('')
  const [dotPosition, setDotPosition] = useState({ top: 14, left: 14 })

  useEffect(() => {
    let localStream

    const startCamera = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError('Camera access is not available in this browser.')
        return
      }

      try {
        localStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        })
        if (videoRef.current) {
          videoRef.current.srcObject = localStream
        }
      } catch {
        setCameraError('Unable to access your webcam. Please allow camera permissions and refresh.')
      }
    }

    startCamera()

    return () => {
      if (localStream) {
        localStream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  useEffect(() => {
    const moveTrackingDot = () => {
      const container = videoContainerRef.current
      if (!container) {
        return
      }

      const { width, height } = container.getBoundingClientRect()
      const nextTop = Math.max(0, Math.random() * (height - DOT_SIZE))
      const nextLeft = Math.max(0, Math.random() * (width - DOT_SIZE))
      setDotPosition({ top: nextTop, left: nextLeft })
    }

    moveTrackingDot()
    const interval = setInterval(moveTrackingDot, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="vaas-page">
      <div className="vaas-container">
        <div className="vaas-card">
          <h1 className="vaas-title">AI Video Interview</h1>
          <p className="vaas-subtitle">Respond clearly while the camera tracks your face for verification.</p>

          <div className="vaas-video-wrap" ref={videoContainerRef}>
            {cameraError ? (
              <div className="vaas-video-fallback">{cameraError}</div>
            ) : (
              <video ref={videoRef} className="vaas-video" autoPlay playsInline muted />
            )}
            <span
              className="vaas-tracking-dot"
              style={{ top: `${dotPosition.top}px`, left: `${dotPosition.left}px` }}
            />
          </div>

          <div className="vaas-waveform" aria-hidden="true">
            {Array.from({ length: 24 }).map((_, index) => (
              <span
                key={index}
                className="vaas-wave-bar"
                style={{ animationDelay: `${index * 0.08}s` }}
              />
            ))}
          </div>

          <button
            className="vaas-button vaas-end-btn"
            type="button"
            onClick={() => navigate(`/status?email=${encodeURIComponent(email)}`)}
          >
            End Interview
          </button>
        </div>
      </div>
    </div>
  )
}

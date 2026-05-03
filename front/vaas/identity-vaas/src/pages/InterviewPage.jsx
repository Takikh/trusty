import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { StepIndicator } from '../components/StepIndicator'
import { createInterviewSession, getInterviewWSUrl } from '../api'

const DOT_SIZE = 14

export function InterviewPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'doctor@example.com'
  
  const videoRef = useRef(null)
  const canvasRef = useRef(document.createElement('canvas'))
  const videoContainerRef = useRef(null)
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const frameIntervalRef = useRef(null)

  const [cameraError, setCameraError] = useState('')
  const [dotPosition, setDotPosition] = useState({ top: 14, left: 14 })
  const [elapsed, setElapsed] = useState(0)
  const [aiStatus, setAiStatus] = useState('Initializing interview session...')
  const [aiSubStatus, setAiSubStatus] = useState('Please wait while we connect to the AI model.')

  // 1. Initialize Interview Session and WebSocket
  useEffect(() => {
    let localStream
    let isMounted = true

    const initSession = async () => {
      try {
        // A. Request camera and audio
        localStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: true
        })
        
        if (!isMounted) return
        if (videoRef.current) videoRef.current.srcObject = localStream

        // B. Create backend session
        setAiStatus('Creating secure session...')
        const session = await createInterviewSession(email)
        const wsUrl = getInterviewWSUrl(session.session_uuid)

        // C. Connect WebSocket
        setAiStatus('Connecting to AI Voice...')
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('[Interview] WS Connected')
          setAiStatus('AI is listening...')
          setAiSubStatus('Respond clearly to the prompts as they appear.')
          
          // Start capturing frames for expression analysis
          startFrameCapture()
          
          // Start capturing audio for STT
          startAudioCapture(localStream)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('[Interview] WS Message:', data)
            if (data.type === 'status') {
              setAiStatus(data.message)
            } else if (data.type === 'transcript') {
              setAiSubStatus(data.content)
            }
          } catch (e) {
            console.warn('[Interview] Non-JSON message received')
          }
        }

        ws.onclose = () => {
          console.log('[Interview] WS Disconnected')
          setAiStatus('Interview session ended.')
        }

        ws.onerror = (err) => {
          console.error('[Interview] WS Error:', err)
          setAiStatus('Connection error. Please try again.')
        }

      } catch (err) {
        console.error('[Interview] Initialization error:', err)
        setCameraError('Error: ' + (err.message || 'Check camera/audio permissions.'))
      }
    }

    const startFrameCapture = () => {
      frameIntervalRef.current = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN && videoRef.current) {
          const canvas = canvasRef.current
          const video = videoRef.current
          canvas.width = 320 // Downscale for bandwidth
          canvas.height = 240
          const ctx = canvas.getContext('2d')
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
          const base64 = canvas.toDataURL('image/jpeg', 0.5) // Lower quality for speed
          
          wsRef.current.send(JSON.stringify({
            type: 'video_frame',
            data: base64.split(',')[1] // Just the data part
          }))
        }
      }, 1000) // 1 FPS for expression analysis is sufficient
    }

    const startAudioCapture = (stream) => {
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(event.data) // Send binary audio chunk
        }
      }

      mediaRecorder.start(500) // Send every 500ms
    }

    initSession()

    return () => {
      isMounted = false
      if (localStream) localStream.getTracks().forEach(t => t.stop())
      if (wsRef.current) wsRef.current.close()
      if (frameIntervalRef.current) clearInterval(frameIntervalRef.current)
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop()
    }
  }, [email])

  // Tracking dot
  useEffect(() => {
    const moveTrackingDot = () => {
      const container = videoContainerRef.current
      if (!container) return
      const { width, height } = container.getBoundingClientRect()
      const nextTop = Math.max(20, Math.random() * (height - DOT_SIZE - 40))
      const nextLeft = Math.max(20, Math.random() * (width - DOT_SIZE - 40))
      setDotPosition({ top: nextTop, left: nextLeft })
    }
    const interval = setInterval(moveTrackingDot, 2500)
    return () => clearInterval(interval)
  }, [])

  // Elapsed timer
  useEffect(() => {
    const timer = setInterval(() => setElapsed((p) => p + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  const formattedElapsed = `${String(Math.floor(elapsed / 60)).padStart(2, '0')}:${String(elapsed % 60).padStart(2, '0')}`

  return (
    <div className="vaas-page">
      <Navbar />
      <div className="vaas-container">
        <StepIndicator current={4} />
        <div className="vaas-card">
          <h1 className="vaas-title">AI Video Interview</h1>
          <p className="vaas-subtitle">
            Look directly into the camera and respond clearly to each question. Your expressions and responses are being analyzed in real-time.
          </p>

          <div className="vaas-video-wrap" ref={videoContainerRef}>
            <div className="vaas-video-corners-extra" />
            {cameraError ? (
              <div className="vaas-video-fallback">{cameraError}</div>
            ) : (
              <video ref={videoRef} className="vaas-video" autoPlay playsInline muted />
            )}
            <span
              className="vaas-tracking-dot"
              style={{ top: `${dotPosition.top}px`, left: `${dotPosition.left}px` }}
            />
            <div className="vaas-live-badge">
              <span className="vaas-live-dot" />
              LIVE RECORDING — {formattedElapsed}
            </div>
          </div>

          <div className="vaas-ai-prompt">
            <div className="vaas-ai-prompt-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0 3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
              </svg>
            </div>
            <div>
              <div className="vaas-ai-prompt-text">{aiStatus}</div>
              <div className="vaas-ai-prompt-sub">{aiSubStatus}</div>
            </div>
          </div>

          <div className="vaas-waveform" aria-hidden="true">
            {Array.from({ length: 32 }).map((_, index) => (
              <span
                key={index}
                className="vaas-wave-bar"
                style={{ animationDelay: `${index * 0.06}s` }}
              />
            ))}
          </div>

          <button
            className="vaas-button vaas-end-btn vaas-button-full"
            type="button"
            onClick={() => navigate(`/complete?email=${encodeURIComponent(email)}`)}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V5a3 3 0 0 0-5.94-.6" />
              <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.13 1.48-.35 2.16" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
            End Interview
          </button>
        </div>
      </div>
    </div>
  )
}

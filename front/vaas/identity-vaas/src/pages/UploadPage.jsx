import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { StepIndicator } from '../components/StepIndicator'
import { EmailBanner } from '../components/EmailBanner'
import { uploadDocument } from '../api'

function DocumentDropZone({ label, file, onFileSelect, inputId }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const droppedFile = event.dataTransfer.files?.[0]
    if (droppedFile) onFileSelect(droppedFile)
  }

  const handleInput = (event) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) onFileSelect(selectedFile)
  }

  return (
    <div>
      <label className="vaas-drop-label" htmlFor={inputId}>
        {label}
      </label>
      <div
        className={`vaas-dropzone ${isDragging ? 'is-dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById(inputId)?.click()}
      >
        <input
          id={inputId}
          type="file"
          hidden
          accept="application/pdf,image/*"
          onChange={handleInput}
        />
        {file ? (
          <div className="vaas-file-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <strong>{file.name}</strong>
          </div>
        ) : (
          <div className="vaas-drop-prompt">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span>Drag and drop or click to upload</span>
            <small>PDF, JPG, PNG — Max 10MB</small>
          </div>
        )}
      </div>
    </div>
  )
}

export function UploadPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'doctor@example.com'
  
  const [files, setFiles] = useState({
    diploma: null,
    governmentId: null,
    certificate: null
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const isFormValid = files.diploma && files.governmentId && files.certificate

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!isFormValid || isSubmitting) return

    setIsSubmitting(true)
    setError('')

    try {
      const result = await uploadDocument(email, files.diploma)
      
      sessionStorage.setItem('vaas_job_id', result.job_id)
      sessionStorage.setItem('vaas_session_uuid', result.session_uuid)
      
      navigate(`/quiz?email=${encodeURIComponent(email)}`)
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.message || 'Failed to upload documents. Please try again.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="vaas-page">
      <Navbar />
      <div className="vaas-container">
        <StepIndicator current={1} />
        <div className="vaas-card">
          <EmailBanner email={email} />
          
          <h1 className="vaas-title">Granular Document Upload</h1>
          <p className="vaas-subtitle">
            Upload the required documents below to begin your identity verification process. 
            Each document will be analyzed independently.
          </p>

          {error && <div className="vaas-error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="vaas-zone-list">
              <DocumentDropZone
                label="1. Medical Diploma"
                file={files.diploma}
                inputId="medical-diploma"
                onFileSelect={(file) => setFiles(f => ({ ...f, diploma: file }))}
              />
              <DocumentDropZone
                label="2. Government ID"
                file={files.governmentId}
                inputId="government-id"
                onFileSelect={(file) => setFiles(f => ({ ...f, governmentId: file }))}
              />
              <DocumentDropZone
                label="3. Professional Certificate"
                file={files.certificate}
                inputId="professional-certificate"
                onFileSelect={(file) => setFiles(f => ({ ...f, certificate: file }))}
              />
            </div>

            <button 
              className={`vaas-button ${isSubmitting ? 'is-loading' : ''}`} 
              type="submit" 
              disabled={!isFormValid || isSubmitting}
              style={{ marginTop: 24 }}
            >
              {isSubmitting ? 'Processing Documents...' : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18 }}>
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                  Submit Documents
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

function DocumentDropZone({ label, fileName, onFileSelect, inputId }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    if (file) {
      onFileSelect(file.name)
    }
  }

  const handleInput = (event) => {
    const file = event.target.files?.[0]
    if (file) {
      onFileSelect(file.name)
    }
  }

  return (
    <div>
      <label className="vaas-drop-label" htmlFor={inputId}>
        {label}
      </label>
      <div
        className={`vaas-dropzone ${isDragging ? 'is-dragging' : ''} ${fileName ? 'has-file' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById(inputId)?.click()}
      >
        <input id={inputId} type="file" hidden onChange={handleInput} />
        {fileName ? <strong>{fileName}</strong> : <span>Drag and drop or click to upload</span>}
      </div>
    </div>
  )
}

export function UploadPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') || 'user@email.com'
  const [documents, setDocuments] = useState({
    diploma: '',
    governmentId: '',
    certificate: '',
  })

  const canSubmit = Boolean(documents.diploma && documents.governmentId && documents.certificate)

  const handleSubmit = (event) => {
    event.preventDefault()
    if (canSubmit) {
      navigate(`/processing?email=${encodeURIComponent(email)}`)
    }
  }

  return (
    <div className="vaas-page">
      <div className="vaas-container">
        <div className="vaas-card">
          <div className="vaas-email-banner">Verifying account for: {email}</div>
          <h1 className="vaas-title">Clinical Identity Verification</h1>
          <p className="vaas-subtitle">Upload the required files to start credential verification.</p>

          <form onSubmit={handleSubmit}>
            <div className="vaas-zone-list">
              <DocumentDropZone
                label="1. Medical Diploma"
                fileName={documents.diploma}
                inputId="medical-diploma"
                onFileSelect={(value) => setDocuments((previous) => ({ ...previous, diploma: value }))}
              />
              <DocumentDropZone
                label="2. Government ID"
                fileName={documents.governmentId}
                inputId="government-id"
                onFileSelect={(value) =>
                  setDocuments((previous) => ({ ...previous, governmentId: value }))
                }
              />
              <DocumentDropZone
                label="3. Professional Certificate"
                fileName={documents.certificate}
                inputId="professional-certificate"
                onFileSelect={(value) =>
                  setDocuments((previous) => ({ ...previous, certificate: value }))
                }
              />
            </div>

            <button className="vaas-button" type="submit" disabled={!canSubmit} style={{ marginTop: 16 }}>
              Submit Documents
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

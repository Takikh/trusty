export function EmailBanner({ email }) {
  return (
    <div className="vaas-email-banner">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4M12 8h.01" />
      </svg>
      Verifying account for: <strong>{email}</strong>
    </div>
  )
}

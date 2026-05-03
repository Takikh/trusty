export function Navbar() {
  return (
    <nav className="vaas-navbar">
      <div className="vaas-navbar-logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L3 7v6c0 5.25 3.75 10.15 9 11.25C17.25 23.15 21 18.25 21 13V7l-9-5z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
        <span>SecureID Verification</span>
      </div>
      <div className="vaas-navbar-label">
        Enterprise Security Portal
      </div>
    </nav>
  )
}

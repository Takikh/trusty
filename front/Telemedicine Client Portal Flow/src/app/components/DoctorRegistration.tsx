export function DoctorRegistration({ onNext }: { onNext: () => void }) {
  return (
    <div className="w-full max-w-md mx-auto px-6 py-12">
      <div className="bg-white rounded-lg shadow-sm border border-border p-8">
        <h1 className="text-center mb-8">Join as a Practitioner</h1>

        <form onSubmit={(e) => { e.preventDefault(); onNext(); }} className="space-y-6">
          <div>
            <label htmlFor="firstName" className="block mb-2 text-foreground">
              First Name
            </label>
            <input
              type="text"
              id="firstName"
              className="w-full px-4 py-3 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter your first name"
              required
            />
          </div>

          <div>
            <label htmlFor="lastName" className="block mb-2 text-foreground">
              Last Name
            </label>
            <input
              type="text"
              id="lastName"
              className="w-full px-4 py-3 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter your last name"
              required
            />
          </div>

          <div>
            <label htmlFor="email" className="block mb-2 text-foreground">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              className="w-full px-4 py-3 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block mb-2 text-foreground">
              Password
            </label>
            <input
              type="password"
              id="password"
              className="w-full px-4 py-3 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Create a password"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-primary text-primary-foreground py-3 rounded-lg hover:opacity-90 transition-opacity"
          >
            Create Account
          </button>

          <p className="text-center text-muted-foreground">
            Already have an account?{' '}
            <a href="#" className="text-primary hover:underline">
              Log in
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}

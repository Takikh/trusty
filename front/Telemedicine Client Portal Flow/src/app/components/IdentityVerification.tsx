import { Shield } from 'lucide-react';

export function IdentityVerification({ onNext }: { onNext: () => void }) {
  return (
    <div className="w-full max-w-2xl mx-auto px-6 py-12">
      <div className="bg-white rounded-lg shadow-sm border border-border p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-6">
            <Shield className="w-10 h-10 text-primary" />
          </div>
          <h2 className="text-center mb-4">Action Required: Verify Your Medical Credentials</h2>
          <p className="text-center text-foreground max-w-xl leading-relaxed">
            To protect our patients, all practitioners must undergo a secure identity and credential check through our trusted verification partner. You will be redirected to complete this process.
          </p>
        </div>

        <div className="flex justify-center">
          <button
            onClick={onNext}
            className="bg-primary text-primary-foreground px-8 py-4 rounded-lg hover:opacity-90 transition-opacity"
          >
            Start Verification Process
          </button>
        </div>
      </div>
    </div>
  );
}

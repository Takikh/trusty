import { useState } from 'react';
import { NavigationBar } from './components/NavigationBar';
import { DoctorRegistration } from './components/DoctorRegistration';
import { EmailVerification } from './components/EmailVerification';
import { IdentityVerification } from './components/IdentityVerification';
import { PractitionerDashboard } from './components/PractitionerDashboard';

export default function App() {
  const [currentFrame, setCurrentFrame] = useState(1);

  return (
    <div className="size-full flex flex-col bg-background">
      {currentFrame !== 4 && <NavigationBar />}

      <div className="flex-1 flex items-center justify-center overflow-auto">
        {currentFrame === 1 && (
          <DoctorRegistration onNext={() => setCurrentFrame(2)} />
        )}
        {currentFrame === 2 && (
          <EmailVerification onNext={() => setCurrentFrame(3)} />
        )}
        {currentFrame === 3 && (
          <IdentityVerification onNext={() => setCurrentFrame(4)} />
        )}
        {currentFrame === 4 && <PractitionerDashboard />}
      </div>
    </div>
  );
}
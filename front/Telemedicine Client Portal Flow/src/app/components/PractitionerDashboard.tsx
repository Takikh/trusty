import { Home, Calendar, Users, Settings, ShieldCheck } from 'lucide-react';

export function PractitionerDashboard() {
  return (
    <div className="flex h-full">
      <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground">TH</span>
            </div>
            <span className="text-sidebar-foreground">TeleHealth</span>
          </div>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          <a
            href="#"
            className="flex items-center gap-3 px-3 py-2 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground"
          >
            <Home className="w-5 h-5" />
            <span>Home</span>
          </a>
          <a
            href="#"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <Calendar className="w-5 h-5" />
            <span>Appointments</span>
          </a>
          <a
            href="#"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <Users className="w-5 h-5" />
            <span>Patients</span>
          </a>
          <a
            href="#"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </a>
        </nav>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="bg-primary/10 border border-primary/20 rounded-lg p-6 mb-8">
            <h1 className="text-foreground">Welcome, Dr. Smith</h1>
          </div>

          <div className="bg-white border border-border rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-6 h-6 text-emerald-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-foreground">Profile Status</h3>
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                    Status: Verified Practitioner
                  </span>
                </div>
                <p className="text-muted-foreground">
                  Your identity and medical credentials have been successfully verified. Your profile is active and you can now accept patient appointments.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

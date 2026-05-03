import { Outlet } from "react-router";
import { ShieldCheck } from "lucide-react";

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans flex flex-col">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 py-4 px-6 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-900 font-semibold text-lg">
            <ShieldCheck className="w-6 h-6 text-blue-600" />
            <span>SecureID Verification</span>
          </div>
          <div className="text-sm text-slate-500 font-medium">
            Enterprise Security Portal
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-3xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

import { useNavigate } from "react-router";
import { Clock, Mail } from "lucide-react";

export function ProcessingPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center max-w-lg mx-auto w-full min-h-[60vh] animate-in fade-in zoom-in-95 duration-500">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-50" />
        <div className="relative bg-white p-6 rounded-full border-2 border-blue-100 shadow-sm">
          <Clock className="w-16 h-16 text-blue-600" />
        </div>
      </div>
      
      <h1 className="text-3xl font-bold text-slate-900 mb-4 text-center">Documents Received</h1>
      
      <p className="text-slate-600 text-lg text-center leading-relaxed mb-10 max-w-md">
        We are currently verifying your credentials. You will receive an email with your interview link within 15 minutes.
      </p>

      {/* For prototype demonstration purposes */}
      <div className="mt-12 p-6 bg-slate-100 rounded-xl border border-slate-200 w-full flex flex-col items-center">
        <p className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-4">Prototype Action</p>
        <button
          onClick={() => navigate("/quiz")}
          className="flex items-center gap-2 px-6 py-3 bg-white hover:bg-slate-50 text-blue-700 border border-blue-200 rounded-lg font-medium transition-colors shadow-sm"
        >
          <Mail className="w-4 h-4" />
          Simulate Email Link Click
        </button>
      </div>
    </div>
  );
}

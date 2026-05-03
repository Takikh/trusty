import { Mail } from "lucide-react";
import { useNavigate } from "react-router";

export function SuccessPage() {
  const navigate = useNavigate();

  return (
    <div className="w-full max-w-lg mx-auto bg-white p-10 rounded-3xl shadow-sm border border-slate-200 flex flex-col items-center text-center animate-in fade-in zoom-in duration-500">
      <div className="w-24 h-24 bg-blue-50 rounded-full flex items-center justify-center mb-6">
        <Mail className="w-12 h-12 text-blue-500" />
      </div>
      
      <h1 className="text-3xl font-bold text-slate-900 mb-4">Interview Complete</h1>
      <p className="text-slate-600 mb-10 text-lg leading-relaxed max-w-md">
        We are finalizing your evaluation. Your final verification status will be sent to your email shortly.
      </p>

      <button
        onClick={() => navigate("/")}
        className="w-full py-4 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-semibold text-lg transition-all shadow-md hover:shadow-lg"
      >
        Close Window
      </button>
    </div>
  );
}

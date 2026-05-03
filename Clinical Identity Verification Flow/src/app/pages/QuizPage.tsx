import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Clock } from "lucide-react";

export function QuizPage() {
  const navigate = useNavigate();
  const [timeLeft, setTimeLeft] = useState(299); // 4 minutes 59 seconds
  const [answers, setAnswers] = useState<Record<number, string>>({});

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const questions = [
    {
      id: 1,
      text: "Please describe your primary clinical role and daily responsibilities in detail.",
    },
    {
      id: 2,
      text: "Explain your standard procedure for handling confidential patient data securely.",
    },
    {
      id: 3,
      text: "If a patient requests their medical records, what steps do you take to fulfill this request compliantly?",
    },
  ];

  // A question is considered answered if it has a non-empty string
  const isComplete = questions.every(
    (q) => typeof answers[q.id] === "string" && answers[q.id].trim().length > 0
  );

  const handleInput = (questionId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isComplete) {
      navigate("/interview");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden relative">
        {/* Header with Timer */}
        <div className="bg-slate-50 border-b border-slate-200 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-blue-900">Gatekeeper Quiz</h2>
            <p className="text-sm text-slate-500 mt-1">Please answer all security questions to proceed to the interview.</p>
          </div>
          <div className="flex items-center gap-2 bg-blue-100/50 text-blue-800 px-4 py-2 rounded-lg font-mono font-medium border border-blue-200">
            <Clock className="w-4 h-4 text-blue-600" />
            <span className={timeLeft < 60 ? "text-red-600" : ""}>
              {formatTime(timeLeft)}
            </span>
          </div>
        </div>

        {/* Questions */}
        <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-8">
          {questions.map((q, qIndex) => (
            <div key={q.id} className="space-y-4">
              <h3 className="text-base font-medium text-slate-800 flex gap-3">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-blue-50 text-blue-600 text-sm font-bold mt-0.5">
                  {qIndex + 1}
                </span>
                {q.text}
              </h3>
              <div className="pl-9">
                <textarea
                  className="w-full min-h-[100px] p-3 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm text-slate-700 bg-slate-50 focus:bg-white placeholder-slate-400 resize-y"
                  placeholder="Type your answer here..."
                  value={answers[q.id] || ""}
                  onChange={(e) => handleInput(q.id, e.target.value)}
                  disabled={timeLeft === 0}
                />
              </div>
            </div>
          ))}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!isComplete || timeLeft === 0}
            className={`w-full py-4 mt-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2 ${
              isComplete && timeLeft > 0
                ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg"
                : "bg-slate-200 text-slate-400 cursor-not-allowed"
            }`}
          >
            Submit Answers & Start Interview
          </button>
        </form>
      </div>
    </div>
  );
}
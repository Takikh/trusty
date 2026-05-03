import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router";
import { PhoneOff, Send, Loader2 } from "lucide-react";
import * as faceapi from "face-api.js";

interface ChatMessage {
  role: "ai" | "doctor";
  text: string;
}

export function InterviewPage() {
  const navigate = useNavigate();
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [inputEnabled, setInputEnabled] = useState(false);
  const [status, setStatus] = useState<string>("Connecting...");
  const [modelsLoaded, setModelsLoaded] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const currentTurnRef = useRef<string | null>(null); // tracks which turn we're on
  const { id } = useParams();

  // Auto-scroll chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const sendAnswer = () => {
    const text = inputText.trim();
    if (!text || !inputEnabled || wsRef.current?.readyState !== WebSocket.OPEN) return;

    setChatMessages(prev => [...prev, { role: "doctor", text }]);
    wsRef.current.send(JSON.stringify({ type: "answer", text }));
    setInputText("");
    setInputEnabled(false);
    setStatus("Processing your answer...");
  };

  // Setup WebSocket and Webcam
  useEffect(() => {
    const doctorId = id || "test_doctor";
    const websocket = new WebSocket(`ws://localhost:8001/ws/interview/${doctorId}`);
    wsRef.current = websocket;

    websocket.onopen = () => {
      setStatus("Connected. Starting Interview...");
      websocket.send("START");
    };

    websocket.onmessage = async (event) => {
      if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);

        if (msg.type === "question") {
          // Track which turn we're on based on question count
          setChatMessages(prev => {
            const turnCount = prev.filter(m => m.role === "ai").length;
            const turnId = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"][turnCount] || "t7";
            currentTurnRef.current = turnId;
            return [...prev, { role: "ai", text: msg.text }];
          });
          setStatus("AI is speaking...");
        } else if (msg.type === "status") {
          if (msg.message === "listening") {
            setInputEnabled(true);
            setStatus("Your turn — type your answer below");
          } else if (msg.message === "interview_complete") {
            currentTurnRef.current = null;
            setStatus("Interview complete. Redirecting...");
            setTimeout(() => navigate("/success"), 3000);
          } else if (msg.message !== "done_speaking" && msg.message !== "speaking") {
            setStatus(msg.message);
          }
        }
      } else {
        // Binary audio (TTS) — play it, then enable input when done
        const blob = new Blob([event.data], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        audio.onended = () => {
          setInputEnabled(true);
          setStatus("Your turn — type your answer below");
          URL.revokeObjectURL(url);
        };

        audio.play().catch(() => {
          // If audio fails, still enable input
          setInputEnabled(true);
          setStatus("Your turn — type your answer below");
        });
      }
    };

    websocket.onerror = () => setStatus("Connection Error. Is the backend running?");

    // Camera only (no mic needed)
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then(stream => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(err => console.error("Camera error:", err));

    return () => {
      websocket.close();
      if (videoRef.current?.srcObject)
        (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
    };
  }, [navigate]);

  // Load Face API Models
  useEffect(() => {
    Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri("/models"),
      faceapi.nets.faceLandmark68Net.loadFromUri("/models"),
      faceapi.nets.faceExpressionNet.loadFromUri("/models"),
    ])
      .then(() => setModelsLoaded(true))
      .catch(err => console.error("face-api load error:", err));
  }, []);

  // Face detection overlay
  useEffect(() => {
    if (!modelsLoaded) return;
    const interval = setInterval(async () => {
      if (videoRef.current && canvasRef.current && videoRef.current.readyState === 4) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const displaySize = { width: video.videoWidth, height: video.videoHeight };
        if (canvas.width !== displaySize.width || canvas.height !== displaySize.height)
          faceapi.matchDimensions(canvas, displaySize);

        const det = await faceapi
          .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
          .withFaceLandmarks()
          .withFaceExpressions();

        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          if (det) {
            const r = faceapi.resizeResults(det, displaySize);
            faceapi.draw.drawDetections(canvas, r);
            faceapi.draw.drawFaceLandmarks(canvas, r);
            faceapi.draw.drawFaceExpressions(canvas, r);

            // Send dominant emotion to backend for expression log
            const turnId = currentTurnRef.current;
            if (turnId && wsRef.current?.readyState === WebSocket.OPEN) {
              const expressions = det.expressions as Record<string, number>;
              const dominant = Object.entries(expressions).reduce(
                (best, [k, v]) => (v > best[1] ? [k, v] : best),
                ["neutral", 0]
              )[0];
              wsRef.current.send(JSON.stringify({
                type: "expression",
                turn_id: turnId,
                emotion: dominant
              }));
            }
          }
        }
      }
    }, 1000); // 1fps for expression sampling (lower bandwidth)
    return () => clearInterval(interval);
  }, [modelsLoaded]);

  return (
    <div className="w-full max-w-5xl mx-auto flex gap-6 animate-in fade-in zoom-in-95 duration-500">
      {/* Left — Video + Face detection */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-4">
        <div className="text-center">
          <h1 className="text-xl font-bold text-blue-900">AI Interview</h1>
          <p className="text-xs text-slate-500">Face verified in real-time</p>
        </div>
        <div className="relative aspect-[4/3] bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
          <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
          <canvas ref={canvasRef} className="absolute inset-0 w-full h-full object-cover z-20 pointer-events-none" />
          <div className="absolute inset-0 border border-white/10 m-4 rounded-lg pointer-events-none z-30">
            <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-emerald-400/80" />
            <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-emerald-400/80" />
            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-emerald-400/80" />
            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-emerald-400/80" />
          </div>
          <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-slate-900/80 backdrop-blur px-2 py-1 rounded-full border border-slate-700 z-30">
            <span className="text-emerald-400 text-[10px] font-mono tracking-wider">LIVE</span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>
        </div>

        {/* Status */}
        <div className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all ${
          inputEnabled
            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
            : "bg-blue-50 text-blue-600 border-blue-200"
        }`}>
          <Loader2 className={`w-3.5 h-3.5 ${inputEnabled ? "hidden" : "animate-spin"}`} />
          <span>{status}</span>
        </div>

        <button
          onClick={() => navigate("/success")}
          className="flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-semibold text-sm transition-all shadow-md"
        >
          <PhoneOff className="w-4 h-4" />
          End Interview
        </button>
      </div>

      {/* Right — Chat */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Chat header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white text-sm font-bold shadow">
            AI
          </div>
          <div>
            <p className="font-semibold text-slate-800 text-sm">Credential Verification Officer</p>
            <p className="text-xs text-emerald-500 font-medium">● Online</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0 max-h-[420px]">
          {chatMessages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <p className="text-slate-400 text-sm italic">Interview starting...</p>
            </div>
          )}
          {chatMessages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "doctor" ? "justify-end" : "justify-start"}`}>
              {msg.role === "ai" && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white text-[10px] font-bold mr-2 mt-0.5 flex-shrink-0">AI</div>
              )}
              <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
                msg.role === "ai"
                  ? "bg-slate-100 text-slate-800 rounded-tl-sm"
                  : "bg-blue-600 text-white rounded-tr-sm"
              }`}>
                {msg.text}
              </div>
            </div>
          ))}
          <div ref={chatBottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-4 border-t border-slate-100">
          <div className={`flex items-center gap-3 bg-slate-50 border rounded-xl px-4 py-3 transition-all ${
            inputEnabled ? "border-blue-300 ring-1 ring-blue-200" : "border-slate-200 opacity-50"
          }`}>
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendAnswer()}
              disabled={!inputEnabled}
              placeholder={inputEnabled ? "Type your answer and press Enter..." : "Waiting for the AI..."}
              className="flex-1 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 outline-none"
              autoFocus={inputEnabled}
            />
            <button
              onClick={sendAnswer}
              disabled={!inputEnabled || !inputText.trim()}
              className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-lg transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-[11px] text-slate-400 mt-1.5 text-center">
            The AI will speak the question aloud. Type your response here.
          </p>
        </div>
      </div>
    </div>
  );
}

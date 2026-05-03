import { useState } from "react";
import { useNavigate } from "react-router";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
} from "lucide-react";

interface DropZoneProps {
  label: string;
  onDrop: (name: string, fileObj: File) => void;
  fileName: string | null;
}

function DropZone({ label, onDrop, fileName }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onDrop(file.name, file);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-slate-700">
        {label}
      </label>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`w-full h-32 border-2 border-dashed rounded-xl flex flex-col items-center justify-center transition-colors cursor-pointer ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : fileName
              ? "border-emerald-400 bg-emerald-50/50"
              : "border-slate-300 bg-white hover:border-blue-400 hover:bg-slate-50"
        }`}
      >
        {fileName ? (
          <div className="flex flex-col items-center text-emerald-600">
            <CheckCircle2 className="w-8 h-8 mb-2" />
            <span className="text-sm font-medium px-4 text-center truncate max-w-[250px]">
              {fileName}
            </span>
          </div>
        ) : (
          <div className="flex flex-col items-center text-slate-500">
            <UploadCloud className="w-6 h-6 mb-2 text-blue-500" />
            <span className="text-sm">
              Drag & drop or click to upload
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export function UploadPage() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState({
    diploma: null as string | null,
    diplomaFile: null as File | null,
    id: null as string | null,
    idFile: null as File | null,
    cert: null as string | null,
    certFile: null as File | null,
  });

  const isComplete = !!docs.diploma && !!docs.id && !!docs.cert;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isComplete) return;
    
    // We only send the diploma for the hackathon demo
    const formData = new FormData();
    formData.append("name", "Dr. Yassine");
    formData.append("email", "yassine.alikacem@gmail.com");
    if (docs.diplomaFile) {
        formData.append("diploma", docs.diplomaFile);
    } else {
        alert("Please select a diploma file!");
        return;
    }

    try {
        const response = await fetch("http://localhost:8001/api/upload", {
            method: "POST",
            body: formData,
        });
        if (response.ok) {
            navigate("/processing");
        } else {
            console.error("Upload failed");
            alert("Upload failed. Please check the backend console.");
        }
    } catch (error) {
        console.error("Upload error", error);
        alert("Error connecting to server. Is the backend running?");
    }
  };

  return (
    <div className="flex flex-col items-center max-w-xl mx-auto w-full animate-in fade-in zoom-in-95 duration-300">
      <div className="text-center mb-8 w-full">
        {/* Read-only Text Banner */}
        <div className="bg-blue-50 border border-blue-100 text-blue-800 px-4 py-3 rounded-xl mb-6 text-sm font-medium flex items-center justify-center gap-2 shadow-sm">
          <CheckCircle2 className="w-4 h-4 text-blue-500" />
          Verifying account for: user@email.com
        </div>

        <h1 className="text-3xl font-bold text-blue-900 mb-2">
          Granular Document Upload
        </h1>
        <p className="text-slate-500">
          Please provide the required identification documents.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="w-full space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm"
      >
        {/* Drop Zones */}
        <div className="space-y-6">
          <DropZone
            label="1. Medical Diploma"
            fileName={docs.diploma}
            onDrop={(name, fileObj) =>
              setDocs((p) => ({ ...p, diploma: name, diplomaFile: fileObj }))
            }
          />
          <DropZone
            label="2. Government ID"
            fileName={docs.id}
            onDrop={(name, fileObj) =>
              setDocs((p) => ({ ...p, id: name, idFile: fileObj }))
            }
          />
          <DropZone
            label="3. Professional Certificate"
            fileName={docs.cert}
            onDrop={(name, fileObj) =>
              setDocs((p) => ({ ...p, cert: name, certFile: fileObj }))
            }
          />
        </div>

        <button
          type="submit"
          disabled={!isComplete}
          className={`w-full py-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2 mt-4 ${
            isComplete
              ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg"
              : "bg-slate-200 text-slate-400 cursor-not-allowed"
          }`}
        >
          Submit Documents
        </button>
      </form>
    </div>
  );
}
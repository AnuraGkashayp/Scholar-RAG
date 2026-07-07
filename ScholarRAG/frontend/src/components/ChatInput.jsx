import { useState, useRef } from "react";
import { Upload, X, FileText } from "lucide-react";

export default function ChatInput({ onSend, busy = false, phase = "" }) {
  const [input, setInput]       = useState("");
  const [file, setFile]         = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef(null);
  const dragDepth    = useRef(0);

  const acceptFile = (f) => {
    if (f && f.type === "application/pdf") setFile(f);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    dragDepth.current += 1;
    setDragging(true);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    dragDepth.current -= 1;
    if (dragDepth.current <= 0) {
      dragDepth.current = 0;
      setDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    dragDepth.current = 0;
    setDragging(false);
    acceptFile(e.dataTransfer.files[0]);
  };

  const handleSend = () => {
    if (!input.trim() || busy) return;
    const question = input;
    const f = file;
    setInput("");
    setFile(null);
    onSend(question, f);
  };

  return (
    <div className="w-full flex flex-col items-center gap-2">
      {busy && phase && (
        <div className="w-full max-w-3xl flex items-center gap-2 px-1">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse flex-shrink-0" />
          <span className="text-xs text-slate-400">{phase}</span>
        </div>
      )}

      {file && (
        <div className="w-full max-w-3xl flex items-center gap-2 px-3 py-2 bg-slate-800 border border-indigo-700 rounded-xl">
          <FileText size={14} className="text-indigo-400 flex-shrink-0" />
          <span className="text-sm text-slate-300 truncate flex-1">{file.name}</span>
          <button
            onClick={() => setFile(null)}
            className="text-slate-500 hover:text-slate-300 transition flex-shrink-0"
          >
            <X size={14} />
          </button>
        </div>
      )}

      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`w-full max-w-3xl bg-slate-900 border rounded-2xl p-3 flex items-center gap-3 shadow-lg transition-colors ${
          dragging ? "border-indigo-500 bg-slate-800" : "border-slate-700"
        }`}
      >
        <label className="cursor-pointer flex items-center justify-center w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 transition flex-shrink-0">
          <Upload size={16} className="text-slate-300" />
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => acceptFile(e.target.files[0])}
          />
        </label>

        <input
          value={dragging ? "" : input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={dragging ? "Drop PDF here..." : "Search papers, ask questions..."}
          className="flex-1 bg-transparent outline-none text-white px-2 text-[15px] placeholder:text-slate-500"
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={busy || dragging}
        />

        <button
          onClick={handleSend}
          disabled={busy}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 rounded-xl text-[15px] flex-shrink-0 transition-colors"
        >
          {busy ? (phase || "Thinking...") : "Send"}
        </button>
      </div>

      {dragging && (
        <p className="text-xs text-indigo-400">Release to attach PDF</p>
      )}

    </div>
  );
}

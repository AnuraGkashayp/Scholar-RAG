import {
  FileText,
  FolderOpen,
  Pin,
  History,
  Star,
  PlusSquare,
  Clock,
  Menu,
  LogOut,
  Zap,
  Layers,
  Cpu,
  Trash2,
} from "lucide-react";
import { FaBookOpen } from "react-icons/fa";
import { useState } from "react";

const MODELS = [
  {
    id:    "claude-haiku-4-5-20251001",
    label: "Fast",
    desc:  "Haiku 4.5 — quick answers",
    Icon:  Zap,
    color: "text-yellow-400",
  },
  {
    id:    "claude-sonnet-4-6",
    label: "Balanced",
    desc:  "Sonnet 4.6 — default",
    Icon:  Layers,
    color: "text-indigo-400",
  },
  {
    id:    "claude-opus-4-8",
    label: "Powerful",
    desc:  "Opus 4.8 — deepest reasoning",
    Icon:  Cpu,
    color: "text-purple-400",
  },
];

function ChatItem({ entry, activeId, onLoadHistory, onPin, onStar, onDelete }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={() => onLoadHistory(entry)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer ${
        entry.id === activeId ? "bg-slate-800" : "hover:bg-slate-900"
      }`}
    >
      <Clock size={13} className="text-slate-500 shrink-0" />
      <span className="text-slate-300 text-sm truncate flex-1">{entry.title}</span>
      {hovered && (
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={(e) => { e.stopPropagation(); onPin(entry.id); }}
            className={`p-0.5 rounded transition-colors ${entry.pinned ? "text-indigo-400" : "text-slate-600 hover:text-slate-300"}`}
            title={entry.pinned ? "Unpin" : "Pin"}
          >
            <Pin size={12} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onStar(entry.id); }}
            className={`p-0.5 rounded transition-colors ${entry.starred ? "text-yellow-400" : "text-slate-600 hover:text-slate-300"}`}
            title={entry.starred ? "Unstar" : "Star"}
          >
            <Star size={12} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(entry.id); }}
            className="p-0.5 rounded transition-colors text-slate-600 hover:text-red-400"
            title="Delete chat"
          >
            <Trash2 size={12} />
          </button>
        </div>
      )}
    </div>
  );
}

export default function Sidebar({
  user,
  onNewChat,
  onLogout,
  history = [],
  onLoadHistory,
  activeId,
  onPin,
  onStar,
  onDelete,
  model,
  onModelChange,
}) {
  const [open, setOpen]             = useState(true);
  const [showProfile, setShowProfile] = useState(false);
  const [view, setView]             = useState("history");

  const pinned  = history.filter(h => h.pinned);
  const starred = history.filter(h => h.starred);
  const recent  = history.filter(h => !h.pinned);

  const currentModel = MODELS.find(m => m.id === model) || MODELS[1];

  return (
    <div className="flex h-full">
      <div
        className={`h-full bg-slate-950 flex flex-col transition-all duration-300 overflow-hidden flex-shrink-0 ${
          open ? "w-72 p-5 border-r border-slate-800" : "w-0 p-0"
        }`}
      >
        {/* HEADER */}
        <div className="flex items-center gap-3 mb-10 whitespace-nowrap">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg flex-shrink-0">
            <FaBookOpen className="text-2xl text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-extrabold text-white">ScholarRAG</h1>
            <p className="text-xs text-slate-400">Research Intelligence Platform</p>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="text-slate-400 hover:text-white transition-colors flex-shrink-0"
            title="Close sidebar"
          >
            <Menu size={18} />
          </button>
        </div>

        <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Workspace</p>

        {/* NAVIGATION */}
        <div className="space-y-1 mt-2">
          <div
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-900 cursor-pointer"
            onClick={onNewChat}
          >
            <PlusSquare size={18} />
            <span>New Chat</span>
          </div>


          <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-900 cursor-pointer text-slate-400">
            <FileText size={18} />
            <span>Documents</span>
          </div>

          <div
            className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
              view === "collections" ? "bg-slate-900 text-yellow-400" : "hover:bg-slate-900"
            }`}
            onClick={() => setView(v => v === "collections" ? "history" : "collections")}
          >
            <FolderOpen size={18} />
            <span>Collections</span>
            {starred.length > 0 && (
              <span className="ml-auto text-xs text-yellow-400 font-medium bg-yellow-400/10 px-1.5 py-0.5 rounded-full">
                {starred.length}
              </span>
            )}
          </div>

          <div
            className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
              view === "pinned" ? "bg-slate-900 text-indigo-400" : "hover:bg-slate-900"
            }`}
            onClick={() => setView(v => v === "pinned" ? "history" : "pinned")}
          >
            <Pin size={18} />
            <span>Pinned</span>
            {pinned.length > 0 && (
              <span className="ml-auto text-xs text-indigo-400 font-medium bg-indigo-400/10 px-1.5 py-0.5 rounded-full">
                {pinned.length}
              </span>
            )}
          </div>

          <div
            className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
              view === "history" ? "bg-slate-900" : "hover:bg-slate-900"
            }`}
            onClick={() => setView("history")}
          >
            <History size={18} />
            <span>Recent Activity</span>
          </div>
        </div>

        {/* HISTORY / PINNED / COLLECTIONS */}
        <div className="mt-6 flex-1 overflow-y-auto">

          {view === "pinned" && (
            <>
              <h3 className="text-xs font-bold text-indigo-400 mb-2 px-3 flex items-center gap-1.5 uppercase tracking-wider">
                <Pin size={10} /> Pinned
              </h3>
              <div className="space-y-1">
                {pinned.length === 0
                  ? <p className="text-xs text-slate-600 px-3">No pinned chats yet.</p>
                  : pinned.map(e => (
                      <ChatItem key={e.id} entry={e} activeId={activeId} onLoadHistory={onLoadHistory} onPin={onPin} onStar={onStar} onDelete={onDelete} />
                    ))
                }
              </div>
            </>
          )}

          {view === "collections" && (
            <>
              <h3 className="text-xs font-bold text-yellow-400 mb-2 px-3 flex items-center gap-1.5 uppercase tracking-wider">
                <Star size={10} /> Collections
              </h3>
              <div className="space-y-1">
                {starred.length === 0
                  ? <p className="text-xs text-slate-600 px-3">No starred chats yet.</p>
                  : starred.map(e => (
                      <ChatItem key={e.id} entry={e} activeId={activeId} onLoadHistory={onLoadHistory} onPin={onPin} onStar={onStar} onDelete={onDelete} />
                    ))
                }
              </div>
            </>
          )}

          {view === "history" && (
            <>
              {pinned.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-bold text-slate-500 mb-1.5 px-3 flex items-center gap-1.5 uppercase tracking-wider">
                    <Pin size={10} /> Pinned
                  </h3>
                  <div className="space-y-1">
                    {pinned.map(e => (
                      <ChatItem key={e.id} entry={e} activeId={activeId} onLoadHistory={onLoadHistory} onPin={onPin} onStar={onStar} onDelete={onDelete} />
                    ))}
                  </div>
                  <div className="border-t border-slate-800/60 mt-3 mb-3" />
                </div>
              )}
              <h3 className="text-xs font-bold text-slate-400 mb-2 px-3 uppercase tracking-wider">Recent</h3>
              <div className="space-y-1">
                {recent.length === 0
                  ? <p className="text-xs text-slate-600 px-3">No chats yet.</p>
                  : recent.map(e => (
                      <ChatItem key={e.id} entry={e} activeId={activeId} onLoadHistory={onLoadHistory} onPin={onPin} onStar={onStar} onDelete={onDelete} />
                    ))
                }
              </div>
            </>
          )}
        </div>

        {/* PROFILE */}
        <div className="mt-auto pt-4 relative">
          {showProfile && (
            <div className="absolute bottom-full mb-2 left-0 right-0 bg-slate-900 rounded-xl p-3 space-y-1 border border-slate-800 shadow-xl z-10">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 px-1">AI Model</p>
              {MODELS.map(m => {
                const Icon = m.Icon;
                return (
                  <button
                    key={m.id}
                    onClick={() => { onModelChange(m.id); setShowProfile(false); }}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors ${
                      model === m.id
                        ? "bg-slate-800 border border-slate-700"
                        : "hover:bg-slate-800"
                    }`}
                  >
                    <Icon size={14} className={m.color} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white font-medium">{m.label}</p>
                      <p className="text-xs text-slate-500 truncate">{m.desc}</p>
                    </div>
                    {model === m.id && (
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          )}

          <div
            className="bg-slate-900 p-3 rounded-xl flex items-center gap-3 cursor-pointer hover:bg-slate-800 transition-colors"
            onClick={() => setShowProfile(v => !v)}
          >
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-sm flex-shrink-0">
              {user?.email?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="flex flex-col flex-1 min-w-0">
              <p className="font-medium text-white text-sm truncate">{user?.email ?? ""}</p>
              <p className="text-xs text-slate-400 flex items-center gap-1">
                <currentModel.Icon size={10} className={currentModel.color} />
                {currentModel.label} mode
              </p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); onLogout(); }}
              className="text-slate-400 hover:text-red-400 transition-colors flex-shrink-0"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </div>

      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="px-2 pt-4 text-slate-400 hover:text-white transition-colors flex-shrink-0"
          title="Open sidebar"
        >
          <Menu size={18} />
        </button>
      )}
    </div>
  );
}

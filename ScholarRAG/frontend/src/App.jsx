import { useState, useRef, useEffect, useCallback } from "react";
import { flushSync } from "react-dom";
import ReactMarkdown from "react-markdown";
import API_URL from "./api";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { FileText } from "lucide-react";
import Sidebar from "./components/Sidebar";
import ChatInput from "./components/ChatInput";
import SourcesPanel from "./components/SourcesPanel";
import Login from "./components/Login";
import Register from "./components/Register";

function makeSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

const markdownComponents = {
  p: ({ children }) => (
    <p className="mb-3 last:mb-0 leading-8 text-slate-200 text-[15px]">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="text-white font-semibold">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="text-slate-300 italic">{children}</em>
  ),
  h1: ({ children }) => (
    <h1 className="text-3xl font-bold text-white mt-6 mb-3 pb-1 border-b border-slate-700">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-2xl font-bold text-white mt-5 mb-2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-xl font-semibold text-white mt-4 mb-2">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-lg font-semibold text-slate-100 mt-3 mb-1">{children}</h4>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-6 space-y-2 mb-3 text-slate-200 text-[15px]">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-6 space-y-2 mb-3 text-slate-200 text-[15px]">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="leading-7">{children}</li>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-indigo-500 pl-4 my-3 text-slate-400 italic text-[15px]">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="border-slate-700 my-4" />,
  pre: ({ children }) => <>{children}</>,
  code: ({ className, children }) => {
    const match = /language-(\w+)/.exec(className || "");
    const language = match ? match[1] : "";
    const code = String(children).replace(/\n$/, "");

    if (match) {
      return (
        <div className="rounded-xl overflow-hidden border border-slate-700 my-3 text-sm">
          <div className="flex items-center justify-between px-4 py-1.5 bg-[#1e1e1e] border-b border-slate-700">
            <span className="text-xs text-slate-400 font-mono">{language}</span>
            <button
              onClick={() => navigator.clipboard.writeText(code)}
              className="text-xs text-slate-500 hover:text-slate-300 transition"
            >
              copy
            </button>
          </div>
          <SyntaxHighlighter
            language={language}
            style={vscDarkPlus}
            customStyle={{ margin: 0, borderRadius: 0, background: "#1e1e1e", padding: "1rem" }}
            showLineNumbers={true}
            lineNumberStyle={{ color: "#4a5568", minWidth: "2.5em" }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      );
    }

    return (
      <code className="bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    );
  },
  table: ({ children }) => (
    <div className="overflow-x-auto mb-4 rounded-lg border border-slate-700">
      <table className="w-full border-collapse text-[15px]">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-slate-800">{children}</thead>
  ),
  tbody: ({ children }) => (
    <tbody className="divide-y divide-slate-700">{children}</tbody>
  ),
  tr: ({ children }) => (
    <tr className="border-b border-slate-700 hover:bg-slate-800/40 transition-colors">{children}</tr>
  ),
  th: ({ children }) => (
    <th className="px-4 py-2.5 text-left font-semibold text-white text-sm uppercase tracking-wider">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-2.5 text-slate-300">{children}</td>
  ),
};

export default function App() {
  const [token, setToken]       = useState(() => localStorage.getItem("token"));
  const [user, setUser]         = useState(() => {
    try { return JSON.parse(localStorage.getItem("user")); } catch { return null; }
  });
  const [authPage, setAuthPage]     = useState("login");
  const [latestKeys, setLatestKeys]   = useState(new Set());
  const [history, setHistory]         = useState([]);
  const [activeId, setActiveId]       = useState(() => localStorage.getItem("sessionId") || makeSessionId());
  const [streaming, setStreaming]     = useState({});
  const [model, setModel] = useState(() => localStorage.getItem("preferredModel") || "claude-sonnet-4-6");
  const [panelWidth, setPanelWidth] = useState(360);
  const bottomRef         = useRef(null);
  const streamingRefs     = useRef({});
  const activeIdRef       = useRef(activeId);
  const isDragging = useRef(false);

  const activeChat   = history.find(c => c.id === activeId);
  const messages     = activeChat?.messages || [];
  const sources      = activeChat?.sources || [];
  const activeStream = streaming[activeId] || null;

  const handleDragStart = useCallback(() => {
    isDragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const handleDrag = useCallback((e) => {
    if (!isDragging.current) return;
    const newWidth = window.innerWidth - e.clientX;
    if (newWidth >= 200 && newWidth <= 600) setPanelWidth(newWidth);
  }, []);

  const handleDragEnd = useCallback(() => {
    isDragging.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", handleDrag);
    window.addEventListener("mouseup", handleDragEnd);
    return () => {
      window.removeEventListener("mousemove", handleDrag);
      window.removeEventListener("mouseup", handleDragEnd);
    };
  }, [handleDrag, handleDragEnd]);

  useEffect(() => {
    activeIdRef.current = activeId;
    localStorage.setItem("sessionId", activeId);
  }, [activeId]);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/chats`, {
      headers: { "Authorization": `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => setHistory(data))
      .catch(() => {});
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, activeStream?.text]);

  const handleLogin = (newToken, newUser) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("sessionId");
    setToken(null);
    setUser(null);
    setHistory([]);
    setStreaming({});
    streamingRefs.current = {};
    setActiveId(makeSessionId());
  };

  const handleModelChange = (newModel) => {
    setModel(newModel);
    localStorage.setItem("preferredModel", newModel);
  };

  const handleDelete = async (chatId) => {
    await fetch(`${API_URL}/chats/${chatId}`, {
      method:  "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    }).catch(() => null);
    setHistory(prev => prev.filter(h => h.id !== chatId));
    if (activeId === chatId) setActiveId(makeSessionId());
  };

  const handlePin = async (chatId) => {
    const res = await fetch(`${API_URL}/chats/${chatId}/pin`, {
      method:  "POST",
      headers: { "Authorization": `Bearer ${token}` },
    }).catch(() => null);
    if (!res?.ok) return;
    const data = await res.json();
    setHistory(prev => prev.map(h => h.id === chatId ? { ...h, pinned: data.pinned } : h));
  };

  const handleStar = async (chatId) => {
    const res = await fetch(`${API_URL}/chats/${chatId}/star`, {
      method:  "POST",
      headers: { "Authorization": `Bearer ${token}` },
    }).catch(() => null);
    if (!res?.ok) return;
    const data = await res.json();
    setHistory(prev => prev.map(h => h.id === chatId ? { ...h, starred: data.starred } : h));
  };

  if (!token || !user) {
    return authPage === "login"
      ? <Login onLogin={handleLogin} onSwitch={() => setAuthPage("register")} />
      : <Register onLogin={handleLogin} onSwitch={() => setAuthPage("login")} />;
  }

  const sendQuery = async (question, file) => {
    const chatId   = activeId;
    const fileName = file?.name || null;

    const userMsgs = [
      ...(fileName ? [{ role: "document", text: fileName }] : []),
      { role: "user", text: question },
    ];
    setHistory(prev => {
      const exists = prev.find(c => c.id === chatId);
      if (exists) {
        return prev.map(c => c.id === chatId ? { ...c, messages: [...c.messages, ...userMsgs] } : c);
      }
      return [
        { id: chatId, title: question.slice(0, 40), messages: userMsgs, sources: [], pinned: false, starred: false },
        ...prev,
      ];
    });

    streamingRefs.current[chatId] = "";
    setStreaming(prev => ({ ...prev, [chatId]: { text: "", phase: "Searching..." } }));

    let doneSources = [];
    try {
      const form = new FormData();
      form.append("question", question);
      form.append("session_id", chatId);
      form.append("model", model);
      if (file) form.append("file", file);

      const res = await fetch(`${API_URL}/query/stream`, {
        method:  "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body:    form,
      });

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(part.slice(6));
            if (data.type === "status") {
              setStreaming(prev => ({ ...prev, [chatId]: { text: streamingRefs.current[chatId] || "", phase: data.text } }));
            }
            if (data.type === "token") {
              streamingRefs.current[chatId] = (streamingRefs.current[chatId] || "") + data.text;
              const apply = () => setStreaming(prev => ({ ...prev, [chatId]: { text: streamingRefs.current[chatId], phase: "" } }));
              if (chatId === activeIdRef.current) flushSync(apply); else apply();
            }
            if (data.type === "done") {
              doneSources = data.sources || [];
            }
          } catch {}
        }
      }

      const finalText = streamingRefs.current[chatId] || "";
      setHistory(prev => prev.map(c => {
        if (c.id !== chatId) return c;
        const existingKeys = new Set((c.sources || []).map(s => s.arxiv_id || s.title));
        const added = doneSources.filter(s => !existingKeys.has(s.arxiv_id || s.title));
        return {
          ...c,
          messages: [...c.messages, { role: "assistant", text: finalText }],
          sources:  [...added, ...(c.sources || [])],
        };
      }));
      if (chatId === activeIdRef.current) {
        setLatestKeys(new Set(doneSources.map(s => s.arxiv_id || s.title).filter(Boolean)));
      }
    } catch (err) {
      console.error("Stream error:", err);
      setHistory(prev => prev.map(c => c.id === chatId
        ? { ...c, messages: [...c.messages, { role: "assistant", text: "_Sorry — something went wrong with that request._" }] }
        : c));
    } finally {
      delete streamingRefs.current[chatId];
      setStreaming(prev => {
        const next = { ...prev };
        delete next[chatId];
        return next;
      });
    }
  };

  const handleNewChat = () => {
    setActiveId(makeSessionId());
    setLatestKeys(new Set());
  };

  const handleLoadHistory = (entry) => {
    setActiveId(entry.id);
    setLatestKeys(new Set());
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">

      <Sidebar
        user={user}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        history={history}
        onLoadHistory={handleLoadHistory}
        activeId={activeId}
        onPin={handlePin}
        onStar={handleStar}
        onDelete={handleDelete}
        model={model}
        onModelChange={handleModelChange}
      />

      {/* Center chat area */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 && !activeStream ? (
            <div className="flex flex-col items-center justify-center h-full gap-3">
              <h2 className="text-4xl font-bold text-slate-200">
                Good to see you
              </h2>
              <p className="text-slate-500 text-base">What do you want to know today?</p>
            </div>
          ) : (
            <div className="py-6">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`px-6 py-3 ${
                    msg.role === "user" || msg.role === "document"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }`}
                >
                  {msg.role === "document" ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-indigo-800/50 rounded-lg text-xs text-slate-400 max-w-xs">
                      <FileText size={12} className="text-indigo-400 flex-shrink-0" />
                      <span className="truncate">{msg.text}</span>
                    </div>
                  ) : msg.role === "assistant" ? (
                    <div className="flex gap-4 w-full max-w-3xl">
                      {/* Avatar */}
                      <div className="w-8 h-8 rounded-full bg-indigo-600 flex-shrink-0 flex items-center justify-center mt-0.5 shadow-lg">
                        <span className="text-white text-xs font-bold">S</span>
                      </div>
                      {/* Content — no box, clean text */}
                      <div className="flex-1 min-w-0 text-base">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={markdownComponents}
                        >
                          {msg.text}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-xl bg-slate-700/70 text-white px-4 py-3 rounded-2xl text-[15px] leading-relaxed">
                      {msg.text}
                    </div>
                  )}
                </div>
              ))}
              {activeStream && (
                <div className="px-6 py-3 flex justify-start">
                  <div className="flex gap-4 w-full max-w-3xl">
                    <div className="w-8 h-8 rounded-full bg-indigo-600 flex-shrink-0 flex items-center justify-center mt-0.5 shadow-lg">
                      <span className="text-white text-xs font-bold">S</span>
                    </div>
                    <div className="flex-1 min-w-0 text-base">
                      {activeStream.text ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={markdownComponents}
                        >
                          {activeStream.text}
                        </ReactMarkdown>
                      ) : (
                        <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse rounded-sm" />
                      )}
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input at bottom */}
        <div className="px-6 pb-6 pt-2 border-t border-slate-800/50">
          <ChatInput
            onSend={sendQuery}
            busy={!!activeStream}
            phase={activeStream?.phase || ""}
          />
        </div>
      </div>

      {/* Drag handle */}
      <div
        onMouseDown={handleDragStart}
        className="w-1 cursor-col-resize bg-slate-800 hover:bg-indigo-600 transition-colors flex-shrink-0"
      />

      <SourcesPanel sources={sources} latestKeys={latestKeys} width={panelWidth} />

    </div>
  );
}

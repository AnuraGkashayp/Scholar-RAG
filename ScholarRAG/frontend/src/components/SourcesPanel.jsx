import { useState } from "react";
import { ExternalLink, GitBranch, BookOpen, Star, Users, Calendar, Hash, BookMarked, Microscope, FileText, Search, X } from "lucide-react";

const CATEGORY_COLORS = {
  vision:        "bg-blue-900/60 text-blue-300 border-blue-700",
  video:         "bg-purple-900/60 text-purple-300 border-purple-700",
  language:      "bg-green-900/60 text-green-300 border-green-700",
  audio:         "bg-yellow-900/60 text-yellow-300 border-yellow-700",
  general:       "bg-indigo-900/60 text-indigo-300 border-indigo-700",
  other:         "bg-slate-700/60 text-slate-300 border-slate-600",
  miscellaneous: "bg-slate-700/60 text-slate-300 border-slate-600",
  medicine:      "bg-red-900/60 text-red-300 border-red-700",
  biology:       "bg-emerald-900/60 text-emerald-300 border-emerald-700",
  physics:       "bg-cyan-900/60 text-cyan-300 border-cyan-700",
  mathematics:   "bg-orange-900/60 text-orange-300 border-orange-700",
  economics:     "bg-lime-900/60 text-lime-300 border-lime-700",
  psychology:    "bg-pink-900/60 text-pink-300 border-pink-700",
};

function MetaRow({ icon: Icon, label, children }) {
  if (!children) return null;
  return (
    <div className="flex items-start gap-1.5 text-xs text-slate-400">
      <Icon size={11} className="mt-0.5 flex-shrink-0 text-slate-500" />
      {label && <span className="text-slate-600 flex-shrink-0">{label}:</span>}
      <span className="min-w-0 break-words">{children}</span>
    </div>
  );
}

export default function SourcesPanel({ sources = [], latestKeys = new Set(), width = 360 }) {
  const [query, setQuery] = useState("");

  const filtered = query.trim()
    ? sources.filter(s => s.title?.toLowerCase().includes(query.toLowerCase()))
    : sources;

  return (
    <div style={{ width: `${width}px` }} className="h-full border-l border-slate-800 flex flex-col bg-slate-950 flex-shrink-0">
      <div className="px-5 py-4 border-b border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-400 tracking-widest uppercase">Sources</h2>
          {sources.length > 0 && (
            <p className="text-xs text-slate-600">
              {filtered.length !== sources.length ? `${filtered.length} / ${sources.length}` : `${sources.length} paper${sources.length !== 1 ? "s" : ""}`}
            </p>
          )}
        </div>
        <div className="relative">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by title..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-7 pr-7 py-1.5 text-xs text-slate-300 placeholder:text-slate-600 outline-none focus:border-slate-600 transition-colors"
          />
          {query && (
            <button onClick={() => setQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition">
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        {sources.length === 0 ? (
          <p className="text-slate-500 text-sm leading-relaxed">
            Relevant papers will appear here after your research query.
          </p>
        ) : filtered.length === 0 ? (
          <p className="text-slate-500 text-sm">No papers match "{query}".</p>
        ) : (
          <div className="space-y-3">
            {filtered.map((src, i) => {
              const isNew         = latestKeys.has(src.arxiv_id || src.title);
              const year          = src.published ? src.published.slice(0, 4) : "";
              const authors       = Array.isArray(src.authors) ? src.authors : [];
              const displayAuthors = authors.length > 0
                ? authors.slice(0, 3).join(", ") + (authors.length > 3 ? " et al." : "")
                : "";
              const fields        = Array.isArray(src.fields_of_study) ? src.fields_of_study.slice(0, 3) : [];
              const catKey        = src.category?.toLowerCase();
              const catColor      = CATEGORY_COLORS[catKey] || "bg-slate-700/60 text-slate-300 border-slate-600";
              const githubRepos   = Array.isArray(src.github_repos) ? src.github_repos.filter(Boolean) : [];
              const arxivUrl      = src.arxiv_id ? `https://arxiv.org/abs/${src.arxiv_id}` : "";
              const arxivPdf      = src.arxiv_id ? `https://arxiv.org/pdf/${src.arxiv_id}` : "";
              const pdfLink       = src.pdf_url || arxivPdf;
              const doiUrl        = src.doi ? `https://doi.org/${src.doi}` : "";

              return (
                <div
                  key={i}
                  className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between px-3 py-2 bg-slate-800/50 border-b border-slate-800 gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-500">#{i + 1}</span>
                      {isNew && <span className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" title="From latest response" />}
                      {src.has_code && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-900/50 text-emerald-400 border border-emerald-800 font-medium">
                          Code
                        </span>
                      )}
                    </div>
                    {src.category && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium border flex-shrink-0 ${catColor}`}>
                        {src.category}
                      </span>
                    )}
                  </div>

                  <div className="p-3 space-y-2.5">
                    <h3 className="font-semibold text-sm text-white leading-snug">{src.title}</h3>

                    <div className="space-y-1.5">
                      {displayAuthors && (
                        <MetaRow icon={Users} label="Authors">{displayAuthors}</MetaRow>
                      )}
                      {year && (
                        <MetaRow icon={Calendar} label="Year">{year}</MetaRow>
                      )}
                      {src.citations > 0 && (
                        <MetaRow icon={Star} label="Citations">
                          <span className="text-yellow-400 font-medium">{src.citations.toLocaleString()}</span>
                        </MetaRow>
                      )}
                      {src.journal && (
                        <MetaRow icon={BookMarked} label="Venue">{src.journal}</MetaRow>
                      )}
                      {src.arxiv_id && (
                        <MetaRow icon={Hash} label="arXiv">{src.arxiv_id}</MetaRow>
                      )}
                      {src.doi && (
                        <MetaRow icon={FileText} label="DOI">{src.doi}</MetaRow>
                      )}
                      {fields.length > 0 && (
                        <MetaRow icon={Microscope} label="Fields">{fields.join(", ")}</MetaRow>
                      )}
                    </div>

                    {src.summary && (
                      <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed border-t border-slate-800 pt-2">
                        {src.summary}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-3 pt-1 border-t border-slate-800">
                      {pdfLink && (
                        <a href={pdfLink} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium">
                          <BookOpen size={11} /> PDF
                        </a>
                      )}
                      {arxivUrl && (
                        <a href={arxivUrl} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300 transition-colors">
                          <ExternalLink size={11} /> arXiv
                        </a>
                      )}
                      {doiUrl && (
                        <a href={doiUrl} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300 transition-colors">
                          <ExternalLink size={11} /> DOI
                        </a>
                      )}
                      {githubRepos.map((repo, ri) => (
                        <a key={ri} href={repo} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors font-medium">
                          <GitBranch size={11} />
                          {githubRepos.length > 1 ? `Code ${ri + 1}` : "Code"}
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

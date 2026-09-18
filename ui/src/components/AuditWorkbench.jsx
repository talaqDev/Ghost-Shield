import { AlertTriangle, CheckCircle, Database, Play, ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";
import AuditResultsView from "./AuditResultsView";

const dbOptions = [
  { id: "faiss", label: "FAISS", detail: "Local · exact L2 index" },
  { id: "chroma", label: "ChromaDB", detail: "Local · metadata aware" },
  { id: "qdrant", label: "Qdrant", detail: "Memory · cosine search" },
  { id: "pinecone", label: "Mock Pinecone", detail: "Simulated cloud API" },
];

const initialDocuments = [
  { id: "patient-1842", text: "Patient Ada Lovelace, diagnosis hypertension, policy H-1842." },
  { id: "finance-7719", text: "Account 7719 transferred 2400 dollars to beneficiary 12." },
];

function localVector(text, dimension = 384) {
  const vector = Array(dimension).fill(0);
  for (let index = 0; index < text.length; index += 1) vector[(text.charCodeAt(index) + index * 17) % dimension] += 1;
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value ** 2, 0)) || 1;
  return vector.map((value) => value / norm);
}

function parseDocuments(source) {
  const parsed = JSON.parse(source);
  if (!Array.isArray(parsed) || parsed.length === 0) throw new Error("Documents must be a non-empty JSON array.");
  return parsed.map((document, index) => ({
    id: String(document.id || `document-${index + 1}`),
    text: String(document.text || ""),
    metadata: document.metadata || { source: "audit-workbench" },
    vector: Array.isArray(document.vector) && document.vector.length ? document.vector : localVector(String(document.text || "")),
  }));
}

export default function AuditWorkbench() {
  const [dbType, setDbType] = useState("faiss");
  const [documentText, setDocumentText] = useState(JSON.stringify(initialDocuments, null, 2));
  const [targetId, setTargetId] = useState(initialDocuments[0].id);
  const [topK, setTopK] = useState(1);
  const [epsilon, setEpsilon] = useState(1);
  const [useDp, setUseDp] = useState(false);
  const [auditData, setAuditData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const documentIds = useMemo(() => {
    try { return JSON.parse(documentText).map((document) => document.id).filter(Boolean); } catch { return []; }
  }, [documentText]);

  async function executeAudit(event) {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    setAuditData(null);
    try {
      const response = await fetch("/api/audit/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ db_type: dbType, documents: parseDocuments(documentText), target_id: targetId, top_k: topK, epsilon: useDp ? epsilon : null }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Audit request failed.");
      setAuditData(payload);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-5 xl:grid-cols-[1.1fr_.9fr]">
        <form onSubmit={executeAudit} className="space-y-5 rounded-xl border border-white/8 bg-black/10 p-5">
          <div className="flex items-start justify-between gap-3"><div><div className="mb-2 flex items-center gap-2 text-emerald-300"><Database size={17} /><span className="font-mono text-[10px] uppercase tracking-[0.15em]">Connection manager</span></div><h3 className="text-lg font-semibold text-white">Configure audit target</h3></div><span className="rounded-md border border-emerald-300/15 px-2 py-1 font-mono text-[10px] text-emerald-300">LIVE API</span></div>
          <div className="grid grid-cols-2 gap-2">{dbOptions.map((option) => <button type="button" key={option.id} onClick={() => setDbType(option.id)} className={`rounded-lg border p-3 text-left transition ${dbType === option.id ? "border-emerald-300/50 bg-emerald-300/10" : "border-white/8 bg-white/[0.025] hover:border-white/20"}`}><span className="block text-sm font-semibold text-white">{option.label}</span><span className="mt-1 block text-[10px] text-slate-500">{option.detail}</span></button>)}</div>
          <div><label className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500" htmlFor="documents">Document batch · JSON</label><textarea id="documents" value={documentText} onChange={(event) => setDocumentText(event.target.value)} className="min-h-48 w-full rounded-lg border border-white/10 bg-[#07110f] p-3 font-mono text-xs leading-5 text-slate-300 outline-none transition focus:border-emerald-300/50" spellCheck="false" /></div>
          <div className="grid gap-4 sm:grid-cols-2"><label className="block"><span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Target ID to soft-delete</span><select value={targetId} onChange={(event) => setTargetId(event.target.value)} className="w-full rounded-lg border border-white/10 bg-[#07110f] px-3 py-2.5 text-sm text-slate-200 outline-none">{documentIds.map((id) => <option key={id}>{id}</option>)}<option value="">First document</option></select></label><label className="block"><span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Top-k search depth · {topK}</span><input type="range" min="1" max="5" value={topK} onChange={(event) => setTopK(Number(event.target.value))} className="mt-3 w-full accent-emerald-300" /></label></div>
          <label className="flex items-center justify-between rounded-lg border border-white/8 bg-white/[0.025] p-3"><span><span className="block text-sm text-slate-300">Enable differential privacy</span><span className="mt-1 block text-xs text-slate-500">Obfuscate vectors before indexing</span></span><span className="flex items-center gap-3"><input type="checkbox" checked={useDp} onChange={(event) => setUseDp(event.target.checked)} className="size-4 accent-emerald-300" />{useDp && <span className="font-mono text-xs text-emerald-300">ε {epsilon.toFixed(1)}</span>}</span></label>{useDp && <input type="range" min="0.1" max="5" step="0.1" value={epsilon} onChange={(event) => setEpsilon(Number(event.target.value))} className="w-full accent-emerald-300" />}
          <button type="submit" disabled={isLoading} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 disabled:opacity-50">{isLoading ? <><span className="size-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" /> Running audit...</> : <><Play size={16} fill="currentColor" /> Execute security audit</>}</button>
          {error && <div className="flex items-start gap-2 rounded-lg border border-rose-300/20 bg-rose-300/5 p-3 text-xs leading-5 text-rose-200"><AlertTriangle size={15} className="mt-0.5 shrink-0" />{error}</div>}
        </form>
        <div className="rounded-xl border border-white/8 bg-black/10 p-5"><div className="mb-5 flex items-center gap-2 text-slate-300"><ShieldAlert size={17} className="text-amber-200" /><h3 className="text-sm font-semibold">Audit output</h3></div><AuditResultsView auditData={auditData} /></div>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-500"><CheckCircle size={14} className="text-emerald-300" /> Records are sent to the local FastAPI service only.</div>
    </div>
  );
}

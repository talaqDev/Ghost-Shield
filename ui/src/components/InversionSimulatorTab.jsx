import { useMemo, useState } from "react";
import { AlertTriangle, Bot, CheckCircle, Play, Sparkles } from "lucide-react";

const sampleVector = JSON.stringify([0.12, -0.08, 0.21, 0.04, -0.16, 0.09, 0.18, -0.03], null, 2);

export default function InversionSimulatorTab() {
  const [method, setMethod] = useState("knn");
  const [vectorText, setVectorText] = useState(sampleVector);
  const [reference, setReference] = useState("patient diagnosis record\nfinancial account transaction\nquantum computing research");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const referenceLines = useMemo(() => reference.split("\n").map((line) => line.trim()).filter(Boolean), [reference]);

  async function simulate(event) {
    event.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try {
      const parsed = JSON.parse(vectorText);
      const targetVectors = Array.isArray(parsed[0]) ? parsed : [parsed];
      const response = await fetch(`/api/attack/${method}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_vectors: targetVectors, reference_corpus: referenceLines, top_k: 3 }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Attack simulation failed.");
      setResult(payload);
    } catch (requestError) {
      setError(requestError.message);
    } finally { setLoading(false); }
  }

  const candidates = result?.candidates?.[0] || [];
  return (
    <div className="grid gap-5 xl:grid-cols-[.9fr_1.1fr]">
      <form onSubmit={simulate} className="space-y-5 rounded-xl border border-white/8 bg-black/10 p-5">
        <div className="flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-cyan-300/10 text-cyan-300"><Bot size={19} /></div><div><h3 className="text-lg font-semibold text-white">Inversion attack simulator</h3><p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Compare recovery engines</p></div></div>
        <div className="grid grid-cols-2 gap-2">{[["knn", "KNN inversion"], ["mlp", "PyTorch MLP"]].map(([id, label]) => <button type="button" key={id} onClick={() => setMethod(id)} className={`rounded-lg border p-3 text-left text-sm font-semibold transition ${method === id ? "border-cyan-300/50 bg-cyan-300/10 text-cyan-100" : "border-white/8 text-slate-500 hover:border-white/20"}`}>{label}<span className="mt-1 block text-[10px] font-normal text-slate-500">{id === "knn" ? "Reference nearest-neighbor" : "Learned token decoder"}</span></button>)}</div>
        <label className="block"><span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Target vector · JSON</span><textarea value={vectorText} onChange={(event) => setVectorText(event.target.value)} className="min-h-36 w-full rounded-lg border border-white/10 bg-[#07110f] p-3 font-mono text-xs leading-5 text-slate-300 outline-none focus:border-cyan-300/50" spellCheck="false" /></label>
        <label className="block"><span className="mb-2 block font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Reference corpus · one text per line</span><textarea value={reference} onChange={(event) => setReference(event.target.value)} className="min-h-28 w-full rounded-lg border border-white/10 bg-[#07110f] p-3 text-xs leading-5 text-slate-300 outline-none focus:border-cyan-300/50" /></label>
        <button type="submit" disabled={loading} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-300 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-200 disabled:opacity-50">{loading ? "Simulating attack..." : <><Play size={16} fill="currentColor" /> Run {method.toUpperCase()} attack</>}</button>
        {error && <div className="flex gap-2 rounded-lg border border-rose-300/20 bg-rose-300/5 p-3 text-xs text-rose-200"><AlertTriangle size={15} />{error}</div>}
      </form>
      <section className="rounded-xl border border-white/8 bg-black/10 p-5"><div className="mb-5 flex items-center gap-2"><Sparkles size={17} className="text-cyan-300" /><h3 className="text-sm font-semibold text-white">Recovered candidates</h3></div>{candidates.length ? <div className="space-y-3">{candidates.map((candidate, index) => <div key={`${candidate}-${index}`} className="rounded-lg border border-white/8 bg-white/[0.025] p-4"><div className="mb-2 flex items-center justify-between"><span className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Rank {index + 1}</span><span className="flex items-center gap-1.5 text-xs text-emerald-300"><CheckCircle size={13} /> {Math.max(10, 100 - index * 19)}% confidence</span></div><p className="text-sm text-slate-200">{highlight(candidate, referenceLines)}</p></div>)}</div> : <div className="grid min-h-64 place-items-center text-center text-sm text-slate-500">Run an attack to inspect reconstructed text candidates.</div>}</section>
    </div>
  );
}

function highlight(candidate, referenceLines) {
  const tokens = new Set(referenceLines.join(" ").toLowerCase().split(/\s+/));
  return candidate.split(/(\s+)/).map((part, index) => tokens.has(part.toLowerCase()) ? <mark key={index} className="rounded bg-cyan-300/20 px-0.5 text-cyan-200">{part}</mark> : <span key={index}>{part}</span>);
}

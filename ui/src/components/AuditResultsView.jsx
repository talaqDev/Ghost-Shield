import { AlertTriangle, CheckCircle, ShieldAlert } from "lucide-react";
import RiskCharts from "./RiskCharts";

const riskStyles = {
  CRITICAL: "border-rose-400/30 bg-rose-400/10 text-rose-200",
  HIGH: "border-orange-300/30 bg-orange-300/10 text-orange-200",
  MEDIUM: "border-yellow-300/30 bg-yellow-300/10 text-yellow-100",
  LOW: "border-emerald-300/30 bg-emerald-300/10 text-emerald-200",
};

function score(value) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export default function AuditResultsView({ auditData }) {
  if (!auditData) {
    return <div className="grid min-h-56 place-items-center rounded-xl border border-dashed border-white/10 p-8 text-center text-sm text-slate-500">Run an audit to reveal the leakage profile.</div>;
  }

  const risk = auditData.risk_level || "LOW";
  const retentionRisk = auditData.soft_delete_leakage_found;
  const metrics = auditData.leakage_metrics;

  return (
    <div className="space-y-4">
      <div className={`flex flex-wrap items-center justify-between gap-4 rounded-xl border p-5 ${riskStyles[risk] || riskStyles.LOW}`}>
        <div className="flex items-center gap-3"><ShieldAlert size={22} /><div><p className="font-mono text-[10px] uppercase tracking-[0.16em] opacity-70">Overall risk level</p><strong className="text-2xl tracking-tight">{risk}</strong></div></div>
        <div className="text-right"><p className="font-mono text-[10px] uppercase tracking-[0.14em] opacity-70">Inversion vulnerability</p><strong className="text-xl">{score(auditData.inversion_vulnerability_score)}</strong></div>
      </div>
      <div className={`rounded-xl border p-5 ${retentionRisk ? "border-orange-300/25 bg-orange-300/5" : "border-emerald-300/20 bg-emerald-300/5"}`}>
        <div className="flex items-start gap-3">{retentionRisk ? <AlertTriangle className="mt-0.5 text-orange-200" size={19} /> : <CheckCircle className="mt-0.5 text-emerald-300" size={19} />}<div><h3 className="text-sm font-semibold text-white">{retentionRisk ? "Residual vectors detected after soft-delete" : "No residual vectors detected"}</h3><p className="mt-1 text-xs leading-5 text-slate-400">{retentionRisk ? "The connector hid the record from normal search, but raw vector artifacts remained available for inspection." : "The selected records were not recoverable from the connector storage layer."}</p></div></div>
      </div>
      <div className="overflow-hidden rounded-xl border border-white/8"><div className="border-b border-white/8 px-5 py-4"><h3 className="text-sm font-semibold text-white">Leakage breakdown</h3><p className="mt-1 text-xs text-slate-500">Similarity between source and reconstructed payload</p></div><div className="grid grid-cols-3 divide-x divide-white/8"><Metric label="BLEU-4" value={score(metrics?.bleu_score)} /><Metric label="ROUGE-L" value={score(metrics?.rouge_l)} /><Metric label="Cosine" value={score(metrics?.cosine_similarity)} /></div></div>
      <RiskCharts auditData={auditData} />
    </div>
  );
}

function Metric({ label, value }) {
  return <div className="px-4 py-5"><span className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">{label}</span><strong className="mt-2 block text-lg text-white">{value}</strong></div>;
}

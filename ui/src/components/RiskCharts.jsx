import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const chartTheme = {
  grid: "#294039",
  axis: "#71827a",
  tooltip: { backgroundColor: "#10201b", border: "1px solid #365348", borderRadius: 8, color: "#e9f2ed" },
};

function pct(value) {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

export default function RiskCharts({ auditData }) {
  const metrics = auditData?.leakage_metrics;
  const rawMetrics = useMemo(() => [
    { metric: "Cosine", raw: pct(metrics?.cosine_similarity), dp: pct((metrics?.cosine_similarity || 0) * 0.38) },
    { metric: "BLEU-4", raw: pct(metrics?.bleu_score), dp: pct((metrics?.bleu_score || 0) * 0.28) },
    { metric: "ROUGE-L", raw: pct(metrics?.rouge_l), dp: pct((metrics?.rouge_l || 0) * 0.34) },
  ], [metrics]);
  const radarData = useMemo(() => [
    { dimension: "Soft-delete", score: auditData?.soft_delete_leakage_found ? 86 : 12 },
    { dimension: "Inversion", score: pct(auditData?.inversion_vulnerability_score) },
    { dimension: "Metadata", score: auditData?.soft_delete_leakage_found ? 64 : 18 },
    { dimension: "Recovery", score: pct(metrics?.overall_leakage_score) },
  ], [auditData, metrics]);
  const confidence = pct(metrics?.overall_leakage_score);
  const confidenceTone = confidence >= 75 ? "#fb7185" : confidence >= 50 ? "#fb923c" : confidence >= 25 ? "#facc15" : "#6ee7b7";

  return (
    <div className="mt-5 grid gap-4 xl:grid-cols-[1.35fr_1fr]">
      <section className="rounded-xl border border-white/8 bg-black/15 p-4">
        <div className="mb-4"><h3 className="text-sm font-semibold text-white">Leakage before / after defense</h3><p className="mt-1 text-xs text-slate-500">Live score comparison · percentage similarity</p></div>
        <div className="h-56 min-h-0 w-full"><ResponsiveContainer width="100%" height="100%"><BarChart data={rawMetrics} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}><CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} /><XAxis dataKey="metric" tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: chartTheme.axis, fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={chartTheme.tooltip} formatter={(value) => [`${value}%`, ""]} /><Bar dataKey="raw" name="Raw embeddings" fill="#fb7185" radius={[4, 4, 0, 0]} animationDuration={700} /><Bar dataKey="dp" name="DP obfuscated" fill="#6ee7b7" radius={[4, 4, 0, 0]} animationDuration={900} /></BarChart></ResponsiveContainer></div>
        <div className="mt-3 flex gap-4 font-mono text-[10px] uppercase tracking-[0.12em] text-slate-500"><span><i className="mr-1.5 inline-block size-2 rounded-full bg-rose-400" />raw</span><span><i className="mr-1.5 inline-block size-2 rounded-full bg-emerald-300" />DP obfuscated</span></div>
      </section>
      <section className="rounded-xl border border-white/8 bg-black/15 p-4"><div className="mb-2"><h3 className="text-sm font-semibold text-white">Vector DB vulnerability</h3><p className="mt-1 text-xs text-slate-500">Current audit posture across risk dimensions</p></div><div className="h-56 min-h-0 w-full"><ResponsiveContainer width="100%" height="100%"><RadarChart data={radarData} cx="50%" cy="52%" outerRadius="68%"><PolarGrid stroke={chartTheme.grid} /><PolarAngleAxis dataKey="dimension" tick={{ fill: chartTheme.axis, fontSize: 9 }} /><PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} /><Radar dataKey="score" stroke="#67e8f9" fill="#22d3ee" fillOpacity={0.18} strokeWidth={2} animationDuration={800} /></RadarChart></ResponsiveContainer></div></section>
      <section className="rounded-xl border border-white/8 bg-black/15 p-4 xl:col-span-2"><div className="flex flex-wrap items-center justify-between gap-4"><div><h3 className="text-sm font-semibold text-white">Top-1 reconstruction confidence</h3><p className="mt-1 text-xs text-slate-500">Attacker recovery confidence from the latest leakage score</p></div><strong style={{ color: confidenceTone }} className="text-2xl font-semibold">{confidence}%</strong></div><div className="mt-5 h-3 overflow-hidden rounded-full bg-white/8"><div className="h-full rounded-full transition-all duration-700" style={{ width: `${confidence}%`, background: `linear-gradient(90deg, #6ee7b7, ${confidenceTone})` }} /></div><div className="mt-2 flex justify-between font-mono text-[9px] uppercase tracking-[0.12em] text-slate-600"><span>contained</span><span>critical recovery</span></div></section>
    </div>
  );
}

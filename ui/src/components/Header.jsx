import { ShieldCheck } from "lucide-react";
import StatusPill from "./StatusPill";

export default function Header({ health }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/8 px-6 py-5 lg:px-10">
      <div className="flex items-center gap-3">
        <div className="grid size-10 place-items-center rounded-xl bg-emerald-300 text-slate-950 shadow-[0_0_28px_rgba(110,231,183,0.22)]">
          <ShieldCheck size={22} strokeWidth={2.5} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight text-white">Ghost Shield</span>
            <span className="rounded bg-white/8 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">v0.1.0</span>
          </div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">Vector privacy command center</p>
        </div>
      </div>
      <StatusPill status={health.status} message={health.message} />
    </header>
  );
}

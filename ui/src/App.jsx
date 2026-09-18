import { useEffect, useState } from "react";
import {
  Activity,
  BarChart3,
  Bot,
  Database,
  FileCheck2,
  LockKeyhole,
  ScanSearch,
  Shield,
  SlidersHorizontal,
  Sparkles,
  Upload,
} from "lucide-react";
import Header from "./components/Header";
import AuditWorkbench from "./components/AuditWorkbench";

const tabs = [
  { id: "audit", label: "Audit Workbench", icon: ScanSearch },
  { id: "attack", label: "Inversion Attack Simulator", icon: Bot },
  { id: "defense", label: "Privacy Defenses", icon: Shield },
  { id: "reports", label: "Reports & Analytics", icon: BarChart3 },
];

const stats = [
  { label: "Total vectors audited", value: "12,480", note: "+18.4% this week", icon: Database, tone: "text-emerald-300" },
  { label: "Leakage risk index", value: "18.6%", note: "Contained · −42.1%", icon: Activity, tone: "text-cyan-300" },
  { label: "Active defenses", value: "04", note: "All systems operational", icon: LockKeyhole, tone: "text-amber-200" },
];

function App() {
  const [activeTab, setActiveTab] = useState("audit");
  const [health, setHealth] = useState({ status: "checking", message: "Checking API" });

  useEffect(() => {
    let mounted = true;
    async function checkHealth() {
      try {
        const response = await fetch("http://localhost:8000/health");
        if (!response.ok) throw new Error("API unavailable");
        if (mounted) setHealth({ status: "connected", message: "API connected" });
      } catch {
        if (mounted) setHealth({ status: "disconnected", message: "API disconnected" });
      }
    }
    checkHealth();
    const interval = window.setInterval(checkHealth, 15000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const currentTab = tabs.find((tab) => tab.id === activeTab);
  const CurrentIcon = currentTab.icon;

  return (
    <div className="min-h-screen bg-transparent font-sans text-slate-100">
      <Header health={health} />
      <main className="mx-auto max-w-[1440px] px-6 py-10 lg:px-10 lg:py-14">
        <section className="mb-10 flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
          <div className="max-w-2xl">
            <div className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.2em] text-emerald-300">
              <Sparkles size={14} /> Security observatory
            </div>
            <h1 className="text-4xl font-semibold tracking-[-0.04em] text-white sm:text-6xl">Know what your vectors reveal.</h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-slate-400">Run privacy audits, simulate inversion attacks, and verify that your defenses hold when data leaves the application boundary.</p>
          </div>
          <button className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-300 px-4 py-3 text-sm font-semibold text-slate-950 shadow-[0_10px_30px_rgba(110,231,183,0.12)] transition hover:bg-emerald-200">
            <Upload size={16} /> New audit
          </button>
        </section>

        <section className="mb-10 grid gap-3 md:grid-cols-3">
          {stats.map(({ label, value, note, icon: Icon, tone }) => (
            <article key={label} className="rounded-2xl border border-white/8 bg-white/[0.035] p-5 backdrop-blur-sm">
              <div className="mb-8 flex items-start justify-between"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">{label}</span><Icon size={18} className={tone} /></div>
              <div className="flex items-end justify-between gap-4"><strong className="text-3xl font-semibold tracking-tight text-white">{value}</strong><span className="text-right text-xs text-slate-500">{note}</span></div>
            </article>
          ))}
        </section>

        <section className="overflow-hidden rounded-2xl border border-white/8 bg-[#0b1916]/80 shadow-2xl shadow-black/20">
          <nav className="flex gap-1 overflow-x-auto border-b border-white/8 p-2" aria-label="Dashboard sections">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)} className={`flex shrink-0 items-center gap-2 rounded-lg px-4 py-3 text-sm transition ${activeTab === id ? "bg-white/10 text-white" : "text-slate-500 hover:bg-white/[0.04] hover:text-slate-300"}`}>
                <Icon size={16} /> {label}
              </button>
            ))}
          </nav>
          {activeTab === "audit" ? <div className="p-6 lg:p-8"><AuditWorkbench /></div> : <div className="grid gap-8 p-6 lg:grid-cols-[1.25fr_.75fr] lg:p-8">
            <div>
              <div className="mb-7 flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-emerald-300/10 text-emerald-300"><CurrentIcon size={19} /></div><div><h2 className="text-xl font-semibold text-white">{currentTab.label}</h2><p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-500">Workspace module · ready</p></div></div>
              <div className="rounded-xl border border-dashed border-white/12 bg-black/10 p-8"><div className="mb-4 flex items-center gap-2 text-slate-400"><SlidersHorizontal size={18} /><span className="text-sm font-medium">Module workspace</span></div><p className="max-w-lg text-sm leading-6 text-slate-500">This module is connected to the Ghost Shield API foundation. The interactive controls for document upload, vector selection, attack execution, and report export land here next.</p><div className="mt-6 flex flex-wrap gap-2"><span className="rounded-md border border-emerald-300/15 bg-emerald-300/5 px-2.5 py-1.5 font-mono text-[10px] text-emerald-300">LOCAL-FIRST</span><span className="rounded-md border border-white/10 px-2.5 py-1.5 font-mono text-[10px] text-slate-500">ASYNC API</span></div></div>
            </div>
            <aside className="rounded-xl border border-white/8 bg-black/15 p-5"><div className="mb-6 flex items-center justify-between"><span className="font-mono text-[10px] uppercase tracking-[0.16em] text-slate-500">System posture</span><FileCheck2 size={17} className="text-emerald-300" /></div><div className="space-y-4">{["FAISS connector", "ChromaDB connector", "DP obfuscation", "Audit reporting"].map((item) => <div key={item} className="flex items-center justify-between text-sm"><span className="text-slate-400">{item}</span><span className="flex items-center gap-2 text-xs text-emerald-300"><i className="size-1.5 rounded-full bg-emerald-300" /> Ready</span></div>)}</div></aside>
          </div>}
        </section>
        <footer className="mt-8 flex flex-wrap justify-between gap-3 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-600"><span>Ghost Shield / Security console</span><span>Week 3 · UI foundation</span></footer>
      </main>
    </div>
  );
}

export default App;

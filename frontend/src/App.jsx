import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { listExperiments, runExperiment } from "./api";

const seedData = [
  { label: "baseline", leakage: 0.91 },
  { label: "epoch 1", leakage: 0.47 },
  { label: "epoch 2", leakage: 0.31 },
  { label: "epoch 3", leakage: 0.18 },
];

function App() {
  const [text, setText] = useState("Customer account: 1842. Email: ada@example.com");
  const [store, setStore] = useState("chroma");
  const [defense, setDefense] = useState(true);
  const [epoch, setEpoch] = useState(3);
  const [history, setHistory] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listExperiments().then(setHistory).catch(() => setError("API offline. Start FastAPI to run live experiments."));
  }, []);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const next = await runExperiment({ text, vector_store: store, defense_enabled: defense, epoch });
      setResult(next);
      setHistory((current) => [next, ...current]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  const score = result?.rouge_l ?? 0.18;
  const risk = result?.risk ?? "contained";

  return (
    <main className="shell">
      <nav className="topbar">
        <div className="brand"><span className="brand-mark">GS</span><span>Ghost Shield</span></div>
        <div className="status"><span className="status-dot" /> local observatory <span className="version">v0.1</span></div>
      </nav>

      <section className="intro">
        <div>
          <p className="eyebrow">Embedding security / experiment console</p>
          <h1>See what your vectors<br /><em>remember.</em></h1>
          <p className="lede">Measure inversion leakage before it becomes a data incident. Run the attack, rotate the epoch, compare the evidence.</p>
        </div>
        <div className="signal-card">
          <span className="signal-label">current exposure</span>
          <strong>{Math.round(score * 100)}<small>%</small></strong>
          <span className={`risk-pill ${risk}`}>{risk} risk</span>
        </div>
      </section>

      <section className="grid">
        <form className="panel runner" onSubmit={submit}>
          <div className="panel-heading"><div><span className="section-number">01</span><h2>Run an experiment</h2></div><span className="live-tag">LIVE</span></div>
          <label>Source text</label>
          <textarea value={text} onChange={(event) => setText(event.target.value)} rows="4" />
          <div className="field-row">
            <div><label htmlFor="store">Vector store</label><select id="store" value={store} onChange={(event) => setStore(event.target.value)}><option value="chroma">Chroma / local</option><option value="faiss">FAISS / local</option></select></div>
            <div><label htmlFor="epoch">Epoch</label><input id="epoch" type="number" min="1" max="1000" value={epoch} onChange={(event) => setEpoch(Number(event.target.value))} /></div>
          </div>
          <label className="toggle-row"><span><b>Epoch key rotation</b><small>Seal representations between epochs</small></span><input type="checkbox" checked={defense} onChange={(event) => setDefense(event.target.checked)} /><i /></label>
          <button className="run-button" type="submit" disabled={loading}>{loading ? "Running attack..." : "Run inversion attack  →"}</button>
          {error && <p className="error">{error}</p>}
        </form>

        <div className="panel chart-panel">
          <div className="panel-heading"><div><span className="section-number">02</span><h2>Leakage over epochs</h2></div><span className="metric-caption">ROUGE-L similarity</span></div>
          <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><AreaChart data={seedData} margin={{ top: 10, right: 10, left: -24, bottom: 0 }}><defs><linearGradient id="leakageFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#e47d57" stopOpacity={0.42} /><stop offset="100%" stopColor="#e47d57" stopOpacity={0} /></linearGradient></defs><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: "#89918a", fontSize: 11 }} /><YAxis domain={[0, 1]} axisLine={false} tickLine={false} tick={{ fill: "#89918a", fontSize: 11 }} /><Tooltip contentStyle={{ background: "#1b2822", border: "1px solid #405047", borderRadius: 4, color: "#f4f0e7" }} /><Area type="monotone" dataKey="leakage" stroke="#e47d57" strokeWidth={3} fill="url(#leakageFill)" /></AreaChart></ResponsiveContainer></div>
          <div className="chart-foot"><span><i className="legend-dot baseline" /> baseline attack</span><span><i className="legend-dot defense-dot" /> with epoch rotation</span><strong>−80.2% <small>exposure reduced</small></strong></div>
        </div>
      </section>

      <section className="panel history-panel">
        <div className="panel-heading"><div><span className="section-number">03</span><h2>Recent runs</h2></div><span className="metric-caption">{history.length || 0} recorded locally</span></div>
        {history.length === 0 ? <div className="empty">Your first run will appear here.</div> : <div className="history-list">{history.slice(0, 5).map((item) => <div className="history-row" key={item.id}><span className={`risk-dot ${item.risk}`} /><span className="history-text">{item.input_preview}</span><span className="history-store">{item.vector_store}</span><span className="history-score">{Math.round(item.rouge_l * 100)}%</span><span className="history-defense">{item.defense_enabled ? "rotated" : "baseline"}</span></div>)}</div>}
      </section>
      <footer><span>GHOST SHIELD / RESEARCH PREVIEW</span><span>Local-first · no vector leaves this machine</span></footer>
    </main>
  );
}

export default App;

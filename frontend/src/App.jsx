import { useEffect, useState } from "react";
import { deleteVector, listVectors, reportUrl, runAttack, uploadDocument } from "./api";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function App() {
  const [vectors, setVectors] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [document, setDocument] = useState(null);
  const [result, setResult] = useState(null);
  const [defense, setDefense] = useState(true);
  const [epoch, setEpoch] = useState(1);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    listVectors().then(setVectors).catch(() => {});
  }, []);

  const allSelected = vectors.length > 0 && selected.size === vectors.length;
  const riskClass = result?.risk || "waiting";
  const score = result ? Math.round(result.rouge_l * 100) : null;
  function toggleVector(id) {
    setSelected((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected(allSelected ? new Set() : new Set(vectors.map((vector) => vector.id)));
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy("upload");
    setError("");
    try {
      const response = await uploadDocument(file);
      setDocument(response.document);
      setVectors((current) => [...response.vectors, ...current]);
      setSelected(new Set(response.vectors.map((vector) => vector.id)));
      setResult(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy("");
      event.target.value = "";
    }
  }

  async function handleDelete() {
    if (!selected.size) return;
    setBusy("delete");
    setError("");
    try {
      await Promise.all([...selected].map((id) => deleteVector(id)));
      setVectors((current) => current.filter((vector) => !selected.has(vector.id)));
      setSelected(new Set());
      setResult(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy("");
    }
  }

  async function handleAttack() {
    if (!selected.size) return;
    setBusy("attack");
    setError("");
    try {
      setResult(await runAttack({ vector_ids: [...selected], defense_enabled: defense, epoch }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar"><div className="brand"><span className="brand-mark">GS</span><span>Ghost Shield</span></div><span className="system-status"><i /> local workspace</span></header>
      <section className="hero"><div><p className="eyebrow">Embedding security workbench</p><h1>Find the data<br /><em>inside the vector.</em></h1><p className="lede">Upload a source document, embed it locally, remove selected records, then measure how much an inversion attack can recover.</p></div><div className={`risk-readout ${riskClass}`}><span>leakage risk</span><strong>{score === null ? "--" : `${score}%`}</strong><small>{result ? result.risk : "run an attack to score"}</small></div></section>

      <section className="workflow">
        <div className="step-card upload-card"><div className="step-head"><span>01</span><h2>Upload document</h2></div><p>Start with a UTF-8 text file. It stays in this local API session.</p><label className={`dropzone ${busy === "upload" ? "working" : ""}`}><input type="file" accept=".txt,.md,.csv,.json,text/plain" onChange={handleUpload} disabled={busy === "upload"} /><span className="upload-icon">↑</span><b>{busy === "upload" ? "Generating embeddings..." : "Choose a document"}</b><small>TXT, MD, CSV, or JSON</small></label>{document && <div className="document-chip"><span>▤</span><div><b>{document.name}</b><small>{formatBytes(document.size)} · {document.chunk_count} embeddings</small></div></div>}</div>

        <div className="step-card vectors-card"><div className="step-head"><span>02</span><h2>Vector database</h2><span className="count-badge">{vectors.length} records</span></div><p>Generated chunks are stored as selectable local vector records.</p>{vectors.length === 0 ? <div className="empty-state">Upload a document to populate the vector store.</div> : <><div className="vector-toolbar"><label><input type="checkbox" checked={allSelected} onChange={toggleAll} /> select all</label><button type="button" className="text-button" onClick={handleDelete} disabled={!selected.size || busy === "delete"}>{busy === "delete" ? "Deleting..." : `Delete selected (${selected.size})`}</button></div><div className="vector-list">{vectors.map((vector) => <label className="vector-row" key={vector.id}><input type="checkbox" checked={selected.has(vector.id)} onChange={() => toggleVector(vector.id)} /><span className="vector-index">{String(vector.chunk_index + 1).padStart(2, "0")}</span><span className="vector-copy"><b>{vector.document_name}</b><small>{vector.text}</small></span><code>[{vector.embedding.slice(0, 3).join(", ")}...]</code></label>)}</div></>}</div>

        <div className="step-card attack-card"><div className="step-head"><span>03</span><h2>Attack simulation</h2></div><p>Try to reconstruct source text from the selected embeddings.</p><div className="control-line"><span>Epoch key rotation</span><label className="switch"><input type="checkbox" checked={defense} onChange={(event) => setDefense(event.target.checked)} /><i /></label></div><div className="epoch-line"><label htmlFor="epoch">defense epoch</label><input id="epoch" type="number" min="1" max="1000" value={epoch} onChange={(event) => setEpoch(Number(event.target.value))} /></div><button type="button" className="attack-button" onClick={handleAttack} disabled={!selected.size || busy === "attack"}>{busy === "attack" ? "Simulating..." : `Attack ${selected.size ? `${selected.size} vectors` : "selected vectors"}  →`}</button>{!selected.size && <small className="hint">Select at least one embedding to continue.</small>}</div>
      </section>

      <section className="results-grid"><div className="result-card"><div className="step-head"><span>04</span><h2>Leakage assessment</h2></div>{result ? <><div className="score-line"><strong className={riskClass}>{score}%</strong><div><b>{result.risk} exposure</b><small>ROUGE-L reconstruction similarity</small></div></div><div className="assessment-bar"><i style={{ width: `${score}%` }} /></div><div className="result-meta"><span>{result.vector_count} vectors tested</span><span>{result.defense_enabled ? `epoch ${result.epoch} rotation enabled` : "baseline attack"}</span></div><details><summary>View reconstruction output</summary><pre>{result.reconstruction}</pre></details></> : <div className="empty-state">Your leakage score will appear after the attack simulation.</div>}</div><div className="report-card"><div className="step-head"><span>05</span><h2>Download report</h2></div><p>Export the experiment inputs, reconstructed output, defense state, and score as JSON.</p><a className={`report-button ${!result ? "disabled" : ""}`} href={result ? reportUrl(result.id) : undefined} onClick={(event) => !result && event.preventDefault()}>↓ &nbsp; Download assessment</a>{error && <p className="error">{error}</p>}</div></section>
      <footer><span>GHOST SHIELD / LOCAL-FIRST MVP</span><span>Documents remain in your local session</span></footer>
    </main>
  );
}

export default App;

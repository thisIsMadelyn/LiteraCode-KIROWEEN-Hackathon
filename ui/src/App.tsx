import { useEffect, useState } from "react";
import ConflictView from "./ConflictView";
import type { Conflict } from "./types";

export default function App() {
  const [conflicts, setConflicts] = useState<Conflict[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  // Resolution text per chunk id, kept so navigating does not lose edits.
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [done, setDone] = useState<{ prose: number } | null>(null);
  const [file, setFile] = useState<string>("the file");

  useEffect(() => {
    fetch("/api/conflicts", { method: "POST" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setConflicts)
      .catch((e: Error) => setError(e.message));
    fetch("/api/file")
      .then((r) => r.json())
      .then((d) => setFile(d.name))
      .catch(() => {});
  }, []);

  /** Writes the resolution. Returns an error message, or null on success. */
  async function resolve(chunkId: string, body: string): Promise<string | null> {
    try {
      const r = await fetch("/api/resolve", {
        method: "POST",
        body: JSON.stringify({ chunk_id: chunkId, body }),
      });
      const data = await r.json();
      if (!r.ok) return data.error ?? `HTTP ${r.status}`;
      const rest = conflicts!.filter((c) => c.chunk_id !== chunkId);
      setConflicts(rest);
      setIndex(Math.min(index, Math.max(rest.length - 1, 0)));
      if (data.remaining === 0) setDone({ prose: data.prose_conflicts });
      return null;
    } catch (e) {
      return (e as Error).message;
    }
  }

  if (done)
    return (
      <div className="center">
        <div className="card">
          <div className="done-icon" aria-hidden="true">✓</div>
          <h1>All conflicts resolved.</h1>
          <p>Stage the result to finish the merge:</p>
          <div className="cmd">git add {file}</div>
          <p className="card-hint">The server stops in a few seconds.</p>
          {done.prose > 0 && (
            <p role="alert" className="alert">
              {done.prose} prose conflict(s) are still marked in the file with{" "}
              <code>&lt;&lt;&lt;&lt;&lt;&lt;&lt; ours</code>. Edit them by hand before staging.
            </p>
          )}
        </div>
      </div>
    );
  if (error)
    return (
      <div className="center">
        <p role="alert" className="alert">Could not load conflicts: {error}</p>
      </div>
    );
  if (!conflicts) return <div className="center"><p className="card-hint">Loading…</p></div>;
  if (conflicts.length === 0)
    return <div className="center"><p className="card-hint">No conflicts in this document.</p></div>;

  const current = conflicts[index];
  const draft = drafts[current.chunk_id] ?? current.ours.body;

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
        <h1 className="brand">
          <span><span className="brand-mark">lit</span> resolve</span>
          <span className="brand-file">{file}</span>
        </h1>
        <nav aria-label="Conflicts">
          <button onClick={() => setIndex(index - 1)} disabled={index === 0}>
            ← Prev
          </button>
          <span className="counter" aria-live="polite">
            Conflict {index + 1} of {conflicts.length}
          </span>
          <button onClick={() => setIndex(index + 1)} disabled={index === conflicts.length - 1}>
            Next →
          </button>
          <ul className="jump">
            {conflicts.map((c, i) => (
              <li key={c.chunk_id}>
                <button
                  className="chip"
                  onClick={() => setIndex(i)}
                  aria-current={i === index ? "true" : undefined}
                >
                  {c.chunk_id}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        </div>
      </header>
      <div className="app">
      <ConflictView
        key={current.chunk_id}
        conflict={current}
        resolution={draft}
        onResolutionChange={(v) => setDrafts({ ...drafts, [current.chunk_id]: v })}
        onResolve={() => resolve(current.chunk_id, draft)}
      />
      </div>
    </>
  );
}
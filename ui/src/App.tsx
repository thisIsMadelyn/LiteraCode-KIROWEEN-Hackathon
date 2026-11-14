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
      <div className="app">
        <h1>All conflicts resolved.</h1>
        <p>
          Run <code>git add {file}</code> to stage the result. The server stops in a few seconds.
        </p>
        {done.prose > 0 && (
          <p role="alert">
            {done.prose} prose conflict(s) are still marked in the file with{" "}
            <code>&lt;&lt;&lt;&lt;&lt;&lt;&lt; ours</code>. Edit them by hand before staging.
          </p>
        )}
      </div>
    );
  if (error) return <p role="alert">Could not load conflicts: {error}</p>;
  if (!conflicts) return <p>Loading…</p>;
  if (conflicts.length === 0) return <p>No conflicts in this document.</p>;

  const current = conflicts[index];
  const draft = drafts[current.chunk_id] ?? current.ours.body;

  return (
    <div className="app">
      <header>
        <h1>lit resolve</h1>
        <nav aria-label="Conflicts">
          <button onClick={() => setIndex(index - 1)} disabled={index === 0}>
            Prev
          </button>
          <span aria-live="polite">
            Conflict {index + 1} of {conflicts.length}
          </span>
          <button onClick={() => setIndex(index + 1)} disabled={index === conflicts.length - 1}>
            Next
          </button>
          <ul className="jump">
            {conflicts.map((c, i) => (
              <li key={c.chunk_id}>
                <button
                  onClick={() => setIndex(i)}
                  aria-current={i === index ? "true" : undefined}
                >
                  {c.chunk_id}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <ConflictView
        key={current.chunk_id}
        conflict={current}
        resolution={draft}
        onResolutionChange={(v) => setDrafts({ ...drafts, [current.chunk_id]: v })}
        onResolve={() => resolve(current.chunk_id, draft)}
      />
    </div>
  );
}
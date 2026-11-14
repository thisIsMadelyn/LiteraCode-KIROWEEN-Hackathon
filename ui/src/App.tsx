import { useEffect, useState } from "react";
import ConflictView from "./ConflictView";
import type { Conflict } from "./types";

export default function App() {
  const [conflicts, setConflicts] = useState<Conflict[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  // Resolution text per chunk id, kept so navigating does not lose edits.
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    fetch("/api/conflicts", { method: "POST" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setConflicts)
      .catch((e: Error) => setError(e.message));
  }, []);

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
      />
    </div>
  );
}
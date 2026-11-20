import { useRef, useState } from "react";
import type { Conflict, Proposal, Side } from "./types";
import { changedLines, diffLines, splitLines } from "./diff";

interface Props {
  conflict: Conflict;
  resolution: string;
  onResolutionChange: (value: string) => void;
  onResolve: () => Promise<string | null>;
}

const SUBTITLES: Record<string, string> = {
  Base: "common ancestor",
  Ours: "your branch (HEAD)",
  Theirs: "branch being merged in",
};

function Prose({ text, label }: { text: string; label: string }) {
  return (
    <pre className={text.trim() ? "prose" : "prose empty"} tabIndex={0} aria-label={label}>
      {text.trim() || "no prose"}
    </pre>
  );
}

function Column({ title, side, base }: { title: string; side: Side; base?: Side }) {
  const lines = splitLines(side.body);
  const changed = base ? changedLines(splitLines(base.body), lines) : new Set<number>();
  return (
    <section className={`column side-${title.toLowerCase()}`} aria-labelledby={`h-${title}`}>
      <div className="column-head">
        <h2 id={`h-${title}`}>{title}</h2>
        <div className="column-sub">{SUBTITLES[title]}</div>
      </div>
      <div className="column-body">
        <Prose text={side.prose_before} label={`${title}: prose before`} />
        <pre className="code" tabIndex={0} aria-label={`${title}: code`}>
          {lines.map((line, i) => (
            <span key={i} className={changed.has(i) ? "line changed" : "line"}>
              {line || " "}
              {"\n"}
            </span>
          ))}
        </pre>
        <Prose text={side.prose_after} label={`${title}: prose after`} />
      </div>
    </section>
  );
}

export default function ConflictView({
  conflict,
  resolution,
  onResolutionChange,
  onResolve,
}: Props) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  async function getProposal() {
    setLoading(true);
    setError(null);
    setProposal(null);
    try {
      const r = await fetch("/api/propose", {
        method: "POST",
        body: JSON.stringify({ chunk_id: conflict.chunk_id }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setProposal(await r.json());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function resolveNow() {
    setSaving(true);
    setSaveError(null);
    const err = await onResolve();
    if (err) {
      setSaveError(err);
      setSaving(false);
    }
  }

  // Accept and Edit are the only paths from a proposal into the resolution area.
  function accept(focus: boolean) {
    if (proposal?.proposal == null) return;
    onResolutionChange(proposal.proposal);
    setProposal(null);
    if (focus) setTimeout(() => textarea.current?.focus(), 0);
  }

  return (
    <main>
      <div className="chunk-head">
        <h2 className="chunk-title">
          Chunk <code>{conflict.chunk_id}</code>
        </h2>
        <span className="badge-conflict">edited on both sides</span>
      </div>
      <div className="columns">
        <Column title="Base" side={conflict.base} />
        <Column title="Ours" side={conflict.ours} base={conflict.base} />
        <Column title="Theirs" side={conflict.theirs} base={conflict.base} />
      </div>
      <section className="card proposal" aria-label="Agent proposal">
        <div className="card-head">
          <div>
            <h3>Agent proposal</h3>
            <p className="card-hint">Shown as a diff against Ours. Nothing is written until you press Resolve.</p>
          </div>
          <button className="btn-primary" onClick={getProposal} disabled={loading}>
            {loading ? "Asking the agent…" : "Get proposal"}
          </button>
        </div>
        {error && <p role="alert" className="alert">Could not get a proposal: {error}</p>}
        {proposal && (
          <div>
            {proposal.source === "stub" && (
              <p className="note">Offline stub, not an agent proposal. {proposal.reasoning}</p>
            )}
            {proposal.proposal === null ? (
              <p role="alert" className="alert">The agent cannot resolve this conflict. Please resolve manually.</p>
            ) : (
              <>
                <h4>Proposed change to Ours</h4>
                <pre className="code diff" tabIndex={0} aria-label="Diff of proposal against Ours">
                  {diffLines(splitLines(conflict.ours.body), splitLines(proposal.proposal)).map(
                    (l, i) => (
                      <span key={i} className={`line ${l.kind}`}>
                        {l.kind === "add" ? "+ " : l.kind === "del" ? "- " : "  "}
                        {l.text}
                        {"\n"}
                      </span>
                    ),
                  )}
                </pre>
                <div className="actions">
                  <button className="btn-primary" onClick={() => accept(false)}>Accept</button>
                  <button onClick={() => accept(true)}>Edit</button>
                  <button className="btn-danger" onClick={() => setProposal(null)}>Reject</button>
                </div>
              </>
            )}
            {proposal.source !== "stub" && (
              <>
                <h4>Reasoning{proposal.confidence ? ` (confidence: ${proposal.confidence})` : ""}</h4>
                <pre className="prose">{proposal.reasoning}</pre>
              </>
            )}
          </div>
        )}
      </section>
      <section className="card resolution">
        <label htmlFor="resolution" className="label-block">
          <span className="label-title">Resolution</span>
          <span className="card-hint">Starts as the Ours body. This is exactly what gets written.</span>
        </label>
        <textarea
          id="resolution"
          ref={textarea}
          value={resolution}
          spellCheck={false}
          rows={Math.max(6, resolution.split("\n").length + 1)}
          onChange={(e) => onResolutionChange(e.target.value)}
        />
        {saveError && <p role="alert" className="alert">Could not resolve: {saveError}</p>}
        <div className="actions end">
          <button className="btn-success" onClick={resolveNow} disabled={!resolution.trim() || saving}>
            {saving ? "Writing…" : "Resolve"}
          </button>
        </div>
      </section>
    </main>
  );
}
import type { Conflict, Side } from "./types";
import { changedLines, splitLines } from "./diff";

interface Props {
  conflict: Conflict;
  resolution: string;
  onResolutionChange: (value: string) => void;
}

function Column({ title, side, base }: { title: string; side: Side; base?: Side }) {
  const lines = splitLines(side.body);
  const changed = base ? changedLines(splitLines(base.body), lines) : new Set<number>();
  return (
    <section className="column" aria-labelledby={`h-${title}`}>
      <h2 id={`h-${title}`}>{title}</h2>
      <pre className="prose" tabIndex={0} aria-label={`${title}: prose before`}>
        {side.prose_before || "(no prose)"}
      </pre>
      <pre className="code" tabIndex={0} aria-label={`${title}: code`}>
        {lines.map((line, i) => (
          <span key={i} className={changed.has(i) ? "line changed" : "line"}>
            {line || " "}
            {"\n"}
          </span>
        ))}
      </pre>
      <pre className="prose" tabIndex={0} aria-label={`${title}: prose after`}>
        {side.prose_after || "(no prose)"}
      </pre>
    </section>
  );
}

export default function ConflictView({ conflict, resolution, onResolutionChange }: Props) {
  return (
    <main>
      <h2 className="chunk-title">
        Chunk <code>{conflict.chunk_id}</code>
      </h2>
      <div className="columns">
        <Column title="Base" side={conflict.base} />
        <Column title="Ours" side={conflict.ours} base={conflict.base} />
        <Column title="Theirs" side={conflict.theirs} base={conflict.base} />
      </div>
      <section className="resolution">
        <label htmlFor="resolution">Resolution (starts as the Ours body)</label>
        <textarea
          id="resolution"
          value={resolution}
          spellCheck={false}
          rows={Math.max(6, resolution.split("\n").length + 1)}
          onChange={(e) => onResolutionChange(e.target.value)}
        />
      </section>
    </main>
  );
}
// Line-level diff helpers. No dependency: bodies are short.

/** Lines of `side` that are not part of the longest common subsequence with `base`. */
export function changedLines(base: string[], side: string[]): Set<number> {
  const n = base.length;
  const m = side.length;
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] =
        base[i] === side[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const changed = new Set<number>();
  let i = 0;
  let j = 0;
  while (j < m) {
    if (i < n && base[i] === side[j]) {
      i++;
      j++;
    } else if (i < n && lcs[i + 1][j] >= lcs[i][j + 1]) {
      i++;
    } else {
      changed.add(j);
      j++;
    }
  }
  return changed;
}

export function splitLines(text: string): string[] {
  const lines = text.split("\n");
  if (lines[lines.length - 1] === "") lines.pop();
  return lines;
}
export interface DiffLine {
  kind: "same" | "add" | "del";
  text: string;
}

/** Line diff from `a` to `b` (LCS based). */
export function diffLines(a: string[], b: string[]): DiffLine[] {
  const n = a.length;
  const m = b.length;
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] =
        a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const out: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a[i] === b[j]) {
      out.push({ kind: "same", text: a[i] });
      i++;
      j++;
    } else if (j < m && (i === n || lcs[i][j + 1] > lcs[i + 1][j])) {
      out.push({ kind: "add", text: b[j++] });
    } else {
      out.push({ kind: "del", text: a[i++] });
    }
  }
  return out;
}

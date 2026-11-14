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
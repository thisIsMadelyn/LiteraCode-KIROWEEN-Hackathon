export interface Side {
  body: string;
  prose_before: string;
  prose_after: string;
}

export interface Conflict {
  chunk_id: string;
  lang: string;
  base: Side;
  ours: Side;
  theirs: Side;
}
export interface Proposal {
  /** null when the agent says it cannot resolve the conflict */
  proposal: string | null;
  reasoning: string;
  confidence: string;
  /** "openai" | "anthropic" | "stub" */
  source: string;
}

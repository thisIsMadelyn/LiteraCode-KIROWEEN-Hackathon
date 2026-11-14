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
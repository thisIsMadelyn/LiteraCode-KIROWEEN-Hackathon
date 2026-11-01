# task-phase3-1: `lit resolve` serves the React UI

## Status
- [ ] Done

## What this is
`lit resolve` starts a local HTTP server that serves a React app. The app reads
the conflicted document, presents each conflict for human review, and writes
resolutions back. No deployment, no auth, local only.

## Prerequisite
Phase 2 gate (Scenario A on real branches) must be passed. A conflicted
document with `lit:conflict` markers must exist to test against.

## How to execute

### 1. Project structure

```
src/
  literacode/
    resolve_server.py   ← Python HTTP server, serves the React app + API
ui/
  package.json
  src/
    App.tsx
    ConflictView.tsx
    index.tsx
  dist/                 ← built output, served by resolve_server.py
```

### 2. Bootstrap the React app

```bash
cd ui
npm create vite@latest . -- --template react-ts
npm install
```

Use Vite. No extra dependencies beyond what the conflict view needs.

### 3. Python server (`resolve_server.py`)

```python
import http.server, json, threading, webbrowser
from pathlib import Path
from .parser import parse_document
from .merge import Conflict

class ResolveHandler(http.server.SimpleHTTPRequestHandler):
    # Serve ui/dist/ for GET requests
    # POST /api/conflicts  → return list of conflicts as JSON
    # POST /api/resolve    → accept { chunk_id, body } and write to document
    ...

def serve(doc_path: Path, port: int = 7070) -> None:
    ...
    webbrowser.open(f"http://localhost:{port}")
```

### 4. Wire up the CLI

```python
def cmd_resolve(args):
    from .resolve_server import serve
    # Find the conflicted document (current directory or args.file)
    serve(Path(args.file), port=args.port)
```

`lit resolve [file.md] [--port N]`

### 5. Build step

The Python package must ship the built React app. Add a build step:
```bash
cd ui && npm run build
```
The output goes to `ui/dist/`. The server points its static file root there.

For development, Vite's dev server can proxy the API to the Python server.

### 6. Smoke test

- Start the server against a fixture conflicted document.
- `GET /` returns 200 with HTML.
- `POST /api/conflicts` returns a JSON array with the right chunk ids.

## Done when
- `lit resolve somefile.md` opens a browser tab
- The page loads without errors
- The API returns conflict data for a fixture conflicted document

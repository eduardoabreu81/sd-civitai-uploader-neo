# AGENTS.md — CivitAI Uploader Neo

> Reference for AI coding agents working on this project.

---

## Project Overview

**CivitAI Uploader Neo** is a [Stable Diffusion WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo) extension that lets users browse local generated images, compare them, and upload them as posts to CivitAI via the official CivitAI MCP server.

Key capabilities:
- Browse images in local folders (default: `outputs/`) with subfolder navigation.
- Search and filter by filename, generation metadata, model, LoRA, or local tags.
- Local tags and favorites (`#favorite` is a special tag).
- Preview images with extracted metadata (prompt, model, sampler, seed, LoRAs, etc.).
- Multi-selection with Ctrl/Cmd and Shift range selection.
- Compare two images side-by-side with metadata diff.
- Build CivitAI posts with title, description, tags, and publish/draft mode.
- Upload directly through `https://mcp.civitai.com/mcp`.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.x (Forge Neo environment) |
| UI Framework | Gradio 4.40.0+ |
| Host | Forge Neo (by Haoming02) |
| Frontend | Vanilla JavaScript + Sortable.js (drag-and-drop) |
| Styling | Custom CSS (`style.css`) |

### Python Dependencies (`requirements.txt`)
- `requests` — HTTP/JSON-RPC client for the CivitAI MCP server.
- `Pillow` — Image thumbnail generation and conversion.

### Implicit Runtime Dependencies
- `gradio` — provided by Forge Neo.
- `modules.images.read_info_from_image` — Forge Neo helper to read PNG metadata.

### External Inspiration
- Metadata parsing is inspired by [Infinite Image Browsing](https://github.com/zanllp/infinite-image-browsing).

## Project Structure

```
sd-civitai-uploader-neo/
├── install.py                       # Forge dependency-install hook
├── requirements.txt                 # Python dependencies
├── README.md                        # Public user-facing documentation
├── AGENTS.md                        # This file
├── style.css                        # UI styles
├── javascript/
│   ├── Sortable.min.js              # Drag-and-drop library
│   └── civitai-gallery.js           # Frontend logic
├── scripts/                         # Python backend (loaded as Forge extension)
│   ├── civitai_gallery_gui.py       # Gradio UI definition and callbacks
│   ├── civitai_gallery_api.py       # CivitAI MCP client
│   ├── civitai_gallery_meta.py      # PNG metadata extraction and diff
│   ├── civitai_gallery_tags.py      # Local tags and favorites
│   └── civitai_gallery_utils.py     # Filesystem, thumbnails, filters
└── config_states/                   # Runtime state (gitignored)
    ├── gallery_defaults.json
    ├── gallery_tags.json
    └── thumbnails/
```

## Code Style Guidelines

### Language
- **Code, comments, docstrings, and commits:** English
- **Private chat / local docs:** Brazilian Portuguese

### Commit Convention
```
type(scope): short description

Types: feat | fix | chore | refactor | docs | test
Scope : python | js | css | readme
```

### Python Conventions
- Import order: (1) stdlib, (2) third-party, (3) WebUI (`modules.*`), (4) extension (`scripts.*`)
- Use `pathlib.Path` for new path handling.
- Keep functions focused and small.

### JavaScript Conventions
- Vanilla JS only; no frameworks besides Sortable.js.
- Use `gradioApp().querySelector(...)` to reach Gradio-generated DOM nodes.
- Dispatch both `input` and `change` events when syncing hidden textboxes.

## Security Considerations

- The CivitAI API key is read from Forge settings (`opts.civitai_gallery_api_key`).
- Never log the full API key.
- Uploaded images are sent directly to CivitAI; no intermediary server.
- Respect user folder selection; never scan outside the chosen directory tree without explicit action.

## Runtime Artifacts (never commit)

- `config_states/` — local settings, tags, favorites and thumbnail cache.

## Useful References

- `README.md` — public features, changelog, roadmap
- `docs/PROJECT_CONTEXT.md` — architecture handoff and sensitive points
- `docs/PROJECT_LOG.md` — dev timeline and decisions
- `scripts/civitai_gallery_api.py` — MCP client and schemas
- `scripts/civitai_gallery_meta.py` — metadata extraction
- `scripts/civitai_gallery_tags.py` — local tags/favorites
- `scripts/civitai_gallery_utils.py` — filesystem and thumbnails
- `scripts/civitai_gallery_gui.py` — Gradio UI and callbacks

---

**Last updated:** 2026-06-15

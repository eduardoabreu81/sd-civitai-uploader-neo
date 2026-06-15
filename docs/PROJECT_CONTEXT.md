# PROJECT_CONTEXT.md — CivitAI Uploader Neo

> Architecture handoff and sensitive points for AI agents.

---

## Identity

- **Name:** CivitAI Uploader Neo
- **Purpose:** Let Forge Neo users browse local generated images and upload them as posts to CivitAI via the official MCP server.
- **Stack:** Python 3.x, Gradio 4.40.0+, Vanilla JS, Sortable.js
- **Host:** Stable Diffusion WebUI Forge Neo
- **Repo:** https://github.com/eduardoabreu81/sd-civitai-uploader-neo

---

## Critical Invariants

1. **Gradio 4+ only.** Never use Gradio 3 APIs.
2. **MCP schemas are authoritative.** Always validate against real schemas via `node mcp-cli.mjs schema <tool>` before changing upload/post logic.
3. **20 images per post maximum.** Enforced in both JS and Python.
4. **Never commit runtime artifacts:** `config_states/`, `__pycache__/`, thumbnails.
5. **API key never logged.** It is read from Forge settings only.

---

## Architecture Snapshot

### Components
- `civitai_gallery_gui.py` — Gradio UI, event bindings, HTML rendering.
- `civitai_gallery_api.py` — MCP JSON-RPC client.
- `civitai_gallery_meta.py` — PNG metadata extraction and diff.
- `civitai_gallery_tags.py` — Local tags/favorites persistence.
- `civitai_gallery_utils.py` — Filesystem, thumbnails, filters.
- `civitai-gallery.js` — Frontend selection, preview, drag-drop.
- `style.css` — UI styling.

### Data Flow
```
User UI (Gradio + JS)
    ↓
civitai_gallery_gui.py
    ↓
civitai_gallery_utils.py  →  thumbnails + file scan
    ↓
civitai_gallery_meta.py   →  metadata extraction
    ↓
civitai_gallery_api.py    →  upload_image → create_post (CivitAI MCP)
```

### Fragile Dependencies
- `modules.images.read_info_from_image` from Forge Neo.
- CivitAI MCP server schemas (can change).
- Gradio 4 component DOM structure (affects JS selectors).

---

## State Management

- **Selection:** stored in browser `localStorage` and synced to a hidden Gradio textbox (`#civitai_gallery_selected_sync`).
- **Folder/filters:** persisted in `config_states/gallery_defaults.json`.
- **Tags/favorites:** persisted in `config_states/gallery_tags.json`.
- **Thumbnails:** cached in `config_states/thumbnails/`.

---

## Warnings / Sensitive Points

- The JS relies on `gradioApp().querySelector(...)` for hidden sync inputs. If Gradio's DOM changes, interactions may break.
- Preview on hover triggers Python callbacks; debounced at 150 ms.
- Favorite toggle re-renders the browser HTML and relies on `MutationObserver` to restore selection visuals.
- Sortable.js drag-and-drop is initialized lazily when the selected list appears in the DOM.

---

# docs/PROJECT_LOG.md — CivitAI Uploader Neo

> Internal development timeline and decisions. **Never commit.**

---

## Scope

**CivitAI Uploader Neo** — Forge Neo extension for browsing, comparing and uploading generated images to CivitAI via the official MCP server (`https://mcp.civitai.com/mcp`).

- Stack: Python 3.x, Gradio 4.40.0+, Vanilla JS, Sortable.js
- Host: Stable Diffusion WebUI Forge Neo
- Repo: https://github.com/eduardoabreu81/sd-civitai-uploader-neo
- Current version: **v0.1.0**

---

## Quick State

| Item | Detail |
|---|---|
| **UI** | 3-column Gradio tab: Gallery / Compare |
| **Upload flow** | `upload_image` (base64) → `create_post` (draft or publish) |
| **Selection** | Multi-select with Ctrl/Cmd/Shift, drag-and-drop reorder |
| **Metadata** | PNG parameters parsed; shown in preview and detail auto-fill |
| **Limits** | 20 images/post, 10 MB/image |
| **Auth** | Forge setting `civitai_gallery_api_key` |
| **Status** | Real uploads tested successfully; ready for Forge Neo integration tests |

---

## Timeline

### 2026-06-15 — Real-World MCP Validation & Model Association Discovery

**What changed:**
- Validated end-to-end upload with real CivitAI account (`tripledamn`).
- Confirmed `upload_image` + `create_post` create draft posts successfully.
- Discovered that **MCP does NOT extract generation metadata** (prompt, sampler, seed, resources) automatically, even when the raw PNG contains `parameters`.
- Confirmed that **`modelVersionId` in `create_post` correctly associates the post with a checkpoint** (e.g. `samANIMA_turboV16` → `modelVersionId: 2907101`).
- Tested sending prompt tokens as `tags`; they are accepted but not a good UX.
- Added **user status badge** in the UI (`whoami` → `👤 username`), loaded on tab open.

**Files changed:**
- `scripts/civitai_gallery_gui.py` — `_get_user_status()`, `user_status_html`, `interface.load(...)`.
- `style.css` — `.civitai-user-badge` styles.

**Decisions:**
- Generation metadata will be placed in the post `detail` field as formatted text, since MCP has no structured metadata field.
- `modelVersionId` association will be implemented via a **hybrid resolver**:
  1. Read `Model:` from image metadata.
  2. Look up the local checkpoint file.
  3. Try Browser Neo cache (`lib/models/checkpoint_hashes.json`) first.
  4. Fall back to SHA256 hash + `https://civitai.com/api/v1/model-versions/by-hash/{hash}`.
  5. Cache results locally to avoid re-hashing large files.
- `.gitignore` updated to exclude `docs/` and `AGENTS.local.md` (project-init pattern).

**Next steps:**
1. Implement `civitai_gallery_model_resolver.py` (Browser Neo cache + SHA256 fallback).
2. Wire `modelVersionId` into `create_post`.
3. Format and inject generation metadata into `detail`.
4. Test full flow inside Forge Neo.

---

### 2026-06-15 — v0.1.0 Initial Release

**What was done:**
- Created extension structure for Forge Neo (Gradio 4.40.0+).
- Implemented CivitAI MCP client (`scripts/civitai_gallery_api.py`):
  - `upload_image` using base64 `data` + `contentType`.
  - `create_post` using `title`, `detail`, `images[].uuid`, `tags`, `publish`.
  - `get_post` to retrieve canonical post URL after creation.
  - `whoami` for auth/onboarding validation.
- Implemented metadata parser (`scripts/civitai_gallery_meta.py`):
  - Reads PNG info, EXIF or `.txt` sidecar.
  - Extracts prompt tags, LoRAs, LyCORIS and generation specs.
  - Metadata diff for compare mode.
- Implemented local tags/favorites system (`scripts/civitai_gallery_tags.py`).
- Implemented filesystem utilities (`scripts/civitai_gallery_utils.py`):
  - Folder scanning, thumbnail caching, filtering.
- Implemented 3-column Gradio UI (`scripts/civitai_gallery_gui.py`):
  - Gallery tab: sources, filters, preview, metadata, post editor.
  - Compare tab: side-by-side images + metadata diff.
- Implemented frontend logic (`javascript/civitai-gallery.js`):
  - Multi-selection (click, Ctrl/Cmd, Shift).
  - Hover preview, favorite toggle, tag filtering.
  - Drag-and-drop reordering with Sortable.js.
- Enforced 20 images per post limit in JS and Python.
- Styled with custom CSS (`style.css`).
- Published to GitHub: `https://github.com/eduardoabreu81/sd-civitai-uploader-neo`.

**Key decisions:**
- Use the **hosted CivitAI MCP server** (`https://mcp.civitai.com/mcp`) instead of self-hosting, to avoid Node dependencies for end users.
- Use **local tags** where `#favorite` is a special tag, inspired by Infinite Image Browsing.
- Keep scheduling/NSFW out of the UI because the current MCP `create_post` schema does not support them.
- Use base64 inline thumbnails to avoid relying on Forge's file serving for previews.

---

## Backlog

| Item | Status | Notes |
|---|---|---|
| Real Forge Neo loading test | 🚧 | UI built, needs integration test |
| `modelVersionId` auto-resolution | 🚧 | Browser Neo cache + SHA256 fallback planned |
| Generation metadata in `detail` | 🚧 | Workaround for MCP missing structured metadata |
| Video upload support | ⏳ | MCP schema supports `type: video`; needs testing |
| Bulk local tag management | ⏳ | Add/remove tags to multiple images |
| Keyboard shortcuts | ⏳ | Arrow navigation, delete, favorite |
| Scheduled publishing | ⏳ | Blocked by CivitAI MCP limitations |
| NSFW flag on posts | ⏳ | Blocked by CivitAI MCP limitations |

---

## Observations to Avoid Drift

- **MCP `create_post` schema is minimal:** only `title`, `detail`, `images`, `tags`, `modelVersionId`, `collectionId`, `publish`. No metadata, no NSFW flag, no scheduling.
- **Upload raw PNG does not trigger CivitAI metadata extraction.** The site upload pipeline is different from the MCP pipeline.
- **20 images per post is a hard CivitAI limit.** Enforce in JS and Python.
- **API key never logged.** Read only from `opts.civitai_gallery_api_key`.
- **Do not commit runtime artifacts:** `config_states/`, `docs/`, `AGENTS.local.md`.

# PROJECT_LOG.md — CivitAI Uploader Neo

> Internal development timeline and decisions.

---

## 2026-06-15 — v0.1.0 Initial Release

### What was done
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

### Key decisions
- Use the **hosted CivitAI MCP server** (`https://mcp.civitai.com/mcp`) instead of self-hosting, to avoid Node dependencies for end users.
- Use **local tags** where `#favorite` is a special tag, inspired by Infinite Image Browsing.
- Keep scheduling/NSFW out of the UI because the current MCP `create_post` schema does not support them.
- Use base64 inline thumbnails to avoid relying on Forge's file serving for previews.

### Next steps
1. Test extension in Forge Neo and fix Gradio 4-specific issues.
2. Verify upload/post flow with a real CivitAI API key.
3. Add video support if requested.
4. Add keyboard shortcuts after initial UX feedback.

---

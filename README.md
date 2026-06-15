# 📤 CivitAI Uploader Neo

[![Forge Neo](https://img.shields.io/badge/Forge-Neo-blue)](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo)
[![Gradio](https://img.shields.io/badge/Gradio-4.40.0-orange)](https://gradio.app/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Extension for [Stable Diffusion WebUI Forge - Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo)**

Browse, compare, and upload your generated images directly to CivitAI from inside Forge Neo — with metadata-aware captions, drag-and-drop curation, and one-click posting via the official CivitAI MCP server.

---

## 📋 Table of Contents

- [What's New](#-whats-new)
- [Changelog](#-changelog)
- [Roadmap](#️-roadmap)
- [Features](#-features)
- [Installation](#-installation)
- [Setup](#-setup)
- [Usage](#-usage)
- [Known Limitations](#-known-limitations)
- [Credits](#-credits)

---

## 🆕 What's New

### v0.1.0 — Initial Release: Browse, Compare & Upload

- **3-column gallery UI** — Sources, preview/metadata, and post editor in one tab.
- **Smart local browser** — Scan any folder with subfolder navigation, search by filename or generation metadata.
- **Multi-selection** — Click, Ctrl/Cmd, Shift range selection, and drag-and-drop reordering.
- **Compare mode** — Side-by-side view with highlighted metadata differences.
- **Auto-fill post details** — Title, description and tags suggested from the first selected image.
- **Direct CivitAI upload** — Posts created through the official MCP server (`https://mcp.civitai.com/mcp`).
- **User status badge** — Shows the connected CivitAI account at the top of the tab.
- **20 images per post limit** enforced in the UI and backend.
- **Resize before upload** to stay under CivitAI's 10 MB image cap.

---

## 📖 Changelog

### v0.1.0 — Initial Release
- Created extension structure for Forge Neo / Gradio 4.40.0+.
- Implemented CivitAI MCP JSON-RPC client (`scripts/civitai_gallery_api.py`):
  - `upload_image` via base64 PNG.
  - `create_post` with title, detail, tags, images and publish/draft mode.
  - `get_post` to retrieve the canonical post URL.
  - `whoami` for auth and onboarding validation.
- Implemented PNG metadata extraction (`scripts/civitai_gallery_meta.py`):
  - Reads PNG `parameters`, EXIF, or `.txt` sidecar.
  - Extracts prompt tags, negative prompt, model, sampler, steps, CFG, seed, size and LoRAs.
  - Metadata diff for compare mode.
- Implemented local tags/favorites system (`scripts/civitai_gallery_tags.py`).
- Implemented filesystem utilities (`scripts/civitai_gallery_utils.py`):
  - Recursive folder scanning, thumbnail cache, filtering and sorting.
- Implemented Gradio UI (`scripts/civitai_gallery_gui.py`):
  - Gallery tab with sources, filters, preview, metadata and post editor.
  - Compare tab for two-image side-by-side review.
- Implemented vanilla JS frontend (`javascript/civitai-gallery.js`):
  - Selection, hover preview, favorite toggle, tag filtering, drag-and-drop reordering.
- Added custom CSS (`style.css`).

---

## 🗺️ Roadmap

### v0.2.0 — Model Association & Metadata Polish *(planned)*
- Associate posts with the generation checkpoint via `modelVersionId` when possible.
- Inject formatted generation metadata into the post description as a fallback for missing MCP auto-extraction.
- Cache checkpoint hashes to avoid re-hashing large files.

### v0.3.0 — Curation & Bulk Tools *(planned)*
- Bulk add/remove local tags.
- Saved search presets.
- Keyboard shortcuts (arrow navigation, delete, favorite).

### v0.4.0 — Media & Scheduling *(planned)*
- Video upload support (if CivitAI MCP stabilizes `type: video`).
- Scheduled publishing (if CivitAI MCP adds support).

### v1.0.0 — First Stable Release *(planned)*
- All known issues resolved.
- Full Forge Neo compatibility guarantee.

---

## 🎯 Features

### 🖼️ Local Image Browser
- Scan any folder (defaults to `outputs/`) with subfolder navigation.
- Thumbnail grid with adjustable tile size.
- Sort by date, name or file size.

### 🔍 Smart Search & Filters
- Search by **filename** or inside **generation metadata**.
- Filter by **local tags** (e.g. `#favorite`, `#post-later`).
- Filter by **favorites** only.
- Extracted model, sampler, LoRA and prompt tags are all searchable.

### 🖼️ Preview & Metadata
- Large preview panel updated on hover.
- Full generation metadata: prompt, negative prompt, model, model hash, sampler, steps, CFG, seed, size and LoRAs.
- Metadata parsing inspired by [Infinite Image Browsing](https://github.com/zanllp/infinite-image-browsing).

### ☑️ Powerful Selection
- **Click** to toggle selection.
- **Ctrl/Cmd + click** for multi-select.
- **Shift + click** for range selection.
- Limit of **20 images per post** (CivitAI cap), enforced in UI and backend.

### 🏷️ Local Tags & Favorites
- Mark images with local tags.
- **Favorite** = special `#favorite` tag.
- Tag cloud shows all tags used and filters on click.

### 🆚 Compare Mode
- Select exactly **2 images** and open the Compare tab.
- Side-by-side view with **highlighted metadata differences**.
- Quickly choose which variant to post.

### 📝 Post Editor
- Title and description (Markdown / HTML supported).
- CivitAI tags with auto-suggestion from metadata.
- Publish immediately or save as **draft**.
- Optional resize before upload to stay under CivitAI's 10 MB limit.

### 👤 Account Badge
- Shows the connected CivitAI username at the top of the tab.
- Validates onboarding status before posting.

### 🔐 Secure Upload
- Uses the official CivitAI MCP server at `https://mcp.civitai.com/mcp`.
- Your CivitAI API key is stored in Forge Neo settings.
- Images are uploaded directly from your machine to CivitAI.

---

## 📦 Installation

1. Open Forge Neo.
2. Go to **Extensions** → **Install from URL**.
3. Paste:
   ```
   https://github.com/eduardoabreu81/sd-civitai-uploader-neo
   ```
4. Click **Install** and restart Forge Neo.

> ⚠️ This extension requires **Forge Neo**.

---

## 🔑 Setup

1. Create a CivitAI API key at [civitai.com/user/account](https://civitai.com/user/account).
2. In Forge Neo, go to **Settings** → **CivitAI Uploader Neo**.
3. Paste your API key.
4. Restart the UI.

> **Note:** The API key must have write access. Use a **Full key** or a scoped key with `MediaWrite` permission.

---

## 🖱️ Usage

1. Open the **CivitAI Gallery** tab.
2. Set the image folder and click **🔄 Scan**.
3. Select images:
   - **Click** to toggle.
   - **Ctrl/Cmd + click** to add/remove individual images.
   - **Shift + click** to select a range.
4. Hover images to preview and inspect metadata.
5. Click the **⭐** on a card to mark it as favorite.
6. On the right panel, fill the title, description and CivitAI tags.
   - Tip: click **✨ Auto-fill from first image** to pre-populate from metadata.
7. Choose **Publish now** or **Save as draft**.
8. Click **🚀 Post**.

### Compare Mode

1. Select exactly **2 images** in the Gallery tab.
2. Switch to the **🆚 Compare** tab.
3. Review the images and the metadata diff table.
4. Click **🚀 Post this one** on the image you want to upload.

---

## ⚠️ Known Limitations

- **20 images per post** — hard cap from CivitAI.
- **10 MB per image** — enforced by the CivitAI MCP server. Use the resize slider if needed.
- **No built-in scheduling** — the MCP server supports only `publish now` or `save as draft`.
- **No NSFW flag on posts** — the current MCP `create_post` schema does not expose this field.
- **Generation metadata is not extracted automatically** — the MCP upload pipeline does not read PNG metadata. The extension includes generation info in the post description as a workaround.
- **Videos** are not supported yet; only static images (PNG, JPG, WEBP, GIF, BMP).

---

## 📄 Credits

- **[Infinite Image Browsing](https://github.com/zanllp/infinite-image-browsing)** — metadata parsing inspiration.
- **[Sortable.js](https://sortablejs.github.io/Sortable/)** — drag-and-drop reordering.
- **[Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo)** by Haoming02 — host WebUI.

---

## 📜 License

MIT — see [LICENSE](LICENSE)

---

Made with ❤️ for the Stable Diffusion community

**[Report Bug](https://github.com/eduardoabreu81/sd-civitai-uploader-neo/issues)** • **[Request Feature](https://github.com/eduardoabreu81/sd-civitai-uploader-neo/issues)** • **[Discussions](https://github.com/eduardoabreu81/sd-civitai-uploader-neo/discussions)**

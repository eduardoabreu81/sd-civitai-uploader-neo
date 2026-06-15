# CivitAI Uploader Neo

[![Forge Neo](https://img.shields.io/badge/Forge%20Neo-compatible-blue)](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo)
[![Gradio](https://img.shields.io/badge/Gradio-4.40%2B-orange)](https://gradio.app)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A [Stable Diffusion WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo) extension that lets you **browse, compare and upload** your generated images directly to **CivitAI** — without leaving the WebUI.

Built for power users who generate dozens of images and want a fast, visual workflow to curate and post the best ones.

---

## 🚀 Features

### 🗂️ Local Image Browser
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

### 🔐 Secure Upload
- Uses the official CivitAI MCP server at `https://mcp.civitai.com/mcp`.
- Your CivitAI API key is stored in Forge Neo settings.
- Images are uploaded directly from your machine to CivitAI.

### 👤 Account Badge
- Shows the connected CivitAI username at the top of the tab.
- Validates onboarding status before posting.

---

## 📋 Requirements

- [Stable Diffusion WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo)
- Gradio 4.40.0+
- CivitAI account with API key
- Completed CivitAI onboarding

---

## 📦 Installation

### Via Extensions UI (recommended)

1. Open Forge Neo.
2. Go to **Extensions** → **Install from URL**.
3. Paste:
   ```
   https://github.com/eduardoabreu81/sd-civitai-uploader-neo
   ```
4. Click **Install** and restart Forge Neo.

### Manual

```bash
cd extensions/
git clone https://github.com/eduardoabreu81/sd-civitai-uploader-neo.git
```

Then restart Forge Neo.

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
- **Generation metadata is not extracted automatically** — the MCP upload pipeline does not read PNG metadata. The extension will include generation info in the post description as a workaround.
- **Videos** are not supported yet; only static images (PNG, JPG, WEBP, GIF, BMP).

---

## 🗺️ Roadmap

- [ ] Video upload support (MP4, WEBM, GIF as video).
- [ ] Bulk add/remove local tags.
- [ ] Keyboard shortcuts (arrow navigation, delete, favorite).
- [x] Integration with CivitAI model resources from metadata (modelVersionId association planned).
- [ ] Auto-publish drafts at a scheduled time (if CivitAI MCP adds support).

---

## 📝 Changelog

### v0.1.0 (2026-06-15)
- Initial release.
- 3-column gallery UI with preview, metadata and post editor.
- Multi-selection, local tags, favorites and compare mode.
- Direct upload to CivitAI via MCP server.
- 20 images per post limit and 10 MB image size handling.

---

## 📄 License

MIT

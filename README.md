# CivitAI Uploader Neo

A [Stable Diffusion WebUI Forge Neo](https://github.com/Haoming02/sd-webui-forge-classic/tree/neo) extension that lets you browse, compare and upload your generated images directly to CivitAI — without leaving the WebUI.

## Features

- 🗂️ **Local image browser** — scan any folder (defaults to `outputs/`) with subfolder navigation.
- 🔍 **Smart search & filters** — search by filename, metadata, model, LoRA, or local tags.
- 🏷️ **Local tags & favorites** — tag images locally (`#favorite`, `#post-later`, etc.) and filter by them.
- 🖼️ **Preview + metadata** — large preview with extracted generation info (prompt, model, sampler, seed, LoRAs, etc.).
- ☑️ **Multi-selection** — Ctrl/Cmd click, Shift+click range selection, click to toggle.
- 🆚 **Compare mode** — compare two images side-by-side with highlighted metadata differences.
- 📝 **Post editor** — title, description, tags, NSFW flag.
- 📅 **Scheduling** — publish now, schedule a date/time, or save as draft.
- 🚀 **Direct upload** — posts to CivitAI through the official `civitai-mcp-server` hosted endpoint.

## Requirements

- Forge Neo (Gradio 4.40.0+)
- CivitAI account with API key
- Completed CivitAI onboarding

## Installation

1. Open Forge Neo.
2. Go to **Extensions** → **Install from URL**.
3. Paste `https://github.com/eduardoabreu81/sd-civitai-uploader-neo` (or clone into `extensions/sd-civitai-uploader-neo` manually).
4. Restart Forge Neo.

## Setup

1. Go to **Settings** → **CivitAI Gallery Uploader**.
2. Paste your CivitAI API key.
3. Restart the UI if needed.

You can create an API key at [civitai.com/user/account](https://civitai.com/user/account).

## Usage

1. Open the **CivitAI Gallery** tab.
2. Set the image folder and click **Scan**.
3. Click images to select them (Ctrl/Cmd for multi, Shift for range).
4. Hover images to preview and see metadata.
5. Click the ⭐ to mark favorites.
6. Edit title, description, tags, schedule on the right panel.
7. Click **🚀 Post** to upload to CivitAI.

### Compare mode

1. Select exactly **2 images** in the Gallery tab.
2. Open the **🆚 Compare** tab.
3. Review the images side-by-side with metadata differences highlighted.
4. Click **Post this one** on the image you want to upload.

## Notes

- Uploads use the official CivitAI MCP server at `https://mcp.civitai.com/mcp`.
- The CivitAI API key must have write access (`MediaWrite` scope or a Full key).
- Large images can be resized before upload using the slider.
- Metadata parsing is inspired by [Infinite Image Browsing](https://github.com/zanllp/infinite-image-browsing).

## License

MIT

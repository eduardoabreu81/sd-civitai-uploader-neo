import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import gradio as gr

# === WebUI imports ===
from modules import script_callbacks, shared
from modules.shared import opts
from modules.paths import data_path

# === Extension imports ===
from . import civitai_gallery_api as _api
from . import civitai_gallery_meta as _meta
from . import civitai_gallery_tags as _tags
from . import civitai_gallery_utils as _utils


_EXT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULTS_PATH = _EXT_ROOT / 'config_states' / 'gallery_defaults.json'


def _load_defaults() -> Dict[str, Any]:
    try:
        with open(_DEFAULTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_defaults(data: Dict[str, Any]) -> None:
    _DEFAULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DEFAULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def _default_image_folder() -> str:
    defaults = _load_defaults()
    if defaults.get('image_folder'):
        return defaults['image_folder']
    outputs = Path(data_path) / 'outputs'
    if outputs.exists():
        return str(outputs)
    return str(data_path)


# ─────────────────────────────────────────────────────────────────────────────
# HTML Renderers
# ─────────────────────────────────────────────────────────────────────────────

def _render_browser_html(
    images: List[str],
    tile_size: int,
    selected: List[str],
    preview_path: Optional[str] = None,
    favorites: Optional[set] = None,
) -> str:
    if not images:
        return '<div class="gallery-empty">No images found. Try another folder or filter.</div>'

    selected_set = set(selected)
    fav_set = favorites if favorites is not None else _tags.get_images_with_tag('favorite')
    rows = ['<div class="gallery-grid">']
    for path in images:
        thumb_url = _utils.thumbnail_to_base64(path, tile_size)
        if not thumb_url:
            continue
        safe_path = html.escape(path)
        filename = html.escape(Path(path).name)
        file_size = _utils.format_file_size(path)
        is_selected = path in selected_set
        is_preview = path == preview_path
        is_fav = _tags._normalize_path(path) in fav_set

        rows.append(
            f'<div class="gallery-card {"selected" if is_selected else ""} {"preview" if is_preview else ""}" '
            f'     data-path="{safe_path}" '
            f'     onclick="handleGalleryCardClick(event, this)">'
            f'  <img src="{thumb_url}" loading="lazy" alt="{filename}">'
            f'  <div class="gallery-card-overlay">'
            f'    <span class="gallery-fav-star {"active" if is_fav else ""}" onclick="toggleGalleryFav(event, this)">★</span>'
            f'    <span class="gallery-card-check">&#10003;</span>'
            f'  </div>'
            f'  <div class="gallery-card-info">{filename}<br><small>{file_size}</small></div>'
            f'</div>'
        )
    rows.append('</div>')
    return '\n'.join(rows)


def _render_sources_html(folder: str) -> str:
    subfolders = _utils.discover_subfolders(folder)
    rows = ['<div class="gallery-sources">']
    rows.append(
        f'<div class="gallery-source-item active" data-path="{html.escape(folder)}" '
        f'onclick="selectGallerySource(this)">📁 {html.escape(Path(folder).name or folder)}</div>'
    )
    for sub in subfolders:
        name = Path(sub).name
        rows.append(
            f'<div class="gallery-source-item" data-path="{html.escape(sub)}" '
            f'onclick="selectGallerySource(this)">├─ {html.escape(name)}</div>'
        )
    rows.append('</div>')
    return '\n'.join(rows)


def _render_tags_cloud() -> str:
    tags = _tags.get_all_tags()
    if not tags:
        return '<div class="gallery-tags-empty">No tags yet. Click the star on images to add favorites.</div>'

    rows = ['<div class="gallery-tags-cloud">']
    for tag in tags:
        label = f'#{tag}'
        rows.append(
            f'<span class="gallery-tag-chip" data-tag="{html.escape(tag)}" '
            f'onclick="filterGalleryByTag(this)">{html.escape(label)}</span>'
        )
    rows.append('</div>')
    return '\n'.join(rows)


MAX_IMAGES_PER_POST = 20


def _render_selected_html(selected_paths: List[str], tile_size: int) -> str:
    count = len(selected_paths)
    if not selected_paths:
        return '<div class="gallery-empty">No images selected.<br>Click images in the gallery to select them.</div>'

    header = (
        f'<div class="gallery-selected-header">'
        f'<span>Selected ({count}/{MAX_IMAGES_PER_POST})</span>'
        f'<button type="button" class="gallery-clear-btn" onclick="clearGallerySelection()">Clear</button>'
        f'</div>'
    )
    rows = [header, '<div class="gallery-selected-list" id="gallery-selected-list">']
    for idx, path in enumerate(selected_paths, 1):
        thumb_url = _utils.thumbnail_to_base64(path, tile_size)
        if not thumb_url:
            continue
        safe_path = html.escape(path)
        filename = html.escape(Path(path).name)
        rows.append(
            f'<div class="gallery-selected-item" data-path="{safe_path}">'
            f'  <span class="gallery-selected-index">{idx}</span>'
            f'  <img src="{thumb_url}" alt="{filename}">'
            f'  <span class="gallery-selected-name">{filename}</span>'
            f'  <button type="button" class="gallery-remove-btn" onclick="removeGallerySelection(this)">&#10005;</button>'
            f'</div>'
        )
    rows.append('</div>')
    return '\n'.join(rows)


def _render_metadata_html(metadata: Dict[str, Any]) -> str:
    meta = metadata.get('meta', {})
    pos_prompt = metadata.get('pos_prompt', [])
    neg_prompt = metadata.get('neg_prompt', '')
    loras = metadata.get('loras', [])

    rows = ['<div class="gallery-metadata">']

    if pos_prompt:
        tags_html = ' '.join(f'<span class="gallery-meta-tag">{html.escape(t)}</span>' for t in pos_prompt[:30])
        if len(pos_prompt) > 30:
            tags_html += f' <span class="gallery-meta-more">+{len(pos_prompt) - 30} more</span>'
        rows.append(
            f'<div class="gallery-meta-section"><h4>Prompt tags</h4>'
            f'<div class="gallery-meta-tags">{tags_html}</div></div>'
        )

    if neg_prompt:
        rows.append(
            f'<div class="gallery-meta-section"><h4>Negative prompt</h4>'
            f'<div class="gallery-meta-text">{html.escape(neg_prompt)}</div></div>'
        )

    fields = [
        ('Model', 'Model'),
        ('Model hash', 'Model hash'),
        ('Sampler', 'Sampler'),
        ('Schedule type', 'Schedule type'),
        ('CFG scale', 'CFG scale'),
        ('Steps', 'Steps'),
        ('Seed', 'Seed'),
        ('Size', 'Size'),
    ]
    specs = []
    for label, key in fields:
        value = meta.get(key)
        if value:
            specs.append(
                f'<div class="gallery-meta-spec"><span>{html.escape(label)}</span>'
                f'<strong>{html.escape(str(value))}</strong></div>'
            )
    if specs:
        rows.append(
            f'<div class="gallery-meta-section"><h4>Generation specs</h4>'
            f'<div class="gallery-meta-specs">{"".join(specs)}</div></div>'
        )

    if loras:
        lora_html = ' '.join(f'<span class="gallery-meta-lora">{html.escape(l)}</span>' for l in loras)
        rows.append(
            f'<div class="gallery-meta-section"><h4>LoRAs</h4>'
            f'<div class="gallery-meta-loras">{lora_html}</div></div>'
        )

    rows.append('</div>')
    return '\n'.join(rows)


def _render_compare_html(path_a: str, path_b: str) -> str:
    img_a = _utils.image_to_data_url(path_a, max_size=1024)
    img_b = _utils.image_to_data_url(path_b, max_size=1024)
    meta_a = _meta.extract_metadata(path_a)
    meta_b = _meta.extract_metadata(path_b)
    diff = _meta.compute_metadata_diff(meta_a, meta_b, ignore_seed=False)

    rows = ['<div class="gallery-compare">']
    rows.append('<div class="gallery-compare-images">')
    rows.append(
        f'<div class="gallery-compare-side">'
        f'<img src="{img_a or ""}" alt="A">'
        f'<button type="button" class="gallery-compare-post-btn" onclick="postCompareSide(\'left\')">🚀 Post this one</button>'
        f'</div>'
    )
    rows.append(
        f'<div class="gallery-compare-side">'
        f'<img src="{img_b or ""}" alt="B">'
        f'<button type="button" class="gallery-compare-post-btn" onclick="postCompareSide(\'right\')">🚀 Post this one</button>'
        f'</div>'
    )
    rows.append('</div>')

    rows.append('<div class="gallery-compare-diff">')
    rows.append('<h4>Differences</h4>')
    if not diff:
        rows.append('<p>Images have identical generation metadata.</p>')
    else:
        rows.append('<table class="gallery-diff-table">')
        rows.append('<tr><th>Field</th><th>Image A</th><th>Image B</th></tr>')
        for key, values in diff.items():
            if isinstance(values, list) and len(values) == 2:
                va, vb = values
                if isinstance(va, list):
                    va = ', '.join(str(x) for x in va)
                if isinstance(vb, list):
                    vb = ', '.join(str(x) for x in vb)
                rows.append(
                    f'<tr><td>{html.escape(key)}</td>'
                    f'<td>{html.escape(str(va))}</td>'
                    f'<td>{html.escape(str(vb))}</td></tr>'
                )
            else:
                rows.append(
                    f'<tr><td>{html.escape(key)}</td>'
                    f'<td colspan="2">{html.escape(str(values))} different tokens</td></tr>'
                )
        rows.append('</table>')
    rows.append('</div>')
    rows.append('</div>')
    return '\n'.join(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────────────────────

def _get_filtered_images(folder: str, search_text: str, tag_query: str, only_favorites: bool, sort_by: str) -> List[str]:
    images = _utils.scan_image_folder(folder, recursive=True, sort_by=sort_by)
    return _utils.filter_images(
        images,
        search_text=search_text,
        tag_query=tag_query,
        only_favorites=only_favorites,
    )


def scan_folder(
    folder: str,
    tile_size: int,
    search_text: str,
    tag_query: str,
    only_favorites: bool,
    sort_by: str,
) -> tuple:
    if not folder or not Path(folder).exists():
        msg = f'Folder not found: {folder}'
        empty = '<div class="gallery-empty">Folder not found.</div>'
        return empty, _render_sources_html(folder), _render_tags_cloud(), empty, '', msg, folder

    filtered = _get_filtered_images(folder, search_text, tag_query, only_favorites, sort_by)

    defaults = _load_defaults()
    defaults['image_folder'] = folder
    defaults['tile_size'] = tile_size
    _save_defaults(defaults)

    msg = f'Found {len(filtered)} images'
    browser_html = _render_browser_html(filtered, tile_size, [], preview_path=None)
    sources_html = _render_sources_html(folder)
    tags_html = _render_tags_cloud()
    return browser_html, sources_html, tags_html, _render_selected_html([], tile_size), '', msg, folder


def _update_selection(selected_json: str, tile_size: int) -> tuple:
    try:
        selected = json.loads(selected_json) if selected_json else []
    except json.JSONDecodeError:
        selected = []

    preview_path = selected[0] if selected else None
    preview_html = '<div class="gallery-empty">Select an image to preview.</div>'
    metadata_html = '<div class="gallery-empty">Image metadata will appear here.</div>'

    if preview_path:
        img_url = _utils.image_to_data_url(preview_path, max_size=1024)
        if img_url:
            preview_html = f'<div class="gallery-preview"><img src="{img_url}" alt="preview"></div>'
        metadata = _meta.extract_metadata(preview_path)
        metadata_html = _render_metadata_html(metadata)

    compare_html = '<div class="gallery-empty">Select exactly 2 images in the Gallery tab to compare.</div>'
    if len(selected) == 2:
        compare_html = _render_compare_html(selected[0], selected[1])

    can_post = 0 < len(selected) <= MAX_IMAGES_PER_POST
    post_update = gr.update(interactive=can_post)

    return (
        selected_json,
        _render_selected_html(selected, tile_size),
        preview_html,
        metadata_html,
        compare_html,
        post_update,
    )


def _update_preview_only(preview_path: str, tile_size: int) -> tuple:
    if not preview_path or not Path(preview_path).exists():
        return (
            '<div class="gallery-empty">Select an image to preview.</div>',
            '<div class="gallery-empty">Image metadata will appear here.</div>',
        )

    img_url = _utils.image_to_data_url(preview_path, max_size=1024)
    preview_html = f'<div class="gallery-preview"><img src="{img_url or ""}" alt="preview"></div>' if img_url else '<div class="gallery-empty">Could not load preview.</div>'
    metadata = _meta.extract_metadata(preview_path)
    metadata_html = _render_metadata_html(metadata)
    return preview_html, metadata_html


def _handle_fav_toggle(fav_json: str, folder: str, tile_size: int, search_text: str, tag_query: str, only_favorites: bool, sort_by: str) -> tuple:
    try:
        data = json.loads(fav_json) if fav_json else {}
    except json.JSONDecodeError:
        data = {}

    action = data.get('action')
    path = data.get('path')
    if action == 'toggle' and path:
        try:
            _tags.toggle_favorite(path)
        except Exception as e:
            return '', '', f'❌ Failed to toggle favorite: {e}'

    filtered = _get_filtered_images(folder, search_text, tag_query, only_favorites, sort_by)
    selected = []
    browser_html = _render_browser_html(filtered, tile_size, selected, preview_path=None)
    tags_html = _render_tags_cloud()
    return browser_html, tags_html, ''


def _auto_fill_from_metadata(selected_json: str, title: str, detail: str, tags: str) -> tuple:
    try:
        selected = json.loads(selected_json) if selected_json else []
    except json.JSONDecodeError:
        selected = []

    if not selected:
        return title, detail, tags

    metadata = _meta.extract_metadata(selected[0])
    new_detail = _meta.metadata_to_description(metadata)
    new_title = Path(selected[0]).stem

    suggested_tags = set()
    model = metadata.get('meta', {}).get('Model')
    if model:
        suggested_tags.add(model.lower().replace(' ', '_'))
    for lora in metadata.get('loras', [])[:3]:
        suggested_tags.add(lora.lower().replace(' ', '_'))
    for tag in metadata.get('pos_prompt', [])[:10]:
        if ' ' not in tag and len(tag) > 2:
            suggested_tags.add(tag)

    existing_tags = set(t.strip() for t in tags.split(',') if t.strip())
    combined_tags = existing_tags | suggested_tags
    tags_str = ', '.join(sorted(combined_tags))

    return (
        title or new_title,
        detail or new_detail,
        tags_str,
    )


def _build_publish_flag(publish_mode: str) -> bool:
    return publish_mode == 'Publish now'


def _split_tags(tags_text: str) -> List[str]:
    if not tags_text:
        return []
    tags = []
    for raw in tags_text.split(','):
        tag = raw.strip().lower()
        # CivitAI tags: lowercase, no spaces, no special chars
        tag = re.sub(r'[^a-z0-9_\-]', '', tag.replace(' ', '_'))
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def post_to_civitai(
    selected_json: str,
    title: str,
    detail: str,
    tags_text: str,
    publish_mode: str,
    resize_upload: int,
) -> str:
    try:
        selected = json.loads(selected_json) if selected_json else []
    except json.JSONDecodeError:
        selected = []

    if not selected:
        return '❌ No images selected.'
    if len(selected) > MAX_IMAGES_PER_POST:
        return f'❌ CivitAI allows up to {MAX_IMAGES_PER_POST} images per post. You selected {len(selected)}.'
    if not title.strip():
        return '❌ Title is required.'

    whoami = _api.whoami()
    if not whoami.get('ok'):
        return f'❌ Failed to authenticate with CivitAI: {whoami.get("error")}'
    structured = whoami.get('structured') or {}
    if not structured.get('isOnboarded'):
        return '❌ Your CivitAI account is not fully onboarded. Complete onboarding on civitai.com first.'

    logs = [f'👤 Logged in as {structured.get("username", "unknown")}']

    image_uuids = []
    for path in selected:
        logs.append(f'⏳ Uploading {Path(path).name}...')
        result = _api.upload_image(path, resize=resize_upload if resize_upload > 0 else None)
        if not result.get('ok'):
            logs.append(f'❌ Upload failed: {result.get("error")}')
            return '<br>'.join(logs)

        uploaded = result.get('structured') or {}
        image_uuid = uploaded.get('uuid') or uploaded.get('id')
        if not image_uuid:
            logs.append(f'⚠️ Upload succeeded but no UUID returned: {result.get("text")}')
            return '<br>'.join(logs)

        image_uuids.append(image_uuid)
        logs.append(f'✅ Uploaded {Path(path).name} → {image_uuid}')

    publish = _build_publish_flag(publish_mode)
    tags = _split_tags(tags_text)

    logs.append('⏳ Creating post...')
    post_result = _api.create_post(
        title=title.strip(),
        detail=detail.strip(),
        image_uuids=image_uuids,
        tags=tags,
        publish=publish,
    )

    if not post_result.get('ok'):
        logs.append(f'❌ Failed to create post: {post_result.get("error")}')
        return '<br>'.join(logs)

    post_data = post_result.get('structured') or {}
    post_id = post_data.get('id')
    post_url = None

    # Try to get the canonical URL from the created post
    if post_id:
        get_result = _api.get_post(post_id)
        if get_result.get('ok'):
            post_url = (get_result.get('structured') or {}).get('url')
        if not post_url:
            post_url = f'https://civitai.com/posts/{post_id}'

    if post_url:
        logs.append(f'✅ Post created: <a href="{post_url}" target="_blank">{post_url}</a>')
    else:
        logs.append(f'✅ Post created: {post_result.get("text")}')

    return '<br>'.join(logs)


def test_connection() -> str:
    result = _api.whoami()
    if not result.get('ok'):
        return f'❌ Connection failed: {result.get("error")}'
    data = result.get('structured') or {}
    username = data.get('username', 'unknown')
    onboarded = data.get('isOnboarded', False)
    muted = data.get('muted', False)
    status = 'onboarded' if onboarded else 'NOT onboarded'
    muted_text = ' (muted)' if muted else ''
    return f'✅ Connected as <b>{username}</b> — {status}{muted_text}'


def _get_user_status() -> str:
    """Return a small HTML badge showing the current CivitAI user."""
    try:
        result = _api.whoami()
        if not result.get('ok'):
            return '<span class="civitai-user-badge error">⚠️ Not connected</span>'
        data = result.get('structured') or {}
        username = data.get('username', 'unknown')
        onboarded = data.get('isOnboarded', False)
        muted = data.get('muted', False)
        if onboarded and not muted:
            return f'<span class="civitai-user-badge ok">👤 {username}</span>'
        if muted:
            return f'<span class="civitai-user-badge warn">👤 {username} (muted)</span>'
        return f'<span class="civitai-user-badge warn">👤 {username} (not onboarded)</span>'
    except Exception as e:
        return f'<span class="civitai-user-badge error">⚠️ {e}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# UI Definition
# ─────────────────────────────────────────────────────────────────────────────

def on_ui_tabs():
    defaults = _load_defaults()
    tile_size = defaults.get('tile_size', 192)

    with gr.Blocks() as civitai_gallery_interface:
        # Hidden state fields
        selected_state = gr.Textbox(value='[]', visible=False, elem_id='civitai_gallery_selected_state')
        current_folder_state = gr.Textbox(value=_default_image_folder(), visible=False, elem_id='civitai_gallery_folder_state')

        gr.Markdown('## 📤 CivitAI Uploader Neo')
        gr.Markdown('Browse, compare and upload your generated images directly to CivitAI.')

        user_status_html = gr.HTML(
            value=_get_user_status(),
            elem_id='civitai_gallery_user_status'
        )

        with gr.Tabs():
            # ── Gallery Tab ──
            with gr.Tab(label='🖼️ Gallery', elem_id='civitai_gallery_tab_gallery'):
                with gr.Row():
                    # Left column: sources + filters
                    with gr.Column(scale=1, min_width=240):
                        gr.Markdown('### 🗂️ Sources')
                        folder_input = gr.Textbox(
                            label='Folder',
                            value=_default_image_folder(),
                            elem_id='civitai_gallery_folder'
                        )
                        sources_html = gr.HTML(value='', elem_id='civitai_gallery_sources')

                        gr.Markdown('### 🔍 Filters')
                        search_input = gr.Textbox(label='Search', placeholder='filename or metadata...')
                        tag_filter_input = gr.Textbox(label='Tags', placeholder='#favorite, #pony...', elem_id='civitai_gallery_tag_filter')
                        only_favorites = gr.Checkbox(label='Only favorites', value=False)
                        sort_dropdown = gr.Dropdown(
                            label='Sort by',
                            choices=['date_desc', 'date_asc', 'name', 'size_desc', 'size_asc'],
                            value='date_desc'
                        )

                        gr.Markdown('### 🏷️ Tags')
                        tags_cloud_html = gr.HTML(value='', elem_id='civitai_gallery_tags_cloud')

                        scan_btn = gr.Button(value='🔄 Scan', variant='primary', elem_id='civitai_gallery_scan_btn')

                    # Center column: browser + preview + metadata
                    with gr.Column(scale=2, min_width=360):
                        tile_slider = gr.Slider(
                            label='Tile size',
                            minimum=64,
                            maximum=512,
                            value=tile_size,
                            step=16,
                        )
                        browser_html = gr.HTML(
                            value='<div class="gallery-empty">Click "Scan" to load images.</div>',
                            elem_id='civitai_gallery_browser'
                        )
                        preview_html = gr.HTML(
                            value='<div class="gallery-empty">Select an image to preview.</div>',
                            elem_id='civitai_gallery_preview'
                        )
                        metadata_html = gr.HTML(
                            value='<div class="gallery-empty">Image metadata will appear here.</div>',
                            elem_id='civitai_gallery_metadata'
                        )

                    # Right column: post details
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown('### ✏️ Post details')
                        title_input = gr.Textbox(label='Title', placeholder='Post title')
                        detail_input = gr.Textbox(
                            label='Description / Detail',
                            placeholder='Supports Markdown / HTML',
                            lines=6
                        )
                        tags_input = gr.Textbox(label='CivitAI tags', placeholder='comma, separated')

                        publish_mode = gr.Radio(
                            label='Publish',
                            choices=['Publish now', 'Save as draft'],
                            value='Publish now'
                        )

                        resize_input = gr.Slider(
                            label='Resize before upload (0 = original)',
                            minimum=0,
                            maximum=2048,
                            value=0,
                            step=64,
                        )

                        auto_fill_btn = gr.Button(value='✨ Auto-fill from first image', size='sm')

                        gr.Markdown('### 📋 Selected')
                        selected_html = gr.HTML(
                            value='<div class="gallery-empty">No images selected.</div>',
                            elem_id='civitai_gallery_selected'
                        )

                        with gr.Row():
                            test_btn = gr.Button(value='🔑 Test', variant='secondary')
                            post_btn = gr.Button(value='🚀 Post', variant='primary')

                with gr.Row():
                    log_html = gr.HTML(label='Log', value='', elem_id='civitai_gallery_log')

            # ── Compare Tab ──
            with gr.Tab(label='🆚 Compare', elem_id='civitai_gallery_tab_compare'):
                compare_html = gr.HTML(
                    value='<div class="gallery-empty">Select exactly 2 images in the Gallery tab to compare.</div>',
                    elem_id='civitai_gallery_compare'
                )

        # JS sync inputs
        selected_sync = gr.Textbox(visible=False, elem_id='civitai_gallery_selected_sync')
        preview_sync = gr.Textbox(visible=False, elem_id='civitai_gallery_preview_sync')
        fav_sync = gr.Textbox(visible=False, elem_id='civitai_gallery_fav_sync')

        # Events
        scan_btn.click(
            fn=scan_folder,
            inputs=[folder_input, tile_slider, search_input, tag_filter_input, only_favorites, sort_dropdown],
            outputs=[browser_html, sources_html, tags_cloud_html, selected_html, preview_html, log_html, current_folder_state],
        )

        selected_sync.change(
            fn=_update_selection,
            inputs=[selected_sync, tile_slider],
            outputs=[selected_state, selected_html, preview_html, metadata_html, compare_html, post_btn],
        )

        preview_sync.change(
            fn=_update_preview_only,
            inputs=[preview_sync, tile_slider],
            outputs=[preview_html, metadata_html],
        )

        fav_sync.change(
            fn=_handle_fav_toggle,
            inputs=[fav_sync, current_folder_state, tile_slider, search_input, tag_filter_input, only_favorites, sort_dropdown],
            outputs=[browser_html, tags_cloud_html, log_html],
        )

        auto_fill_btn.click(
            fn=_auto_fill_from_metadata,
            inputs=[selected_state, title_input, detail_input, tags_input],
            outputs=[title_input, detail_input, tags_input],
        )

        test_btn.click(fn=test_connection, outputs=[log_html])

        civitai_gallery_interface.load(
            fn=_get_user_status,
            outputs=[user_status_html],
        )

        post_btn.click(
            fn=post_to_civitai,
            inputs=[
                selected_state,
                title_input,
                detail_input,
                tags_input,
                publish_mode,
                resize_input,
            ],
            outputs=[log_html],
        )

    return [(civitai_gallery_interface, 'CivitAI Gallery', 'civitai_gallery_uploader')]


def on_ui_settings():
    try:
        from modules.options import categories
        categories.register_category('civitai_gallery_uploader', 'CivitAI Uploader Neo')
    except Exception:
        pass

    cat_id = 'civitai_gallery_uploader'

    if not (hasattr(shared.OptionInfo, 'info') and callable(getattr(shared.OptionInfo, 'info'))):
        def info(self, info_text):
            self.label += f' ({info_text})'
            return self
        shared.OptionInfo.info = info

    shared.opts.add_option(
        'civitai_gallery_api_key',
        shared.OptionInfo(
            default=r'',
            label='CivitAI API key for uploads',
            section=('civitai_gallery', 'Gallery Uploader'),
            category_id=cat_id,
        ).info('Create at civitai.com/user/account. Required for posting images.')
    )


script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_ui_settings(on_ui_settings)

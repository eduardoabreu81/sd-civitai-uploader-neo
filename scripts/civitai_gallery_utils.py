import base64
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PIL import Image as PILImage

from . import civitai_gallery_meta as _meta
from . import civitai_gallery_tags as _tags


SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}


def is_supported_image(path: str) -> bool:
    """Return True if the file has a supported image extension."""
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def _image_sort_key(path: Path, sort_by: str) -> any:
    """Return a sort key for an image path."""
    stat = path.stat()
    if sort_by == 'name':
        return path.name.lower()
    if sort_by == 'date_asc':
        return stat.st_mtime
    if sort_by == 'date_desc':
        return -stat.st_mtime
    if sort_by == 'size_asc':
        return stat.st_size
    if sort_by == 'size_desc':
        return -stat.st_size
    # default: newest first
    return -stat.st_mtime


def scan_image_folder(
    folder: str,
    recursive: bool = True,
    sort_by: str = 'date_desc',
) -> List[str]:
    """Return a list of supported image file paths inside a folder."""
    folder_path = Path(folder)
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    images = []
    if recursive:
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            images.extend(folder_path.rglob(f'*{ext}'))
            images.extend(folder_path.rglob(f'*{ext.upper()}'))
    else:
        for ext in SUPPORTED_IMAGE_EXTENSIONS:
            images.extend(folder_path.glob(f'*{ext}'))
            images.extend(folder_path.glob(f'*{ext.upper()}'))

    seen: Set[str] = set()
    unique: List[Path] = []
    for p in images:
        resolved = str(p.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)

    unique.sort(key=lambda p: _image_sort_key(p, sort_by))
    return [str(p) for p in unique]


def ensure_thumbnail_cache() -> Path:
    """Return (and create if needed) the extension-local thumbnail cache directory."""
    ext_root = Path(__file__).resolve().parents[1]
    cache_dir = ext_root / 'config_states' / 'thumbnails'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_thumbnail_path(image_path: str, size: int = 256) -> Path:
    """Return the cached thumbnail path for an image."""
    cache_dir = ensure_thumbnail_cache()
    resolved = Path(image_path).resolve()
    hash_input = f'{resolved}|{size}'
    name_hash = base64.urlsafe_b64encode(
        hash_input.encode('utf-8')
    ).decode('utf-8').rstrip('=')
    return cache_dir / f'{name_hash}.jpg'


def generate_thumbnail(image_path: str, size: int = 256, force: bool = False) -> Optional[str]:
    """Generate a JPEG thumbnail for an image and return its path."""
    thumb_path = get_thumbnail_path(image_path, size)
    if thumb_path.exists() and not force:
        return str(thumb_path)

    try:
        with PILImage.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail((size, size), PILImage.LANCZOS)
            img.save(str(thumb_path), 'JPEG', quality=85)
        return str(thumb_path)
    except Exception:
        return None


def thumbnail_to_base64(image_path: str, size: int = 256) -> Optional[str]:
    """Generate or reuse a thumbnail and return it as a base64 data URL."""
    thumb_path = generate_thumbnail(image_path, size)
    if not thumb_path:
        return None
    try:
        with open(thumb_path, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('utf-8')
        return f'data:image/jpeg;base64,{b64}'
    except Exception:
        return None


def image_to_data_url(image_path: str, max_size: Optional[int] = None) -> Optional[str]:
    """Convert an image file to a base64 data URL."""
    try:
        with PILImage.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            if max_size:
                img.thumbnail((max_size, max_size), PILImage.LANCZOS)
            from io import BytesIO
            bio = BytesIO()
            img.save(bio, format='PNG')
            buffer = bio.getvalue()
        b64 = base64.b64encode(buffer).decode('utf-8')
        return f'data:image/png;base64,{b64}'
    except Exception:
        return None


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Remove illegal characters and cap filename length."""
    name = re.sub(r'[\\\\/:*?"<>|]', '_', name)
    name = name.strip('.')
    if len(name) > max_length:
        name = name[:max_length]
    return name or 'untitled'


def format_file_size(path: str) -> str:
    """Return a human-readable file size."""
    try:
        size = os.path.getsize(path)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
    except Exception:
        return '?'


def format_datetime(timestamp: float) -> str:
    """Format a timestamp as a readable datetime."""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return '?'


def discover_subfolders(root: str) -> List[str]:
    """Return immediate subfolders of a root path, sorted."""
    root_path = Path(root)
    if not root_path.exists() or not root_path.is_dir():
        return []
    folders = [str(p) for p in root_path.iterdir() if p.is_dir()]
    folders.sort(key=lambda x: x.lower())
    return folders


def filter_images(
    image_paths: List[str],
    search_text: str = '',
    tag_query: str = '',
    extensions: Optional[List[str]] = None,
    only_favorites: bool = False,
) -> List[str]:
    """Filter images by search text, tags, extension and favorites."""
    result = image_paths

    # Filter by extension
    if extensions:
        ext_set = {e.lower().lstrip('.') for e in extensions}
        result = [p for p in result if Path(p).suffix.lower().lstrip('.') in ext_set]

    # Filter by favorites
    if only_favorites:
        favs = _tags.get_images_with_tag('favorite')
        result = [p for p in result if _tags._normalize_path(p) in favs]

    # Filter by local tags
    if tag_query:
        result = _tags.search_images_by_tag(result, tag_query)

    # Filter by text search (filename and metadata)
    if search_text:
        query = search_text.lower()
        filtered = []
        for path in result:
            if query in Path(path).name.lower():
                filtered.append(path)
                continue
            # Search in metadata
            metadata = _meta.extract_metadata(path)
            meta_text = json.dumps(metadata, default=str).lower()
            if query in meta_text:
                filtered.append(path)
        result = filtered

    return result


def get_image_stats(image_paths: List[str]) -> Dict[str, any]:
    """Return aggregate stats for a list of images."""
    total_size = 0
    model_counts: Dict[str, int] = {}
    lora_counts: Dict[str, int] = {}

    for path in image_paths:
        try:
            total_size += os.path.getsize(path)
        except Exception:
            pass

        metadata = _meta.extract_metadata(path)
        model = metadata.get('meta', {}).get('Model')
        if model:
            model_counts[model] = model_counts.get(model, 0) + 1
        for lora in metadata.get('loras', []):
            lora_counts[lora] = lora_counts.get(lora, 0) + 1

    return {
        'count': len(image_paths),
        'total_size': format_file_size_from_bytes(total_size),
        'top_models': sorted(model_counts.items(), key=lambda x: -x[1])[:5],
        'top_loras': sorted(lora_counts.items(), key=lambda x: -x[1])[:5],
    }


def format_file_size_from_bytes(size_bytes: int) -> str:
    """Return a human-readable file size from bytes."""
    if size_bytes == 0:
        return '0 B'
    size = float(size_bytes)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} PB'

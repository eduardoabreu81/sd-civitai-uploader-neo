import json
from pathlib import Path
from typing import Dict, List, Set


_EXT_ROOT = Path(__file__).resolve().parents[1]
_TAGS_DB_PATH = _EXT_ROOT / 'config_states' / 'gallery_tags.json'
_FAVORITES_KEY = 'favorite'


def _load_db() -> Dict[str, List[str]]:
    """Load the local tags database: {image_path: [tag1, tag2, ...]}."""
    try:
        with open(_TAGS_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def _save_db(data: Dict[str, List[str]]) -> None:
    """Save the local tags database."""
    _TAGS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_TAGS_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def _normalize_path(path: str) -> str:
    return str(Path(path).resolve())


def get_image_tags(image_path: str) -> List[str]:
    """Return the tags assigned to a single image."""
    db = _load_db()
    return db.get(_normalize_path(image_path), [])


def add_image_tag(image_path: str, tag: str) -> None:
    """Add a tag to an image."""
    tag = tag.strip().lower()
    if not tag or tag.startswith('#'):
        tag = tag.lstrip('#')
    if not tag:
        return

    db = _load_db()
    key = _normalize_path(image_path)
    tags = set(db.get(key, []))
    tags.add(tag)
    db[key] = sorted(tags)
    _save_db(db)


def remove_image_tag(image_path: str, tag: str) -> None:
    """Remove a tag from an image."""
    tag = tag.strip().lower().lstrip('#')
    if not tag:
        return

    db = _load_db()
    key = _normalize_path(image_path)
    tags = db.get(key, [])
    if tag in tags:
        tags.remove(tag)
        if tags:
            db[key] = tags
        else:
            db.pop(key, None)
        _save_db(db)


def toggle_image_tag(image_path: str, tag: str) -> bool:
    """Toggle a tag on an image. Returns True if tag is now present."""
    tag = tag.strip().lower().lstrip('#')
    db = _load_db()
    key = _normalize_path(image_path)
    tags = set(db.get(key, []))
    if tag in tags:
        tags.remove(tag)
        present = False
    else:
        tags.add(tag)
        present = True

    if tags:
        db[key] = sorted(tags)
    else:
        db.pop(key, None)
    _save_db(db)
    return present


def toggle_favorite(image_path: str) -> bool:
    """Toggle favorite status on an image. Returns new favorite state."""
    return toggle_image_tag(image_path, _FAVORITES_KEY)


def is_favorite(image_path: str) -> bool:
    """Return True if the image is marked as favorite."""
    return _FAVORITES_KEY in get_image_tags(image_path)


def get_all_tags() -> List[str]:
    """Return all unique tags used across images."""
    db = _load_db()
    all_tags: Set[str] = set()
    for tags in db.values():
        all_tags.update(tags)
    return sorted(all_tags)


def get_images_with_tag(tag: str) -> Set[str]:
    """Return all image paths that have a given tag."""
    tag = tag.strip().lower().lstrip('#')
    db = _load_db()
    result = set()
    for path, tags in db.items():
        if tag in tags:
            result.add(path)
    return result


def search_images_by_tag(image_paths: List[str], tag_query: str) -> List[str]:
    """Filter a list of image paths by tag query."""
    if not tag_query:
        return image_paths

    query_tags = [t.strip().lower().lstrip('#') for t in tag_query.split(',') if t.strip()]
    if not query_tags:
        return image_paths

    matching = None
    for tag in query_tags:
        paths = get_images_with_tag(tag)
        if matching is None:
            matching = paths
        else:
            matching &= paths

    return [p for p in image_paths if _normalize_path(p) in (matching or set())]


def add_batch_tag(image_paths: List[str], tag: str) -> None:
    """Add a tag to multiple images at once."""
    tag = tag.strip().lower().lstrip('#')
    if not tag:
        return

    db = _load_db()
    for path in image_paths:
        key = _normalize_path(path)
        tags = set(db.get(key, []))
        tags.add(tag)
        db[key] = sorted(tags)
    _save_db(db)

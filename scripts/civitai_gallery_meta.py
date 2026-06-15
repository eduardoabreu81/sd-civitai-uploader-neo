import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# === WebUI imports ===
try:
    from modules.images import read_info_from_image
except Exception:
    read_info_from_image = None


def _unique(items: List[str]) -> List[str]:
    """Preserve order while deduplicating."""
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _unquote(value: str) -> str:
    """Unquote a double-quoted string value."""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    return value


# Regex inspired by Infinite Image Browsing's robust parser
_RE_PARAM = re.compile(r'\s*([\w ]+):\s*("(?:\\"[^,]|\\"|\\|[^\"])+"|[^,]*)(?:,|$)')
_RE_IMAGE_SIZE = re.compile(r'^(\d+)x(\d+)$')
_RE_LORA_PROMPT = re.compile(r'<lora:([\w_\s.-]+)(?::([\d.]+))*>', re.IGNORECASE)
_RE_LYCO_PROMPT = re.compile(r'<lyco:([\w_\s.]+):([\d.]+)>', re.IGNORECASE)
_RE_PARENS = re.compile(r'[\\/\[\](){}]+')
_RE_LORA_EXTRACT = re.compile(r'([\w_\s.-]+)')


def _lora_extract(name: str) -> str:
    """Clean a LoRA name by removing hash suffixes."""
    match = _RE_LORA_EXTRACT.match(name)
    return match.group(1).strip() if match else name.strip()


def _parse_prompt_tags(prompt: str) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a prompt into tags, LoRAs and LyCORIS."""
    # Normalize separators and whitespace
    prompt = re.sub(r'\sBREAK\s', ' , BREAK , ', prompt)
    prompt = re.sub(r'>\s+', '> , ', prompt)
    prompt = prompt.replace('，', ',').replace('_', ' ')
    prompt = re.sub(_RE_PARENS, '', prompt)

    tags = []
    loras = []
    lycos = []

    for raw_tag in prompt.split(','):
        tag = raw_tag.strip()
        if not tag:
            continue

        # Check for LoRA
        lora_match = _RE_LORA_PROMPT.search(tag)
        if lora_match:
            weight = float(lora_match.group(2)) if lora_match.group(2) is not None else 1.0
            loras.append({'name': _lora_extract(lora_match.group(1)), 'weight': weight})
            continue

        # Check for LyCORIS
        lyco_match = _RE_LYCO_PROMPT.search(tag)
        if lyco_match:
            lycos.append({'name': lyco_match.group(1).strip(), 'weight': float(lyco_match.group(2))})
            continue

        # Strip weight syntax like (tag:1.2) -> tag (parentheses already removed)
        colon_idx = tag.find(':')
        if colon_idx != -1:
            tag = tag[:colon_idx].strip()

        if tag:
            tags.append(tag.lower())

    return _unique(tags), loras, lycos


def parse_generation_parameters(text: str) -> Dict[str, any]:
    """Parse a Stable Diffusion generation parameters string into structured data."""
    result = {
        'meta': {},
        'pos_prompt': [],
        'neg_prompt': '',
        'loras': [],
        'lycos': [],
    }

    if not text:
        return result

    # Handle extra JSON metadata appended by some UIs (Fooocus/ComfyUI style)
    extra_json_match = re.search(r'\nextraJsonMetaInfo:\s*(\{[\s\S]*\})\s*$', text.strip())
    if extra_json_match:
        try:
            extra = json.loads(extra_json_match.group(1))
            for k, v in extra.items():
                result['meta'][k] = v if isinstance(v, str) else json.dumps(v)
            text = re.sub(r'\nextraJsonMetaInfo:\s*\{[\s\S]*\}\s*$', '', text.strip())
        except json.JSONDecodeError:
            pass

    # Split into lines; last line usually contains the key:value params
    lines = text.strip().split('\n')
    lastline = lines[-1] if lines else ''

    # If last line has fewer than 3 params, it might belong to the prompt
    if len(_RE_PARAM.findall(lastline)) < 3:
        lines.append(lastline)
        lastline = ''

    # Special case for postprocess-only metadata
    if len(lines) == 1 and lines[0].startswith('Postprocess'):
        lastline = lines[0]
        lines = []

    positive_prompt = []
    negative_prompt = []
    done_with_prompt = False

    for line in lines:
        line = line.strip()
        if line.startswith('Negative prompt:'):
            done_with_prompt = True
            line = line[16:].strip()

        if done_with_prompt:
            negative_prompt.append(line)
        else:
            positive_prompt.append(line)

    result['pos_prompt'] = _parse_prompt_tags('\n'.join(positive_prompt))
    result['neg_prompt'] = '\n'.join(negative_prompt).strip()

    # Parse key:value pairs from the last line
    for key, value in _RE_PARAM.findall(lastline):
        try:
            value = value.strip()
            if not value:
                result['meta'][key] = value
                continue
            if value[0] == '"' and value[-1] == '"':
                value = _unquote(value)

            size_match = _RE_IMAGE_SIZE.match(value)
            if size_match:
                result['meta'][f'{key}-width'] = size_match.group(1)
                result['meta'][f'{key}-height'] = size_match.group(2)
            else:
                result['meta'][key] = value
        except Exception as e:
            print(f'[CivitAI Gallery] Error parsing metadata "{key}: {value}": {e}')

    # Extract LoRAs also from AddNet fields (alternative embedding format)
    for key in list(result['meta'].keys()):
        key_str = str(key)
        if key_str.startswith('AddNet Module') and str(result['meta'][key]).lower() == 'lora':
            model_key = key_str.replace('Module', 'Model')
            weight_key = key_str.replace('Module', 'Weight A')
            model_name = result['meta'].get(model_key, '')
            weight = float(result['meta'].get(weight_key, '1') or '1')
            if model_name:
                result['loras'].append({'name': _lora_extract(model_name), 'weight': weight})

    # Merge parsed LoRAs from prompt with AddNet ones
    prompt_tags, prompt_loras, prompt_lycos = _parse_prompt_tags('\n'.join(positive_prompt))
    result['pos_prompt'] = prompt_tags
    result['loras'] = _unique([l['name'] for l in result['loras'] + prompt_loras])
    result['lycos'] = _unique([l['name'] for l in prompt_lycos])

    return result


def _read_txt_sidecar(image_path: str) -> Optional[str]:
    """Try to read metadata from a .txt sidecar file."""
    txt_path = Path(image_path).with_suffix('.txt')
    if txt_path.exists():
        try:
            return txt_path.read_text(encoding='utf-8')
        except Exception:
            pass
    return None


def extract_metadata(image_path: str) -> Dict[str, any]:
    """Extract generation metadata from an image using Forge helper or sidecar."""
    raw_text = ''

    if read_info_from_image is not None:
        try:
            _, raw_text = read_info_from_image(image_path)
        except Exception:
            raw_text = ''

    if not raw_text:
        raw_text = _read_txt_sidecar(image_path) or ''

    return parse_generation_parameters(raw_text)


def metadata_to_description(metadata: Dict[str, any]) -> str:
    """Build a CivitAI-friendly description from parsed metadata."""
    lines = []
    meta = metadata.get('meta', {})

    prompt = ', '.join(metadata.get('pos_prompt', []))
    negative = metadata.get('neg_prompt', '')

    if prompt:
        lines.append(f'**Prompt:** {prompt}')
    if negative:
        lines.append(f'**Negative prompt:** {negative}')

    fields = ['Model', 'Model hash', 'Sampler', 'Schedule type', 'CFG scale', 'Steps', 'Seed', 'Size']
    parts = []
    for field in fields:
        value = meta.get(field)
        if value:
            parts.append(f'{field}: {value}')

    loras = metadata.get('loras', [])
    if loras:
        parts.append(f'LoRAs: {", ".join(loras)}')

    if parts:
        lines.append('')
        lines.append(', '.join(parts))

    return '\n'.join(lines).strip()


def get_model_resource(metadata: Dict[str, any]) -> Optional[Dict[str, str]]:
    """Return a CivitAI resource hint if model hash is present."""
    meta = metadata.get('meta', {})
    model_hash = meta.get('Model hash') or meta.get('modelhash')
    model_name = meta.get('Model', 'Unknown model')
    if model_hash:
        return {'name': model_name, 'hash': model_hash}
    return None


def compute_metadata_diff(meta_a: Dict[str, any], meta_b: Dict[str, any], ignore_seed: bool = False) -> Dict[str, any]:
    """Compare two parsed metadata dicts and return differences."""
    diff = {}
    skip = {'hashes', 'resources'}
    if ignore_seed:
        skip.add('seed')

    # Compare flat meta fields
    fields_a = meta_a.get('meta', {})
    fields_b = meta_b.get('meta', {})
    all_keys = set(fields_a.keys()) | set(fields_b.keys())

    for key in all_keys:
        if key.lower() in skip:
            continue
        val_a = fields_a.get(key, '')
        val_b = fields_b.get(key, '')
        if val_a != val_b:
            diff[key] = [val_a, val_b]

    # Compare prompts as token lists
    for prompt_key in ('pos_prompt', 'neg_prompt'):
        val_a = meta_a.get(prompt_key, [])
        val_b = meta_b.get(prompt_key, [])
        if isinstance(val_a, str):
            val_a = [t.strip() for t in val_a.split(',') if t.strip()]
        if isinstance(val_b, str):
            val_b = [t.strip() for t in val_b.split(',') if t.strip()]
        if val_a != val_b:
            diff[prompt_key] = len([i for i in range(max(len(val_a), len(val_b))) if i >= len(val_a) or i >= len(val_b) or val_a[i] != val_b[i]])

    # Compare LoRAs
    loras_a = set(meta_a.get('loras', []))
    loras_b = set(meta_b.get('loras', []))
    if loras_a != loras_b:
        diff['loras'] = [sorted(loras_a - loras_b), sorted(loras_b - loras_a)]

    return diff

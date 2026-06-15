import base64
import json
import time
from typing import Any, Dict, List, Optional

import requests

# === WebUI imports ===
from modules.shared import opts


MCP_ENDPOINT = "https://mcp.civitai.com/mcp"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB, matches CivitAI MCP server default


def _get_api_key() -> str:
    """Return the configured CivitAI API key."""
    return getattr(opts, 'civitai_gallery_api_key', '') or getattr(opts, 'custom_api_key', '')


def _get_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    api_key = _get_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def mcp_call(tool_name: str, arguments: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    """Call a tool on the CivitAI MCP server via JSON-RPC over HTTP."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": int(time.time() * 1000),
    }

    try:
        response = requests.post(
            MCP_ENDPOINT,
            headers=_get_headers(),
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return {"ok": False, "error": data["error"]}

        result = data.get("result", {})
        content = result.get("content", [])
        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        full_text = "\n".join(text_parts)

        structured = None
        try:
            structured = json.loads(full_text)
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "ok": True,
            "text": full_text,
            "structured": structured,
            "raw": result,
        }

    except requests.exceptions.Timeout:
        return {"ok": False, "error": f"Request to MCP server timed out after {timeout}s"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"MCP request failed: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected MCP error: {e}"}


def upload_image(image_path: str, resize: Optional[int] = None) -> Dict[str, Any]:
    """Upload a local image to CivitAI and return its UUID."""
    from PIL import Image as PILImage
    from io import BytesIO

    try:
        with PILImage.open(image_path) as img:
            content_type = "image/png"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            if resize:
                img.thumbnail((resize, resize), PILImage.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            raw_bytes = buffer.getvalue()

            if len(raw_bytes) > MAX_UPLOAD_BYTES:
                return {
                    "ok": False,
                    "error": (
                        f"Image '{image_path}' is too large after conversion "
                        f"({len(raw_bytes) / 1024 / 1024:.2f} MB > 10 MB). "
                        "Try enabling resize before upload."
                    ),
                }

            b64 = base64.b64encode(raw_bytes).decode("utf-8")
            return mcp_call("upload_image", {"data": b64, "contentType": content_type})

    except Exception as e:
        return {"ok": False, "error": f"Failed to read/convert image '{image_path}': {e}"}


def create_post(
    title: str,
    detail: str,
    image_uuids: List[str],
    tags: Optional[List[str]] = None,
    publish: bool = False,
) -> Dict[str, Any]:
    """Create a CivitAI post with the given images."""
    images = [{"uuid": uuid, "type": "image"} for uuid in image_uuids]
    arguments: Dict[str, Any] = {
        "title": title,
        "detail": detail,
        "images": images,
        "publish": publish,
    }
    if tags:
        arguments["tags"] = tags

    return mcp_call("create_post", arguments, timeout=180)


def get_post(post_id: int) -> Dict[str, Any]:
    """Fetch a post by ID to confirm creation and get its URL."""
    return mcp_call("get_post", {"id": post_id})


def whoami() -> Dict[str, Any]:
    """Resolve current user info and onboarding status."""
    return mcp_call("whoami", {})


def list_tools() -> Dict[str, Any]:
    """List available tools on the MCP server (useful for debugging)."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": int(time.time() * 1000),
    }
    try:
        response = requests.post(
            MCP_ENDPOINT,
            headers=_get_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return {"ok": True, "data": response.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

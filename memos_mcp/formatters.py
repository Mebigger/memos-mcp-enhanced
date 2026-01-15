"""Response formatting utilities."""
from datetime import datetime
from typing import Any

from .config import settings


def format_timestamp(timestamp: int | None) -> str | None:
    """Format Unix timestamp to ISO 8601 string."""
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp).isoformat()


def truncate_text(text: str, max_length: int | None = None) -> str:
    """Truncate text to maximum length."""
    max_len = max_length or settings.character_limit
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...\n\n[Content truncated due to length limit]"


def format_memo_to_json(memo: dict[str, Any]) -> dict[str, Any]:
    """Format a memo for JSON response."""
    # Handle both old timestamp format and new ISO format
    created_time = memo.get("createTime") or format_timestamp(memo.get("createdTs"))
    updated_time = memo.get("updateTime") or format_timestamp(memo.get("updatedTs"))
    
    return {
        "id": memo.get("id") or memo.get("name"),
        "content": memo.get("content"),
        "created_time": created_time,
        "updated_time": updated_time,
        "display_time": memo.get("displayTime"),
        "visibility": memo.get("visibility"),
        "tags": memo.get("tags", []),
        "creator": {
            "id": memo.get("creator") if isinstance(memo.get("creator"), str) else memo.get("creator", {}).get("id"),
            "username": memo.get("creator", {}).get("username") if isinstance(memo.get("creator"), dict) else None,
            "nickname": memo.get("creator", {}).get("nickname") if isinstance(memo.get("creator"), dict) else None,
        },
        "pinned": memo.get("pinned", False),
        "resources": [
            {
                "id": r.get("id") or r.get("name"),
                "name": r.get("filename"),
                "type": r.get("type"),
                "url": r.get("externalLink") or f"/api/v1/resources/{r.get('id') or r.get('name')}",
            }
            for r in (memo.get("resources") or memo.get("attachments") or [])
        ],
        "relations": [
            {
                "id": rel.get("id"),
                "type": rel.get("type"),
                "related_memo_id": rel.get("relatedMemoId"),
            }
            for rel in memo.get("relations", [])
        ],
        "row_status": memo.get("rowStatus") or memo.get("state"),
    }


def format_memo_to_markdown(memo: dict[str, Any]) -> str:
    """Format a memo for Markdown response."""
    lines = []

    # Header with visibility and timestamp
    visibility = memo.get("visibility", "PRIVATE")
    created = format_timestamp(memo.get("createdTs"))
    updated = format_timestamp(memo.get("updatedTs"))

    lines.append(f"**ID:** {memo.get('id')}")
    lines.append(f"**Visibility:** {visibility}")
    lines.append(f"**Created:** {created}")
    if updated != created:
        lines.append(f"**Updated:** {updated}")
    if memo.get("pinned"):
        lines.append("**📌 Pinned**")

    # Content
    content = memo.get("content", "")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(content)

    # Tags
    tags = memo.get("tags", [])
    if tags:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Tags:** " + ", ".join(f"`{tag}`" for tag in tags))

    # Resources
    resources = memo.get("resources", [])
    if resources:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Resources:**")
        for r in resources:
            name = r.get("filename", "unnamed")
            rtype = r.get("type", "unknown")
            lines.append(f"- [{name}]({r.get('externalLink') or '#'}) ({rtype})")

    return "\n".join(lines)


def format_memo_list(
    memos: list[dict[str, Any]],
    format_type: str | None = None,
) -> str:
    """Format a list of memos."""
    fmt = format_type or settings.response_format

    if fmt == "markdown":
        lines = ["# Memos\n"]
        for memo in memos:
            preview = memo.get("content", "")[:100].replace("\n", " ")
            tags = ", ".join(memo.get("tags", []))
            created = format_timestamp(memo.get("createdTs")) or "unknown"
            lines.append(f"- **{created}** | {preview}")
            if tags:
                lines.append(f"  - Tags: {tags}")
            lines.append("")
        return "\n".join(lines)
    else:
        return format_memos_to_json_list(memos)


def format_memos_to_json_list(memos: list[dict[str, Any]]) -> str:
    """Format memos as JSON list string."""
    import json

    formatted = [format_memo_to_json(m) for m in memos]
    return json.dumps(formatted, ensure_ascii=False, indent=2)


import json

def format_error(
    code: str,
    message: str,
    suggestion: str | None = None,
) -> str:
    """Format an error response as a JSON string."""
    error = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if suggestion:
        error["error"]["suggestion"] = suggestion
    return json.dumps(error, ensure_ascii=False)


def format_success(
    data: Any,
    meta: dict[str, Any] | None = None,
) -> str:
    """Format a success response as a JSON string."""
    response = {"success": True, "data": data}
    if meta:
        response["meta"] = meta
    return json.dumps(response, ensure_ascii=False)

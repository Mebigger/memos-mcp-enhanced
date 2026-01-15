"""Additional MCP tools for batch operations, templates, and exports."""
from typing import Annotated

from .client import client
from .config import settings
from .formatters import format_error, format_memo_to_json, format_success


# Copy these functions to the end of tools.py


async def batch_operation_impl(
    operation: str,
    filter_tags: list[str] | None = None,
    filter_visibility: str | None = None,
    filter_pinned: bool | None = None,
    confirm: bool = False,
    tag: str | None = None,
    new_visibility: str | None = None,
) -> str:
    """Implementation of batch operations."""
    try:
        # Import validate_visibility from tools
        from .tools import validate_visibility
        
        # Build filter
        filter_conditions = []
        if filter_tags:
            tag_conds = [f"'{t}' in tags" for t in filter_tags]
            filter_conditions.append(f'({" || ".join(tag_conds)})')
        if filter_visibility:
            filter_conditions.append(f'visibility == "{filter_visibility}"')
        if filter_pinned is not None:
            filter_conditions.append(f"pinned == {str(filter_pinned).lower()}")
        
        filter_str = " && ".join(filter_conditions) if filter_conditions else ""
        
        # Get memos
        response = await client.get("/memos", params={
            "pageSize": settings.batch_limit,
            "filter": filter_str
        })
        
        if response.get("error"):
            return str(format_error(
                code="BATCH_FAILED",
                message=response["error"].get("message", "Failed to get memos"),
            ))
        
        memos = response.get("memos", [])
        
        if not memos:
            return str(format_success({
                "message": "No memos match the filter",
                "count": 0,
            }))
        
        # Preview mode
        if not confirm:
            preview = [{
                "id": m.get("id"),
                "content_preview": m.get("content", "")[:100],
                "tags": m.get("tags", []),
            } for m in memos]
            
            return str(format_success({
                "preview": preview,
                "count": len(memos),
                "message": f"Preview: {len(memos)} memo(s) will be affected. Set confirm=True to execute.",
            }))
        
        # Execute operation
        results = []
        errors = []
        
        for memo in memos:
            memo_id = memo.get("id")
            try:
                if operation == "delete":
                    await client.delete(f"/memos/{memo_id}")
                    results.append(memo_id)
                    
                elif operation == "add_tag":
                    if not tag:
                        return str(format_error(code="MISSING_PARAM", message="tag parameter required"))
                    existing_tags = memo.get("tags", [])
                    if tag not in existing_tags:
                        new_tags = existing_tags + [tag]
                        await client.patch(f"/memos/{memo_id}", 
                                         params={"updateMask": "tags"},
                                         json={"tags": new_tags})
                    results.append(memo_id)
                    
                elif operation == "remove_tag":
                    if not tag:
                        return str(format_error(code="MISSING_PARAM", message="tag parameter required"))
                    existing_tags = memo.get("tags", [])
                    if tag in existing_tags:
                        new_tags = [t for t in existing_tags if t != tag]
                        await client.patch(f"/memos/{memo_id}",
                                         params={"updateMask": "tags"},
                                         json={"tags": new_tags})
                    results.append(memo_id)
                    
                elif operation == "set_visibility":
                    if not new_visibility:
                        return str(format_error(code="MISSING_PARAM", message="new_visibility parameter required"))
                    await client.patch(f"/memos/{memo_id}",
                                     params={"updateMask": "visibility"},
                                     json={"visibility": validate_visibility(new_visibility)})
                    results.append(memo_id)
                    
                elif operation == "pin":
                    await client.patch(f"/memos/{memo_id}",
                                     params={"updateMask": "pinned"},
                                     json={"pinned": True})
                    results.append(memo_id)
                    
                elif operation == "unpin":
                    await client.patch(f"/memos/{memo_id}",
                                     params={"updateMask": "pinned"},
                                     json={"pinned": False})
                    results.append(memo_id)
                    
                elif operation == "archive":
                    await client.patch(f"/memos/{memo_id}",
                                     params={"updateMask": "rowStatus"},
                                     json={"rowStatus": "ARCHIVED"})
                    results.append(memo_id)
                    
                else:
                    return str(format_error(code="INVALID_OPERATION", message=f"Unknown operation: {operation}"))
                    
            except Exception as e:
                errors.append({"memo_id": memo_id, "error": str(e)})
        
        return str(format_success({
            "operation": operation,
            "success_count": len(results),
            "error_count": len(errors),
            "processed_ids": results,
            "errors": errors if errors else None,
        }))
        
    except Exception as e:
        return str(format_error(
            code="BATCH_ERROR",
            message=str(e),
        ))


# Template and export tool implementations are in template_manager.py and exporters.py
# They should be wrapped with @mcp.tool() decorator in tools.py

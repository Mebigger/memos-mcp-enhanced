"""Attachment management tools for Memos MCP server."""
from typing import Annotated

from .client import client
from .formatters import format_error, format_memo_to_json, format_success


async def add_attachment_to_memo(
    memo_id: str,
    file_path: str,
    filename: str | None = None,
) -> str:
    """
    Add a single attachment to an existing memo.

    Args:
        memo_id: The ID of the memo
        file_path: Path to the file to upload
        filename: Optional custom filename

    Returns:
        Formatted success or error response
    """
    import os
    
    try:
        # Validate file exists
        resolved_path = os.path.abspath(file_path)
        
        if not os.path.exists(resolved_path):
            return format_error(
                code="FILE_NOT_FOUND",
                message=f"File not found: {file_path}",
                suggestion="Provide a valid file path that exists.",
            )
        
        if not os.path.isfile(resolved_path):
            return format_error(
                code="NOT_A_FILE",
                message=f"Path is not a file: {file_path}",
                suggestion="Provide a path to a file, not a directory.",
            )
        
        # Get current memo
        id_val = str(memo_id).split("/")[-1]
        memo_response = await client.get(f"/memos/{id_val}")
        
        if memo_response.get("error"):
            return format_error(
                code="GET_MEMO_FAILED",
                message=memo_response["error"].get("message", "Memo not found"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )
        
        memo = memo_response
        existing_resources = memo.get("resources", [])
        
        # Upload new file
        name = filename or os.path.basename(resolved_path)
        upload_response = await client.upload_resource(resolved_path, filename=name)
        
        if upload_response.get("error"):
            return format_error(
                code="UPLOAD_FAILED",
                message=upload_response["error"].get("message", "Failed to upload file"),
            )
        
        new_resource = upload_response
        
        # Combine resources
        all_resources = existing_resources + [new_resource]
        # Handle various resource ID formats (int ID vs string Name)
        resource_ids = []
        for r in all_resources:
            rid = r.get("id") or r.get("name")
            if rid:
                # If it's a full name like "resources/123", we might need just "123" depending on version
                # But let's try sending what we have. 
                # Actually, standard is usually ID if available.
                resource_ids.append(rid)
        
        # Update memo
        # API V1 expects 'attachments' list of objects with 'name'
        clean_ids = [str(rid).split("/")[-1] for rid in resource_ids if rid]
        attachments_payload = []
        for rid in clean_ids:
             attachments_payload.append({"name": f"attachments/{rid}"})

        params = {"updateMask": "attachments"}
        
        response = await client.patch(f"/memos/{id_val}", params=params, json={"attachments": attachments_payload})
        
        if response.get("error"):
            return format_error(
                code="ADD_ATTACHMENT_FAILED",
                message=response["error"].get("message", "Failed to add attachment"),
            )
        
        memo = response
        formatted = format_memo_to_json(memo)
        
        return format_success(formatted, {
            "message": f"Attachment '{name}' added successfully",
            "resource_id": new_resource.get("id") or new_resource.get("name"),
        })
    
    except Exception as e:
        return format_error(
            code="ADD_ATTACHMENT_ERROR",
            message=str(e),
        )


async def remove_attachment_from_memo(
    memo_id: str,
    attachment_id: int | str | None = None,
    filename: str | None = None,
) -> str:
    """
    Remove a single attachment from a memo.

    Args:
        memo_id: The ID of the memo
        attachment_id: ID of attachment to remove
        filename: Filename of attachment to remove

    Returns:
        Formatted success or error response
    """
    try:
        if not attachment_id and not filename:
            return format_error(
                code="MISSING_PARAMS",
                message="Must specify either attachment_id or filename",
            )
        
        # Get current memo
        id_val = str(memo_id).split("/")[-1]
        memo_response = await client.get(f"/memos/{id_val}")
        
        if memo_response.get("error"):
            return format_error(
                code="GET_MEMO_FAILED",
                message=memo_response["error"].get("message", "Memo not found"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )
        
        memo = memo_response
        existing_resources = memo.get("resources", [])
        
        # Remove target resource
        if attachment_id:
            # Handle string comparison carefully
            target_id = str(attachment_id).split("/")[-1]
            remaining_resources = [
                r for r in existing_resources 
                if str(r.get("id") or r.get("name")).split("/")[-1] != target_id
            ]
        else:
            remaining_resources = [r for r in existing_resources if r.get("filename") != filename]
        
        if len(remaining_resources) == len(existing_resources):
            return format_error(
                code="ATTACHMENT_NOT_FOUND",
                message=f"Attachment not found",
            )
        
        # Update memo
        resource_ids = [r.get("id") or r.get("name") for r in remaining_resources]
        clean_ids = [str(rid).split("/")[-1] for rid in resource_ids if rid]
        
        # API V1 expects 'attachments' list of objects with 'name'
        attachments_payload = []
        for rid in clean_ids:
             attachments_payload.append({"name": f"attachments/{rid}"})

        params = {"updateMask": "attachments"}
        
        response = await client.patch(f"/memos/{id_val}", params=params, json={"attachments": attachments_payload})
        
        if response.get("error"):
            return format_error(
                code="REMOVE_ATTACHMENT_FAILED",
                message=response["error"].get("message", "Failed to remove attachment"),
            )
        
        memo = response
        formatted = format_memo_to_json(memo)
        
        return format_success(formatted, {
            "message": "Attachment removed successfully",
        })
    
    except Exception as e:
        return format_error(
            code="REMOVE_ATTACHMENT_ERROR",
            message=str(e),
        )

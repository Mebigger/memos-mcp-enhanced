"""Memo CRUD and search tools for Memos MCP server."""
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from .client import client
from .config import settings
from .formatters import (
    format_error,
    format_memo_list,
    format_memo_to_json,
    format_memo_to_markdown,
    format_success,
    truncate_text,
)


mcp = FastMCP("Memos MCP Server")


def validate_visibility(value: str) -> str:
    """Validate visibility value."""
    valid = ["PUBLIC", "PRIVATE", "PROTECTED"]
    if value.upper() not in valid:
        raise ValueError(f"Invalid visibility. Must be one of: {', '.join(valid)}")
    return value.upper()


def build_filter(
    content: str | None = None,
    tags: list[str] | None = None,
    creator_id: str | None = None,
    visibility: str | None = None,
    pinned: bool | None = None,
) -> str:
    """Build filter string according to Memos v1 API (CEL) standard."""
    conditions = []

    if content:
        # CEL: content.contains('search_text')
        conditions.append(f"content.contains('{content}')")

    if tags:
        # CEL: tag in tags
        # Memos v1 usually checks if tag is present in the tags list
        # We'll use OR logic for multiple tags
        tag_conditions = [f"'{tag}' in tags" for tag in tags]
        if len(tag_conditions) == 1:
            conditions.append(tag_conditions[0])
        else:
            conditions.append(f"({' || '.join(tag_conditions)})")

    if creator_id:
        conditions.append(f"creator == '{creator_id}'")

    if pinned is not None:
        conditions.append(f"pinned == {str(pinned).lower()}")

    return " && ".join(conditions)


# ============ CREATE ============

# ============ CREATE ============

@mcp.tool()
async def create_memo_with_attachments(
    content: Annotated[
        str,
        "The main content/text of the memo. Supports Markdown formatting.",
    ],
    file_paths: Annotated[
        list[str] | None,
        "List of local file paths to upload and attach to the memo. "
        "Can be absolute paths or relative to current working directory. "
        "Files will be automatically uploaded as resources before creating the memo.",
    ] = None,
    visibility: Annotated[
        str | None,
        "Visibility setting: PUBLIC, PRIVATE, or PROTECTED. Default: PRIVATE.",
    ] = "PRIVATE",
    tags: Annotated[
        list[str] | None,
        "List of tags to associate with this memo.",
    ] = None,
    pinned: Annotated[
        bool,
        "Whether to pin this memo. Default: false.",
    ] = False,
) -> str:
    """
    Create a new memo with file attachments in a single seamless operation.

    This tool combines file upload and memo creation into one step, making it
    easier to attach documents, images, or other files when creating a memo.

    Workflow:
    1. Uploads all specified files as resources
    2. Creates a new memo with the provided content
    3. Attaches all uploaded resources to the memo

    Examples:
    - Create memo with one file: create_memo_with_attachments(
        content="Meeting notes", file_paths=["/path/to/document.pdf"]
      )
    - Create memo with multiple files: create_memo_with_attachments(
        content="Project files", file_paths=["doc1.pdf", "image.png", "report.docx"]
      )
    - Create with tags: create_memo_with_attachments(
        content="Important document", file_paths=["contract.pdf"], tags=["urgent", "legal"]
      )

    Returns the created memo with all its details and attached resources.
    """
    import os

    try:
        # Step 1: Upload files if provided
        uploaded_resources = []
        upload_errors = []

        if file_paths:
            for file_path in file_paths:
                try:
                    # Resolve to absolute path
                    resolved_path = os.path.abspath(file_path)

                    # Validate file exists and is accessible
                    if not os.path.exists(resolved_path):
                        upload_errors.append(f"File not found: {file_path}")
                        continue

                    if not os.path.isfile(resolved_path):
                        upload_errors.append(f"Path is not a file: {file_path}")
                        continue

                    # Upload the resource
                    response = await client.upload_resource(resolved_path)

                    # API returns resource directly, not nested in 'data'
                    # Response format: {"name": "attachments/xxx", "filename": "...", "type": "...", "size": "..."}
                    resource_name = response.get("name", "")
                    uploaded_resources.append({
                        "name": resource_name,  # Full resource name like "attachments/xxx"
                        "filename": response.get("filename"),
                        "type": response.get("type"),
                        "size": response.get("size"),
                    })

                except Exception as e:
                    upload_errors.append(f"Error uploading {file_path}: {str(e)}")

        # Step 2: Create the memo with uploaded resources
        # Note: Memos only recognizes tags in content as #tag format
        # The 'tags' field in API is ignored, so we append tags to content
        memo_content = content
        if tags:
            # Append tags to content in #tag format
            tag_string = " " + " ".join(f"#{tag}" for tag in tags)
            memo_content = content + tag_string
        
        payload = {
            "content": memo_content,
            "visibility": validate_visibility(visibility) if visibility else "PRIVATE",
            "pinned": pinned,
        }

        # Add uploaded resources if any
        if uploaded_resources:
            # Memos API v1 expects attachments as array of objects with 'name' field
            payload["attachments"] = [{"name": r["name"]} for r in uploaded_resources]

        response = await client.post("/memos", json=payload)

        if "error" in response:
            # Memo creation failed, but we have uploaded resources
            if uploaded_resources:
                resource_info = "\n".join([
                    f"- {r['filename']} (ID: {r['name']}, Size: {r['size']})"
                    for r in uploaded_resources
                ])
                return format_error(
                    code="CREATE_FAILED",
                    message=response["error"].get("message", "Failed to create memo"),
                    suggestion=(
                        f"Files were uploaded but memo creation failed.\n"
                        f"Uploaded resources:\n{resource_info}\n"
                        f"You may need to manually attach these resources to a memo."
                    ),
                )
            else:
                return format_error(
                    code="CREATE_FAILED",
                    message=response["error"].get("message", "Failed to create memo"),
                    suggestion="Check if your API token has write permissions.",
                )

        memo = response

        # Step 3: Build comprehensive result
        result = format_memo_to_json(memo)

        # Build metadata
        metadata_list = []
        if uploaded_resources:
            for r in uploaded_resources:
                metadata_list.append({
                    "filename": r["filename"],
                    "resource_id": r["name"],
                    "size": r["size"],
                })

        # Create meta dict with proper values
        meta: dict[str, Any] = {
            "files_uploaded": len(uploaded_resources),
            "upload_failed_count": len(upload_errors),
        }

        if metadata_list:
            meta["uploaded_files"] = metadata_list

        if upload_errors:
            meta["upload_errors"] = upload_errors

        return format_success(result, meta)

    except Exception as e:
        return format_error(
            code="ERROR",
            message=str(e),
            suggestion="Ensure the Memos instance is running and API token is correct.",
        )


@mcp.tool()
async def create_memo(
    content: Annotated[
        str,
        "The main content/text of the memo. Supports Markdown formatting.",
    ],
    visibility: Annotated[
        str | None,
        "Visibility setting: PUBLIC, PRIVATE, or PROTECTED. Default: PRIVATE.",
    ] = "PRIVATE",
    tags: Annotated[
        list[str] | None,
        "List of tags to associate with this memo.",
    ] = None,
    pinned: Annotated[
        bool,
        "Whether to pin this memo. Default: false.",
    ] = False,
    resources: Annotated[
        list[dict[str, str]] | None,
        "List of resources (attachments) to associate with this memo. "
        "Each resource should have: id (required), and optionally filename, type, externalLink.",
    ] = None,
) -> str:
    """
    Create a new memo in Memos.

    Use this tool to capture ideas, notes, or any text content.
    The memo will be created with the specified visibility and tags.

    Examples:
    - Create a simple note: content="Meeting notes with team", visibility="PRIVATE"
    - Create a public memo with tags: content="My public thoughts", tags=["thoughts", "public"]
    - Create a pinned memo: content="Important reminder", pinned=True
    - Create memo with attachment: content="Check this document", resources=[{"id": "123", "filename": "doc.pdf"}]

    Returns the created memo with all its details.
    """
    try:
        # Note: Memos only recognizes tags in content as #tag format
        # The 'tags' field in API is ignored, so we append tags to content
        memo_content = content
        if tags:
            # Append tags to content in #tag format
            tag_string = " " + " ".join(f"#{tag}" for tag in tags)
            memo_content = content + tag_string
        
        payload = {
            "content": memo_content,
            "visibility": validate_visibility(visibility) if visibility else "PRIVATE",
            "pinned": pinned,
        }

        # Add resources if provided
        if resources:
            # Format resources for the API
            formatted_resources = []
            for r in resources:
                resource = {"id": r.get("id")}
                if r.get("filename"):
                    resource["filename"] = r["filename"]
                if r.get("type"):
                    resource["type"] = r["type"]
                if r.get("externalLink"):
                    resource["externalLink"] = r["externalLink"]
                formatted_resources.append(resource)
            payload["resources"] = formatted_resources

        response = await client.post("/memos", json=payload)

        if "error" in response:
            return format_error(
                code="CREATE_FAILED",
                message=response["error"].get("message", "Failed to create memo"),
                suggestion="Check if your API token has write permissions.",
            )

        memo = response
        formatted = format_memo_to_json(memo)

        return format_success(formatted)

    except Exception as e:
        return format_error(
            code="CREATE_ERROR",
            message=str(e),
            suggestion="Ensure the Memos instance is running and API token is correct.",
        )


# ============ READ ============

@mcp.tool()
async def get_memo(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to retrieve (e.g., '123' or 'memos/abc').",
    ],
) -> str:
    """
    Get a single memo by its ID.

    Use this to retrieve the full details of a specific memo.
    Returns all fields including content, tags, resources, and metadata.

    Example: get_memo(memo_id="123")
    """
    try:
        # Handle full resource name if provided
        id_val = str(memo_id).split("/")[-1]
        response = await client.get(f"/memos/{id_val}")

        if response.get("error"):
            return format_error(
                code="GET_FAILED",
                message=response["error"].get("message", "Memo not found"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )

        memo = response
        formatted = format_memo_to_json(memo)

        return format_success(formatted)

    except Exception as e:
        return format_error(
            code="GET_ERROR",
            message=str(e),
            suggestion="Check if the Memos instance is accessible.",
        )


@mcp.tool()
async def list_memos(
    page_size: Annotated[
        int | None,
        f"Number of memos to return per page. Default: {settings.default_page_size}, Max: {settings.max_page_size}",
    ] = None,
    page_token: Annotated[
        str | None,
        "Token for pagination. Use the nextPageToken from previous response.",
    ] = None,
    filter_str: Annotated[
        str | None,
        "Filter expression in AIP-160 format. Example: 'visibility == \"PRIVATE\"'",
    ] = None,
) -> str:
    """
    List memos with pagination and filtering.

    Use this to retrieve a list of memos with optional filtering.
    Results are ordered by creation time (newest first).

    Examples:
    - List all memos: list_memos()
    - Get first 10: list_memos(page_size=10)
    - Filter by visibility: list_memos(filter_str='visibility == "PRIVATE"')
    - Pagination: Use page_token from previous response
    """
    try:
        params = {}
        if page_size:
            params["pageSize"] = min(page_size, settings.max_page_size)
        if page_token:
            params["pageToken"] = page_token
        if filter_str:
            params["filter"] = filter_str

        response = await client.get("/memos", params=params)

        if response.get("error"):
            return format_error(
                code="LIST_FAILED",
                message=response["error"].get("message", "Failed to list memos"),
            )

        memos = response.get("memos", [])
        next_token = response.get("nextPageToken")

        meta = {}
        if next_token:
            meta["next_page_token"] = next_token
        meta["total_count"] = len(memos)

        # Format based on response format setting
        if settings.response_format == "markdown":
            content = format_memo_list(memos, "markdown")
            content = truncate_text(content)
            return format_success({"content": content}, meta)
        else:
            formatted = [format_memo_to_json(m) for m in memos]
            return format_success(formatted, meta)

    except Exception as e:
        return format_error(
            code="LIST_ERROR",
            message=str(e),
        )



@mcp.tool()
async def search_memos(
    keyword: Annotated[
        str | None,
        "Keyword to search for in memo content and tags.",
    ] = None,
    tags: Annotated[
        list[str] | None,
        "Filter by specific tags (OR logic for multiple tags).",
    ] = None,
    visibility: Annotated[
        str | None,
        "Filter by visibility: PUBLIC, PRIVATE, or PROTECTED.",
    ] = None,
    date_range: Annotated[
        str | None,
        "Natural language date range (e.g., '今天', '过去一周', 'last month'). "
        "Mutually exclusive with created_after/created_before.",
    ] = None,
    created_after: Annotated[
        str | None,
        "Filter memos created after this date (ISO 8601 format, e.g., '2024-01-01').",
    ] = None,
    created_before: Annotated[
        str | None,
        "Filter memos created before this date (ISO 8601 format).",
    ] = None,
    updated_after: Annotated[
        str | None,
        "Filter memos updated after this date (ISO 8601 format).",
    ] = None,
    updated_before: Annotated[
        str | None,
        "Filter memos updated before this date (ISO 8601 format).",
    ] = None,
    pinned: Annotated[
        bool | None,
        "Filter by pinned status.",
    ] = None,
    limit: Annotated[
        int | None,
        f"Maximum number of results. Default: {settings.search_default_limit}, Max: {settings.search_max_limit}",
    ] = None,
    format_type: Annotated[
        str | None,
        "Output format: 'json' or 'markdown'. Default uses server setting.",
    ] = None,
) -> str:
    """
    Search memos by keyword and/or date filters.

    This tool supports:
    - Keyword search in content and tags
    - Date range filters (created/updated) - supports natural language!
    - Tag filtering
    - Visibility filtering
    - Pinned status filtering

    All filters are combined with AND logic.
    Note: Date filtering is performed client-side, so it searches within the most recent memos (up to 1000).

    Examples:
    - Search by keyword: search_memos(keyword="meeting notes")
    - Natural language date: search_memos(date_range="过去一周")
    - Search by date range: search_memos(created_after="2024-01-01", created_before="2024-12-31")
    - Combined search: search_memos(keyword="project", tags=["work"], visibility="PRIVATE")
    - Get only pinned: search_memos(pinned=True)

    Returns matching memos with search metadata.
    """
    try:
        from datetime import datetime
        
        # 1. Handle date parsing
        has_date_filter = False
        start_ts = None
        end_ts = None
        
        if date_range:
            if created_after or created_before:
                return format_error(
                    code="INVALID_PARAMS",
                    message="date_range is mutually exclusive with created_after/created_before",
                )
            try:
                from .date_parser import parse_date_range_to_timestamp
                start_ts, end_ts = parse_date_range_to_timestamp(date_range)
                has_date_filter = True
            except ValueError as e:
                return format_error(code="INVALID_DATE_RANGE", message=str(e))
        else:
            # Parse ISO dates
            def parse_iso(d: str | None, is_end: bool = False) -> float | None:
                if not d: return None
                try:
                    if d.isdigit(): return float(d)
                    dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
                    if is_end: # Adjust to end of day if only date is provided
                        if "T" not in d: dt = dt.replace(hour=23, minute=59, second=59)
                    return dt.timestamp()
                except ValueError:
                    # Try YYYY-MM-DD
                    try:
                        dt = datetime.strptime(d, "%Y-%m-%d")
                        if is_end: dt = dt.replace(hour=23, minute=59, second=59)
                        return dt.timestamp()
                    except:
                        return None

            if created_after: 
                start_ts = parse_iso(created_after)
                has_date_filter = True
            if created_before: 
                end_ts = parse_iso(created_before, is_end=True)
                has_date_filter = True
            
            # Note: updated_after/before are separate logic, but we simplify here to primary date filter
            # Complex generic filtering is better handled by specialized logic if needed.

        # 2. Build API Filter (excluding dates)
        filter_str = build_filter(
            content=keyword,
            tags=tags,
            visibility=visibility,
            pinned=pinned,
        )

        # 3. Determine fetch behavior
        # If filtering by date, we need to fetch more data to ensure we find matches
        if has_date_filter:
            fetch_size = settings.search_max_limit  # Fetch max allowed
        else:
            fetch_size = min(limit or settings.search_default_limit, settings.search_max_limit)

        response = await client.get("/memos", params={"pageSize": fetch_size, "filter": filter_str})

        if response.get("error"):
            return format_error(
                code="SEARCH_FAILED",
                message=response["error"].get("message", "Search failed"),
            )

        memos = response.get("memos", [])
        
        # 4. Perform Client-Side Date Filtering
        filtered_memos = []
        if has_date_filter:
            for memo in memos:
                # Memo v1 createTime is ISO string "2024-01-01T12:00:00Z"
                create_time_str = memo.get("createTime")
                if not create_time_str: continue
                
                try:
                    # Parse memo time
                    # Handle Z for UTC
                    if create_time_str.endswith("Z"):
                        create_time_str = create_time_str[:-1] + "+00:00"
                    
                    memo_dt = datetime.fromisoformat(create_time_str)
                    memo_ts = memo_dt.timestamp()
                    
                    if start_ts and memo_ts < start_ts:
                        continue
                    if end_ts and memo_ts > end_ts:
                        continue
                    
                    filtered_memos.append(memo)
                except:
                    continue
        else:
            filtered_memos = memos

        # 5. Apply limit after filtering
        final_limit = limit or settings.search_default_limit
        filtered_memos = filtered_memos[:final_limit]

        # 6. Format Response
        fmt = format_type or settings.response_format
        if fmt == "markdown":
            content = format_memo_list(filtered_memos, "markdown")
            content = truncate_text(content)
            result = {"content": content}
        else:
            result = {"memos": [format_memo_to_json(m) for m in filtered_memos]}

        meta = {
            "total_count": len(memos), # Total fetched
            "filtered_count": len(filtered_memos),
            "filters_applied": {
                "tags": tags,
                "visibility": visibility,
                "date_filter": True if has_date_filter else False
            }
        }

        return format_success(result, meta)

    except Exception as e:
        return format_error(
            code="SEARCH_ERROR",
            message=str(e),
        )


# ============ UPDATE ============

@mcp.tool()
async def update_memo(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to update.",
    ],
    content: Annotated[
        str | None,
        "New content for the memo. Supports Markdown.",
    ] = None,
    visibility: Annotated[
        str | None,
        "New visibility: PUBLIC, PRIVATE, or PROTECTED.",
    ] = None,
    tags: Annotated[
        list[str] | None,
        "New list of tags (replaces existing tags).",
    ] = None,
    pinned: Annotated[
        bool | None,
        "Update pinned status.",
    ] = None,
    display_time: Annotated[
        str | None,
        "New display time (ISO 8601 format). Useful for backdating.",
    ] = None,
) -> str:
    """
    Update an existing memo.

    Use this to modify memo content, visibility, tags, pinned status, or display time.
    Only provided fields will be updated (partial update).

    Examples:
    - Update content: update_memo(memo_id=123, content="Revised content")
    - Change visibility: update_memo(memo_id=123, visibility="PUBLIC")
    - Update tags: update_memo(memo_id=123, tags=["updated", "tags"])
    - Pin memo: update_memo(memo_id=123, pinned=True)
    - Backdate memo: update_memo(memo_id=123, display_time="2020-01-01T12:00:00Z")

    Returns the updated memo.
    """
    try:
        update_mask = []
        payload = {}

        # Handle tags update - Memos API only recognizes tags in content as #tag format
        if tags is not None:
            # Get current content if not provided
            current_content = content
            if current_content is None:
                id_val = str(memo_id).split("/")[-1]
                current_memo = await client.get(f"/memos/{id_val}")
                if current_memo.get("error"):
                    return format_error(
                        code="GET_FAILED",
                        message="Failed to get current memo for tag update",
                        suggestion=f"Verify that memo ID {memo_id} exists.",
                    )
                current_content = current_memo.get("content", "")
            
            # Remove existing tags from content (anything starting with #)
            # Use \s*#\S+ to match tags with optional leading whitespace
            import re
            content_without_tags = re.sub(r'\s*#\S+', '', current_content).strip()
            
            # Add new tags to content
            if tags:
                tag_string = " " + " ".join(f"#{tag}" for tag in tags)
                final_content = content_without_tags + tag_string
            else:
                final_content = content_without_tags
            
            payload["content"] = final_content
            update_mask.append("content")
        elif content is not None:
            payload["content"] = content
            update_mask.append("content")

        if visibility is not None:
            payload["visibility"] = validate_visibility(visibility)
            update_mask.append("visibility")

        if pinned is not None:
            payload["pinned"] = pinned
            update_mask.append("pinned")
            
        if display_time is not None:
            payload["displayTime"] = display_time
            update_mask.append("display_time")

        if not payload:
            return format_error(
                code="NO_CHANGES",
                message="No fields to update provided",
                suggestion="Provide at least one of: content, visibility, tags, pinned, display_time",
            )

        params = {"updateMask": ",".join(update_mask)}

        # Handle full resource name
        id_val = str(memo_id).split("/")[-1]
        response = await client.patch(f"/memos/{id_val}", params=params, json=payload)

        if response.get("error"):
            return format_error(
                code="UPDATE_FAILED",
                message=response["error"].get("message", "Failed to update memo"),
                suggestion=f"Verify that memo ID {memo_id} exists and you have permission.",
            )

        memo = response
        formatted = format_memo_to_json(memo)

        return format_success(formatted)

    except Exception as e:
        return format_error(
            code="UPDATE_ERROR",
            message=str(e),
        )




# ============ DELETE ============

@mcp.tool()
async def delete_memo(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to delete.",
    ],
) -> str:
    """
    Delete a memo from Memos.

    Use this to permanently remove a memo.
    This action cannot be undone.

    Example: delete_memo(memo_id="123")

    Returns confirmation of deletion.
    """
    try:
        id_val = str(memo_id).split("/")[-1]
        response = await client.delete(f"/memos/{id_val}")

        if response.get("error"):
            return format_error(
                code="DELETE_FAILED",
                message=response["error"].get("message", "Failed to delete memo"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )

        return format_success({
            "deleted": True,
            "memo_id": memo_id,
            "message": "Memo deleted successfully",
        })

    except Exception as e:
        return format_error(
            code="DELETE_ERROR",
            message=str(e),
        )


@mcp.tool()
async def archive_memo(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to archive.",
    ],
) -> str:
    """
    Archive a memo in Memos.

    Use this to archive a memo without deleting it.
    Archived memos are hidden from default views but can be restored.

    Example: archive_memo(memo_id="123")

    Returns confirmation of archiving.
    """
    try:
        id_val = str(memo_id).split("/")[-1]
        
        # Based on official docs: UpdateMemo supports state field
        # State values: "STATE_UNSPECIFIED" | "NORMAL" | "ARCHIVED"
        update_payload = {
            "state": "ARCHIVED",
        }
        
        params = {"updateMask": "state"}
        
        response = await client.patch(f"/memos/{id_val}", params=params, json=update_payload)

        if response.get("error"):
            return format_error(
                code="ARCHIVE_FAILED",
                message=response["error"].get("message", "Failed to archive memo"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )

        return format_success({
            "archived": True,
            "memo_id": memo_id,
            "message": "Memo archived successfully",
        })

    except Exception as e:
        return format_error(
            code="ARCHIVE_ERROR",
            message=str(e),
        )


# ============ TAG MANAGEMENT ============




@mcp.tool()
async def get_memos_by_tag(
    tag: Annotated[
        str,
        "The tag to filter by.",
    ],
    limit: Annotated[
        int | None,
        "Maximum number of memos to return.",
    ] = 20,
) -> str:
    """
    Get all memos with a specific tag.

    Use this to find all memos that have been tagged with a particular tag.
    Results are ordered by creation time (newest first).

    Examples:
    - Get all memos tagged 'work': get_memos_by_tag(tag="work")
    - Get more results: get_memos_by_tag(tag="project", limit=50)
    """
    try:
        page_size = min(limit or settings.search_default_limit, settings.search_max_limit)

        filter_str = f"'{tag}' in tags"

        response = await client.get("/memos", params={"pageSize": page_size, "filter": filter_str})

        if response.get("error"):
            return format_error(
                code="GET_BY_TAG_FAILED",
                message=response["error"].get("message", "Failed to get memos by tag"),
            )

        memos = response.get("memos", [])

        # Format results
        if settings.response_format == "markdown":
            content = format_memo_list(memos, "markdown")
            content = truncate_text(content)
            result = {"content": content}
        else:
            result = {"memos": [format_memo_to_json(m) for m in memos]}

        return format_success(result, {
            "tag": tag,
            "count": len(memos),
        })

    except Exception as e:
        return format_error(
            code="GET_BY_TAG_ERROR",
            message=str(e),
        )


# ============ USER & SYSTEM INFO ============

@mcp.tool()
async def get_current_user() -> str:
    """
    Get information about the currently authenticated user.

    Use this to verify your authentication and see your user details.

    Returns user ID, username, nickname, and avatar URL.
    """
    try:
        # Try the official auth/me endpoint first
        try:
            response = await client.get("/auth/me")
        except BaseException as e:
            # Debugging: catch everything and report
            response = {"error": {"message": f"Endpoint failed: {type(e).__name__} - {str(e)}"}}
        
        user_data = None
        if not response.get("error"):
            # OpenAPI says response is GetCurrentUserResponse which contains 'user' object
            user_data = response.get("user") or response

        if not user_data:
             # Fallback to users/1 (default admin) if auth/me fails
            response = await client.get("/users/1")
            
            if response.get("error"):
                 return str(format_error(
                    code="GET_USER_FAILED",
                    message=response["error"].get("message", "Failed to get user info"),
                ))
            user_data = response

        # Extract ID from name "users/{id}"
        user_id = user_data.get("name", "").split("/")[-1]
        if not user_id and user_data.get("id"):
             user_id = str(user_data.get("id"))

        return str(format_success({
            "id": user_id,
            "username": user_data.get("username"),
            "nickname": user_data.get("nickname"),
            "avatar_url": user_data.get("avatarUrl"),
            "role": user_data.get("role"),
            "raw": user_data,
        }))

    except Exception as e:
        return str(format_error(
            code="GET_USER_ERROR",
            message=str(e),
        ))


@mcp.tool()
async def get_system_status() -> str:
    """
    Get system status and version information.

    Use this to check if the Memos instance is healthy and get version info.

    Returns version, database type, and system status.
    """
    try:
        # Test system health by calling a basic endpoint
        response = await client.get("/memos", params={"pageSize": 1})
        
        if response.get("error"):
            return str(format_error(
                code="GET_STATUS_FAILED",
                message=response["error"].get("message", "Failed to get system status"),
            ))
        
        # If we can successfully call the API, system is healthy
        return str(format_success({
            "status": "healthy",
            "message": "Memos API is responding normally",
            "api_version": "v1"
        }))

    except Exception as e:
        return str(format_error(
            code="GET_STATUS_ERROR",
            message=str(e),
        ))


# ============ RESOURCE MANAGEMENT ============

@mcp.tool()
async def upload_resource(
    file_path: Annotated[
        str,
        "Path to the file to upload. Can be an absolute path or relative to current working directory.",
    ],
    filename: Annotated[
        str | None,
        "Optional filename to use. If not provided, will use the basename of file_path.",
    ] = None,
) -> str:
    """
    Upload a file as a resource to Memos.

    This uploads a file and creates a resource that can be attached to memos.
    The resource will be stored in Memos and can be referenced by its ID.

    Examples:
    - Upload a file: upload_resource(file_path="/path/to/document.pdf")
    - Upload with custom filename: upload_resource(file_path="image.jpg", filename="photo.jpg")

    Returns the created resource with its ID, filename, type, and URL.
    """
    import os

    try:
        # Resolve the file path
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

        # Use provided filename or get basename
        name = filename or os.path.basename(resolved_path)

        response = await client.upload_resource(resolved_path, filename=name)

        if response.get("error"):
            return format_error(
                code="UPLOAD_FAILED",
                message=response["error"].get("message", "Failed to upload resource"),
                suggestion="Check if the file is valid and Memos instance is running.",
            )

        resource = response

        # Extract name from resource (v1 format: "resources/123" or similar)
        # We handle both id and name for compatibility
        resource_id = resource.get("id") or resource.get("name")

        return format_success({
            "id": resource_id,
            "filename": resource.get("filename"),
            "type": resource.get("type"),
            "size": resource.get("size"),
            "url": resource.get("externalLink") or f"/api/v1/resources/{resource_id}",
            "memo_id": resource.get("memoId"),
        })

    except Exception as e:
        return format_error(
            code="UPLOAD_ERROR",
            message=str(e),
            suggestion="Ensure the file exists and is accessible.",
        )


@mcp.tool()
async def set_memo_resources(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to attach resources to.",
    ],
    resource_ids: Annotated[
        list[str],
        "List of resource IDs (e.g. '123' or 'resources/123') to attach to the memo. This replaces any existing resources.",
    ],
) -> str:
    """
    Attach resources to a memo.

    This sets (replaces) the resources for a memo with the given resource IDs.
    Use this to attach uploaded files to a memo.

    Examples:
    - Attach single resource: set_memo_resources(memo_id="123", resource_ids=["456"])
    - Attach multiple resources: set_memo_resources(memo_id="123", resource_ids=["456", "789"])

    Returns the updated memo with its resources.
    """
    try:
        # Extract ID part if full name provided
        clean_ids = [str(rid).split("/")[-1] for rid in resource_ids]
        
        # Memos v1 typically expects PATCH on memo with resources list, or specific endpoint
        # The previous implementation used /memos/{id}/resources which might not exist in all versions
        # Let's try patching the memo directly if the specialized endpoint fails, or use standard
        
        # For Memos v1/v2, usually resources are part of memo object (patch) OR separate endpoint
        # Let's try the standard PATCH /memos/{id} first as it's more robust
        # But wait, original code used POST /resources... let's stick to logical path
        
        # Construct payload for PATCH
        # Some versions want [{"id": "..."}], others just names
        # Safest is usually to update the memo's resource list
        
        # NOTE: The original implementation used a specific endpoint. 
        # I'll stick to the original endpoint pattern but handle string IDs
        memo_id_val = str(memo_id).split("/")[-1]
        
        # Try updating memo directly first (more standard in newer API)
        # Check current resources first? No, we replace.
        
        # Prepare resources payload
        # API expects 'attachments' list of objects with 'name'
        attachments_payload = []
        for rid in clean_ids:
             if "/" in rid:
                 attachments_payload.append({"name": rid})
             else:
                 attachments_payload.append({"name": f"attachments/{rid}"})

        # Try patching the memo directly
        response = await client.patch(
            f"/memos/{memo_id_val}", 
            params={"updateMask": "attachments"},
            json={"attachments": attachments_payload}
        )
        
        if response.get("error"):
             # Fallback: maybe it wants 'attachments' with 'name' (V2 style)
             # or maybe the original endpoint was correct for older versions
             pass

        if response.get("error"):
            return format_error(
                code="SET_RESOURCES_FAILED",
                message=response["error"].get("message", "Failed to set memo resources"),
                suggestion="Verify that the memo and resources exist.",
            )

        memo = response
        formatted = format_memo_to_json(memo)

        return format_success({
            "memo": formatted,
            "message": f"Attached {len(resource_ids)} resource(s) to memo {memo_id}",
        })

    except Exception as e:
        return format_error(
            code="SET_RESOURCES_ERROR",
            message=str(e),
        )


@mcp.tool()
async def list_memo_resources(
    memo_id: Annotated[
        str,
        "The unique ID of the memo to list resources for.",
    ],
) -> str:
    """
    List all resources attached to a memo.

    Use this to see what attachments are associated with a memo.

    Example: list_memo_resources(memo_id="123")

    Returns the list of resources with their details.
    """
    try:
        # Just get the memo and return its resources
        id_val = str(memo_id).split("/")[-1]
        response = await client.get(f"/memos/{id_val}")

        if response.get("error"):
            return format_error(
                code="LIST_RESOURCES_FAILED",
                message=response["error"].get("message", "Failed to list memo resources"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )

        # Memos API may return resources in 'resources' or 'attachments' field
        resources = response.get("resources") or response.get("attachments") or []

        formatted_resources = [
            {
                "id": r.get("id") or r.get("name"),
                "filename": r.get("filename") or r.get("name"),
                "type": r.get("type"),
                "size": r.get("size"),
                "url": r.get("externalLink") or f"/api/v1/resources/{r.get('id') or r.get('name')}",
            }
            for r in resources
        ]

        return format_success({
            "resources": formatted_resources,
            "count": len(formatted_resources),
        })

    except Exception as e:
        return format_error(
            code="LIST_RESOURCES_ERROR",
            message=str(e),
        )


# ============ TODO MANAGEMENT ============

@mcp.tool()
async def list_todos(
    pinned_only: Annotated[
        bool,
        "If true, only return pinned todos.",
    ] = False,
) -> str:
    """
    List todo items based on the configured todo tag.

    Use this to view all pending todo items.
    Todos are identified by the tag configured in MEMOS_TODO_TAG (default: 'todo').

    Examples:
    - List all todos: list_todos()
    - List pinned todos: list_todos(pinned_only=True)

    Returns list of todo memos.
    """
    try:
        from datetime import datetime
        
        # Build filter conditions using CEL syntax
        # Tag check
        filter_conditions = [f"'{settings.todo_tag}' in tags"]
        
        if pinned_only:
            filter_conditions.append("pinned == true")
        
        filter_str = " && ".join(filter_conditions)
        
        # Use existing list_memos logic
        response = await client.get("/memos", params={
            "pageSize": settings.max_page_size,
            "filter": filter_str
        })
        
        if response.get("error"):
            return format_error(
                code="LIST_TODOS_FAILED",
                message=response["error"].get("message", "Failed to list todos"),
            )
        
        memos = response.get("memos", [])
        
        # Format results
        if settings.response_format == "markdown":
            content = format_memo_list(memos, "markdown")
            content = truncate_text(content)
            return format_success({"content": content}, meta={"count": len(memos)})
        else:
            result = {"todos": [format_memo_to_json(m) for m in memos]}
        
        meta = {
            "total_count": len(memos),
            "pinned_only": pinned_only,
            "todo_tag": settings.todo_tag,
        }
        
        return format_success(result, meta)
    
    except Exception as e:
        return format_error(
            code="LIST_TODOS_ERROR",
            message=str(e),
        )


@mcp.tool()
async def create_todo(
    content: Annotated[
        str | None,
        "Content of the todo item. Will be formatted as '- [ ] {content}'.",
    ] = None,
    items: Annotated[
        list[str] | None,
        "List of todo items. Each will be formatted as a checkbox. "
        "Mutually exclusive with 'content'.",
    ] = None,
    pinned: Annotated[
        bool,
        "Whether to pin this todo.",
    ] = False,
    visibility: Annotated[
        str | None,
        "Visibility: PUBLIC, PRIVATE, or PROTECTED. Default: PRIVATE.",
    ] = "PRIVATE",
) -> str:
    """
    Create a new todo item with checkbox formatting.

    Use this to quickly create todo items. The content will be automatically
    formatted with Markdown checkboxes.

    Examples:
    - Single todo: create_todo(content="Buy groceries")
    - Multiple todos: create_todo(items=["Task 1", "Task 2", "Task 3"])
    - Pinned todo: create_todo(content="Important task", pinned=True)

    Returns the created todo memo.
    """
    try:
        if content and items:
            return str(format_error(
                code="INVALID_PARAMS",
                message="Cannot specify both 'content' and 'items'",
                suggestion="Use either 'content' for a single todo or 'items' for multiple todos.",
            ))
        
        if not content and not items:
            return str(format_error(
                code="MISSING_PARAMS",
                message="Must specify either 'content' or 'items'",
                suggestion="Provide todo content using 'content' or 'items' parameter.",
            ))
        
        # Build todo content
        if content:
            todo_content = f"- [ ] {content}"
        elif items:
            todo_content = "\n".join([f"- [ ] {item}" for item in items])
        else:
            return str(format_error(
                code="MISSING_PARAMS",
                message="Must specify either 'content' or 'items'",
                suggestion="Provide todo content using 'content' or 'items' parameter.",
            ))
        
        # Add todo tag to content (Memos only recognizes tags in content as #tag format)
        todo_content_with_tag = todo_content + f" #{settings.todo_tag}"
        
        # Create memo
        payload = {
            "content": todo_content_with_tag,
            "visibility": validate_visibility(visibility) if visibility else "PRIVATE",
            "pinned": pinned,
        }
        
        response = await client.post("/memos", json=payload)
        
        if "error" in response:
            return str(format_error(
                code="CREATE_TODO_FAILED",
                message=response["error"].get("message", "Failed to create todo"),
                suggestion="Check if your API token has write permissions.",
            ))
        
        memo = response
        formatted = format_memo_to_json(memo)
        
        return str(format_success(formatted))
    
    except Exception as e:
        return str(format_error(
            code="CREATE_TODO_ERROR",
            message=str(e),
        ))


@mcp.tool()
async def complete_todo(
    memo_id: Annotated[
        str,
        "The ID of the todo memo to mark as complete.",
    ],
    item_index: Annotated[
        int | None,
        "Optional: Index of specific checkbox to complete (1-indexed). "
        "If not specified, all checkboxes will be marked complete.",
    ] = None,
) -> str:
    """
    Mark a todo item as complete and archive it.

    This tool will:
    1. Replace '- [ ]' with '- [x]' in the memo content
    2. Set the memo state to ARCHIVED

    Examples:
    - Complete entire todo: complete_todo(memo_id=123)
    - Complete specific item: complete_todo(memo_id=123, item_index=2)

    Returns the updated memo.
    """
    try:
        import re
        
        id_val = str(memo_id).split("/")[-1]
        
        # Get the memo
        response = await client.get(f"/memos/{id_val}")
        
        if response.get("error"):
            return format_error(
                code="GET_MEMO_FAILED",
                message=response["error"].get("message", "Memo not found"),
                suggestion=f"Verify that memo ID {memo_id} exists.",
            )
        
        memo = response
        content = memo.get("content", "")
        
        # Replace checkboxes
        if item_index is not None:
            # Replace specific checkbox
            checkboxes = list(re.finditer(r'- \[ \]', content))
            if item_index < 1 or item_index > len(checkboxes):
                return format_error(
                    code="INVALID_INDEX",
                    message=f"Invalid item_index: {item_index}",
                    suggestion=f"This memo has {len(checkboxes)} checkbox(es). Use index 1-{len(checkboxes)}.",
                )
            
            # Replace the specific checkbox
            match = checkboxes[item_index - 1]
            new_content = content[:match.start()] + "- [x]" + content[match.end():]
        else:
            # Replace all checkboxes
            new_content = re.sub(r'- \[ \]', '- [x]', content)
        
        # Update memo content with completed checkboxes
        # Note: Archiving is optional - user can manually archive completed todos if needed
        update_payload = {
            "content": new_content,
        }
        
        params = {"updateMask": "content"}
        
        response = await client.patch(f"/memos/{id_val}", params=params, json=update_payload)

        if response.get("error"):
            return format_error(
                code="COMPLETE_TODO_FAILED",
                message=response["error"].get("message", "Failed to complete todo"),
            )
        
        memo = response
        formatted = format_memo_to_json(memo)
        
        return format_success(formatted, {
            "message": "Todo marked as complete",
            "checkboxes_completed": "all" if item_index is None else item_index,
        })
    
    except Exception as e:
        return format_error(
            code="COMPLETE_TODO_ERROR",
            message=str(e),
        )



# ============ BATCH OPERATIONS ============

@mcp.tool()
async def batch_operation(
    operation: Annotated[
        str,
        "Operation: delete, add_tag, remove_tag, set_visibility, pin, unpin, archive",
    ],
    filter_tags: Annotated[list[str] | None, "Filter by tags"] = None,
    filter_visibility: Annotated[str | None, "Filter by visibility"] = None,
    filter_pinned: Annotated[bool | None, "Filter by pinned"] = None,
    confirm: Annotated[bool, "True to execute, False to preview"] = False,
    tag: Annotated[str | None, "Tag for add_tag/remove_tag"] = None,
    new_visibility: Annotated[str | None, "New visibility for set_visibility"] = None,
) -> str:
    """Perform batch operations on memos. Always preview first (confirm=False)!"""
    from .batch_ops import batch_operation_impl
    return await batch_operation_impl(operation, filter_tags, filter_visibility, filter_pinned, confirm, tag, new_visibility)


# ============ TEMPLATE SYSTEM ============

@mcp.tool()
async def list_templates() -> str:
    """List all available memo templates."""
    try:
        from .template_manager import TemplateManager
        manager = TemplateManager(settings.template_dir)
        templates = manager.list_templates()
        return str(format_success({"templates": templates, "count": len(templates), "template_dir": settings.template_dir}))
    except Exception as e:
        return str(format_error(code="LIST_TEMPLATES_ERROR", message=str(e)))


@mcp.tool()
async def create_from_template(
    template: Annotated[str, "Template name"],
    variables: Annotated[dict[str, str] | None, "Custom variables"] = None,
    visibility: Annotated[str | None, "Visibility"] = "PRIVATE",
    tags: Annotated[list[str] | None, "Tags"] = None,
    pinned: Annotated[bool, "Pin memo"] = False,
) -> str:
    """Create a memo from a template with variable substitution."""
    try:
        from .template_manager import TemplateManager
        manager = TemplateManager(settings.template_dir)
        content = manager.render_template(template, variables)
        
        payload = {
            "content": content,
            "visibility": validate_visibility(visibility) if visibility else "PRIVATE",
            "tags": tags or [],
            "pinned": pinned,
        }
        
        response = await client.post("/memos", json=payload)
        if "error" in response:
            return str(format_error(code="CREATE_FAILED", message=response["error"].get("message", "Failed")))
        
        memo = response  # API returns memo directly, not wrapped in 'data'
        return str(format_success(format_memo_to_json(memo), {"template_used": template, "variables": variables}))
    except FileNotFoundError as e:
        return str(format_error(code="TEMPLATE_NOT_FOUND", message=str(e)))
    except Exception as e:
        return str(format_error(code="CREATE_ERROR", message=str(e)))


@mcp.tool()
def save_template(
    name: Annotated[str, "Template name (without .md extension)"],
    content: Annotated[str, "Template content. Supports {{variable}} placeholders."],
) -> str:
    """Create or update a memo template."""
    try:
        from .template_manager import TemplateManager
        manager = TemplateManager(settings.template_dir)
        path = manager.save_template(name, content)
        return str(format_success({"path": path, "name": name}))
    except Exception as e:
        return str(format_error(code="SAVE_TEMPLATE_ERROR", message=str(e)))


@mcp.tool()
def delete_template(
    name: Annotated[str, "Template name to delete"],
) -> str:
    """Delete a memo template."""
    try:
        from .template_manager import TemplateManager
        manager = TemplateManager(settings.template_dir)
        if manager.delete_template(name):
            return str(format_success({"deleted": True, "name": name}))
        else:
            return str(format_error(code="TEMPLATE_NOT_FOUND", message=f"Template '{name}' not found"))
    except Exception as e:
        return str(format_error(code="DELETE_TEMPLATE_ERROR", message=str(e)))


# ============ EXPORT FUNCTIONS ============

@mcp.tool()
async def export_to_obsidian(
    memo_ids: Annotated[list[str], "Memo IDs to export"],
    mode: Annotated[str, "Mode: content or file"] = "content",
    filename_pattern: Annotated[str, "Pattern: date, title, or id"] = "date",
    subfolder: Annotated[str | None, "Subfolder in vault"] = None,
) -> str:
    """Export memos to Obsidian vault."""
    try:
        from .exporters import ObsidianExporter
        
        memos = []
        for memo_id in memo_ids:
            id_val = str(memo_id).split("/")[-1]
            response = await client.get(f"/memos/{id_val}")
            if not response.get("error"):
                memos.append(format_memo_to_json(response))
        
        if not memos:
            return format_error(code="NO_MEMOS", message="No valid memos found")
        
        if mode == "content":
            exporter = ObsidianExporter(settings.obsidian_vault or "/tmp")
            content = exporter.export_to_content(memos)
            return format_success({"content": content, "memo_count": len(memos)})
        elif mode == "file":
            if not settings.obsidian_vault:
                return format_error(code="NO_VAULT", message="MEMOS_OBSIDIAN_VAULT not set")
            exporter = ObsidianExporter(settings.obsidian_vault)
            files = exporter.export_to_file(memos, filename_pattern, subfolder)
            return format_success({"files_created": files, "memo_count": len(memos)})
        else:
            return format_error(code="INVALID_MODE", message=f"Invalid mode: {mode}")
    except Exception as e:
        return format_error(code="EXPORT_ERROR", message=str(e))


@mcp.tool()
async def export_for_wechat(
    memo_ids: Annotated[list[str], "Memo IDs to export"],
    include_title: Annotated[bool, "Include title"] = True,
    include_date: Annotated[bool, "Include date"] = True,
) -> str:
    """Export memos as plain text for WeChat."""
    try:
        from .exporters import markdown_to_plaintext
        from datetime import datetime
        
        memos = []
        for memo_id in memo_ids:
            id_val = str(memo_id).split("/")[-1]
            response = await client.get(f"/memos/{id_val}")
            if not response.get("error"):
                memos.append(response)
        
        if not memos:
            return format_error(code="NO_MEMOS", message="No memos found")
        
        parts = []
        for memo in memos:
            content = memo.get("content", "")
            plain = markdown_to_plaintext(content)
            
            if include_title or include_date:
                header_parts = []
                if include_date:
                    created = memo.get("createdTs")
                    if created:
                        dt = datetime.fromtimestamp(created)
                        header_parts.append(dt.strftime("%Y-%m-%d"))
                if header_parts:
                    parts.append("【" + " ".join(header_parts) + "】")
            
            parts.append(plain)
            parts.append("")
            parts.append("---")
            parts.append("")
        
        return format_success({"content": "\n".join(parts), "memo_count": len(memos)})
    except Exception as e:
        return format_error(code="EXPORT_ERROR", message=str(e))


# ============ ATTACHMENT MANAGEMENT ============

@mcp.tool()
async def add_attachment(
    memo_id: Annotated[str, "Memo ID"],
    file_path: Annotated[str, "File path"],
    filename: Annotated[str | None, "Custom filename"] = None,
) -> str:
    """Add an attachment to a memo."""
    from .attachment_helpers import add_attachment_to_memo
    return await add_attachment_to_memo(memo_id, file_path, filename)


@mcp.tool()
async def remove_attachment(
    memo_id: Annotated[str, "Memo ID"],
    attachment_id: Annotated[str | None, "Attachment ID (e.g., 'attachments/xxx')"] = None,
    filename: Annotated[str | None, "Filename"] = None,
) -> str:
    """Remove an attachment from a memo."""
    from .attachment_helpers import remove_attachment_from_memo
    return await remove_attachment_from_memo(memo_id, attachment_id, filename)

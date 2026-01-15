---
name: Memos MCP
description: Manage notes in Memos with 27 tools - create, search (natural language dates), tag, todo, template, batch ops, export. Use when user wants to work with Memos notes.
---

# Memos MCP Skill

You have access to a Memos MCP server with 27 tools for comprehensive note management.

## When to Use This Skill

Use this skill when the user wants to:
- Create, read, update, or delete notes in Memos
- Search notes by keyword, tags, or dates (including natural language like "today", "last week")
- Manage todos and checklists
- Work with note templates
- Batch process multiple notes
- Export notes to Obsidian or WeChat format
- Manage attachments and resources

## Available Tools (27)

### Core CRUD (6 tools)
- `create_memo` - Create a new memo with content, tags, visibility
- `create_memo_with_attachments` - Create memo and upload files in one step
- `get_memo` - Get a single memo by ID
- `list_memos` - List memos with pagination and filtering
- `update_memo` - Update memo content, tags, visibility, or pinned status
- `delete_memo` - Permanently delete a memo
- `archive_memo` - Archive a memo (can be restored)

### Search (2 tools)
- `search_memos` - Search by keyword, tags, dates, visibility, pinned status
  - Supports natural language dates: "today", "yesterday", "last week", "this month", "过去7天", "本周"
- `get_memos_by_tag` - Get all memos with a specific tag

### Tags (1 tool)
- `list_tags` - List all tags sorted by usage frequency

### System (2 tools)
- `get_current_user` - Get authenticated user info
- `get_system_status` - Check Memos instance health

### Attachments (5 tools)
- `upload_resource` - Upload a file to Memos
- `set_memo_resources` - Attach resources to a memo
- `list_memo_resources` - List all attachments of a memo
- `add_attachment` - Upload and attach file in one step
- `remove_attachment` - Remove an attachment from a memo

### TODO Management (3 tools)
- `create_todo` - Create todo with checkbox formatting
- `list_todos` - List todos (all or today only)
- `complete_todo` - Mark todo checkboxes as complete

### Batch Operations (1 tool)
- `batch_operation` - Batch process memos (delete, add_tag, remove_tag, set_visibility, pin, unpin, archive)
  - **IMPORTANT**: Always preview first with `confirm=False`

### Templates (4 tools)
- `list_templates` - List available templates
- `create_from_template` - Create memo from template with variable substitution
- `save_template` - Save a new template
- `delete_template` - Delete a template

### Export (2 tools)
- `export_to_obsidian` - Export to Obsidian vault (content or file mode)
- `export_for_wechat` - Export as plain text for WeChat

## Key Features

### Natural Language Date Search
The `search_memos` tool supports natural language date expressions in both English and Chinese:

**English**: today, yesterday, tomorrow, last 7 days, past 30 days, this week, last week, this month, last month, this year, last year

**Chinese**: 今天, 昨天, 前天, 明天, 过去7天, 最近30天, 本周, 上周, 本月, 上个月, 今年, 去年

Example:
```python
search_memos(date_range="last week", tags=["work"])
search_memos(date_range="过去一周", keyword="项目")
```

### Visibility Options
- `PRIVATE` - Only visible to the creator
- `PUBLIC` - Visible to everyone
- `PROTECTED` - Accessible via link

### Batch Operations Safety
Always use `confirm=False` first to preview what will be affected:
```python
# 1. Preview
batch_operation(operation="add_tag", filter_tags=["temp"], tag="processed", confirm=False)

# 2. Execute after review
batch_operation(operation="add_tag", filter_tags=["temp"], tag="processed", confirm=True)
```

## Common Workflows

### Create a Note
```python
create_memo(
    content="Meeting notes #work #meeting",
    visibility="PRIVATE",
    tags=["work", "meeting"],
    pinned=False
)
```

### Search Notes
```python
# Search by keyword and date
search_memos(keyword="project", date_range="this week")

# Search by tags
search_memos(tags=["work", "urgent"], visibility="PRIVATE")

# Get all notes from yesterday
search_memos(date_range="yesterday")
```

### Manage Todos
```python
# Create todo
create_todo(items=["Buy groceries", "Call dentist", "Finish report"])

# List today's todos
list_todos(scope="today")

# Complete a todo
complete_todo(memo_id="123")
```

### Use Templates
```python
# List available templates
list_templates()

# Create from template
create_from_template(
    template="daily_note",
    variables={"date": "2026-01-15", "mood": "productive"},
    tags=["journal"]
)

# Save new template
save_template(
    name="meeting_notes",
    content="# Meeting - {{date}}\n\n**Attendees**: {{attendees}}\n\n## Notes\n{{content}}"
)
```

### Batch Process
```python
# Archive all completed todos
batch_operation(
    operation="archive",
    filter_tags=["todo"],
    confirm=False  # Preview first
)
```

### Export Notes
```python
# Export to Obsidian
export_to_obsidian(
    memo_ids=["123", "456"],
    mode="file",
    filename_pattern="date"
)

# Export for WeChat
export_for_wechat(
    memo_ids=["123", "456"],
    include_title=True,
    include_date=True
)
```

## Important Notes

1. **Memo IDs**: Can be numeric (e.g., "123") or full resource names (e.g., "memos/abc")
2. **Tags in Content**: Tags can be embedded in content as `#tag` or passed as array
3. **Deletion is Permanent**: Use `archive_memo` instead of `delete_memo` when possible
4. **File Paths**: Must be absolute paths for file uploads
5. **Batch Safety**: Always preview batch operations before confirming

## Error Handling

If a tool returns an error:
- Check the error message for specific guidance
- Verify memo IDs exist
- Ensure file paths are correct and files exist
- Check API token has proper permissions
- Verify Memos instance is accessible

## Configuration

The MCP server requires these environment variables:
- `MEMOS_INSTANCE_URL` - Your Memos instance URL
- `MEMOS_API_TOKEN` - Your API authentication token

Optional settings:
- `MEMOS_TODO_TAG` - Tag for todos (default: "todo")
- `OBSIDIAN_VAULT_PATH` - Path to Obsidian vault for exports
- `RESPONSE_FORMAT` - Output format: "json" or "markdown"

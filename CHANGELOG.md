# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-01-16

### 🐛 Bug Fixes

- **Configuration Loading**: Fixed critical issue where configuration failed to load when running via `uvx`
  - Issue: Pydantic-settings defaulted to searching for `.env` only in the current working directory, causing connection failures (localhost:8080) when launched from MCP clients.
  - Fix: Implemented intelligent `.env` discovery and prioritized environment variables.
  - Improvement: Added support for `MEMOS_` prefix to all optional settings for consistency.

---

## [0.2.0] - 2026-01-16

### 🐛 Bug Fixes

#### P0-Critical Issues
- **Batch Operations**: Fixed execution mode that was causing 100% failure rate
  - Root cause: Failed to extract actual ID from full resource name (`memos/xxx`)
  - Impact: All batch operations (delete, archive, tag management) were failing
  - Fix: Added ID extraction logic and updated tag operations to use content format

- **Tag Functionality**: Fixed systematic tag issues affecting multiple tools
  - Root cause: Memos API doesn't support direct `tags` field, only `#tag` format in content
  - Affected tools: `update_memo`, `create_todo`, `batch_operation`
  - Fix: Unified tag handling to use content-based `#tag` format
  - Regex improvement: Changed from `\s+#\S+` to `\s*#\S+` to match tags at any position

#### P1-High Issues
- **remove_attachment**: Fixed parameter type error
  - Issue: `attachment_id` was defined as `int` but actual IDs are strings
  - Fix: Changed type to `str | None` with example documentation

- **list_memo_resources**: Fixed returning empty list
  - Issue: Only checked `resources` field, not `attachments` field
  - Fix: Check both fields to match API response format

### ✨ Improvements

- Improved error handling and boundary case protection
- Unified ID extraction pattern across all tools
- Enhanced tag processing logic with better regex matching
- Added comprehensive validation for edge cases

### 📚 Documentation

- **NEW**: `TEST_REPORT.md` - Detailed test results for all 26 MCP tools (27 test cases)
- **NEW**: `OPTIMIZATION_GUIDE.md` - In-depth technical analysis and fix explanations
- **NEW**: `SUMMARY.md` - Quick overview of test results and fixes
- **NEW**: `RELEASE_GUIDE.md` - Complete guide for publishing to GitHub and PyPI

### 🎉 Highlights

- **Clarification**: `create_memo` tool works perfectly (previously reported issue was a false alarm)
- **Test Coverage**: Comprehensive testing of all 26 tools with 27 test cases
- **Pass Rate**: Improved from 74% to ~85% after fixes
- **Quality**: All P0 and P1 issues resolved

### 🔧 Technical Details

**Modified Files**:
- `memos_mcp/tools.py` - Fixed `update_memo` and `create_todo` tag handling
- `memos_mcp/batch_ops.py` - Fixed ID extraction and tag operations

**Key Changes**:
1. Tag operations now modify content with `#tag` format instead of using API `tags` field
2. ID extraction unified: `str(resource_id).split("/")[-1]`
3. Regex pattern improved for tag matching
4. Resource field checking enhanced to support both `resources` and `attachments`

See [OPTIMIZATION_GUIDE.md](./OPTIMIZATION_GUIDE.md) for detailed technical information.

---

## [0.1.0] - 2026-01-15

### 🎉 Initial Release

#### Features

**Core CRUD Operations**
- `create_memo` - Create memos with tags, visibility, and pinning
- `create_memo_with_attachments` - Create memos with file uploads in one step
- `get_memo` - Retrieve individual memo details
- `list_memos` - List memos with pagination and filtering
- `update_memo` - Update memo content, tags, visibility, etc.
- `delete_memo` - Permanently delete memos
- `archive_memo` - Archive memos without deletion

**Search & Tags**
- `search_memos` - Advanced search with keyword and date filters
  - Natural language date support (e.g., "今天", "上周", "last month")
  - Tag filtering
  - Visibility filtering
- `get_memos_by_tag` - Find all memos with specific tags

**Todo Management**
- `create_todo` - Create todo items with checkbox formatting
- `list_todos` - List all todo items
- `complete_todo` - Mark todos as complete and archive

**Resource/Attachment Management**
- `upload_resource` - Upload files to Memos
- `set_memo_resources` - Attach resources to memos
- `list_memo_resources` - List memo attachments
- `add_attachment` - Quick file upload and attachment
- `remove_attachment` - Remove attachments from memos

**Template System**
- `list_templates` - View available templates
- `save_template` - Create/update templates with variables
- `delete_template` - Remove templates
- `create_from_template` - Create memos from templates with variable substitution

**Batch Operations**
- `batch_operation` - Bulk operations on memos
  - Operations: delete, add_tag, remove_tag, set_visibility, pin, unpin, archive
  - Preview mode for safety (confirm=False)
  - Filtering by tags, visibility, pinned status

**Export Functions**
- `export_to_obsidian` - Export to Obsidian markdown format
  - Content or file mode
  - Customizable filename patterns
- `export_for_wechat` - Export for WeChat Official Accounts
  - Plain text format
  - Optional title and date

**System Tools**
- `get_current_user` - Get authenticated user info
- `get_system_status` - Check Memos instance health

#### Configuration

- Environment-based configuration via `.env`
- Customizable settings:
  - Memos instance URL
  - API token authentication
  - Request timeout
  - Page sizes and limits
  - Todo tag customization
  - Template directory
  - Obsidian vault path

#### Documentation

- Comprehensive README with installation and usage
- Tool reference guide (TOOLS_REFERENCE.md)
- Example configurations
- Integration guide for MCP clients

---

## Links

- [GitHub Repository](https://github.com/Mebigger/memos-mcp-enhanced)
- [PyPI Package](https://pypi.org/project/memos-mcp-enhanced/)
- [Issue Tracker](https://github.com/Mebigger/memos-mcp-enhanced/issues)

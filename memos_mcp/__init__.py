"""Main entry point for Memos MCP server."""
import sys

from mcp.server.fastmcp import FastMCP

from .config import settings
from .tools import mcp


def main() -> None:
    """Run the Memos MCP server."""
    if not settings.is_configured:
        print(
            "Warning: MEMOS_API_TOKEN not configured. "
            "Please set MEMOS_INSTANCE_URL and MEMOS_API_TOKEN in your MCP client's env config.",
            file=sys.stderr,
        )

    # Initialize templates
    try:
        from .template_manager import TemplateManager
        TemplateManager(settings.template_dir).ensure_default_templates()
    except Exception as e:
        print(f"Warning: Failed to initialize templates: {e}", file=sys.stderr)

    mcp.run()


if __name__ == "__main__":
    main()

"""Export utilities for Memos MCP server."""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def markdown_to_plaintext(content: str) -> str:
    """
    Convert Markdown to plain text for WeChat.
    
    Args:
        content: Markdown content
        
    Returns:
        Plain text with basic formatting preserved
    """
    text = content
    
    # Remove code blocks but keep content
    text = re.sub(r"```[\w]*\n(.*?)\n```", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    
    # Convert headers to plain text with emphasis
    text = re.sub(r"^#{1,6}\s+(.+)$", r"【\1】", text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    
    # Convert links to plain text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    
    # Keep list markers
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    
    return text


class ObsidianExporter:
    """Export memos to Obsidian vault."""
    
    def __init__(self, vault_path: str):
        """
        Initialize Obsidian exporter.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path).expanduser()
        
    def export_to_content(self, memos: list[dict[str, Any]]) -> str:
        """
        Export memos to Markdown content.
        
        Args:
            memos: List of memo objects
            
        Returns:
            Formatted Markdown content
        """
        lines = []
        
        for memo in memos:
            content = memo.get("content", "")
            created = memo.get("created_time", "")
            tags = memo.get("tags", [])
            
            # Add metadata
            lines.append(f"## {created}")
            if tags:
                lines.append(f"Tags: {', '.join(f'#{tag}' for tag in tags)}")
            lines.append("")
            
            # Add content
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def export_to_file(
        self,
        memos: list[dict[str, Any]],
        filename_pattern: str = "date",
        subfolder: str | None = None,
    ) -> str:
        """
        Export memos to file in Obsidian vault.
        
        Args:
            memos: List of memo objects
            filename_pattern: Naming pattern (date, title, id)
            subfolder: Optional subfolder in vault
            
        Returns:
            Path to created file
        """
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")
        
        # Determine target directory
        target_dir = self.vault_path
        if subfolder:
            target_dir = target_dir / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Group memos by date if using date pattern
        if filename_pattern == "date":
            # Group by date
            date_groups: dict[str, list[dict[str, Any]]] = {}
            for memo in memos:
                created = memo.get("created_time", "")
                date = created.split("T")[0] if "T" in created else created.split()[0]
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(memo)
            
            # Write each date group
            files_created = []
            for date, group_memos in date_groups.items():
                filename = f"{date}.md"
                filepath = target_dir / filename
                
                # If file exists, append
                if filepath.exists():
                    existing_content = filepath.read_text(encoding="utf-8")
                    new_content = self.export_to_content(group_memos)
                    combined = existing_content + "\n\n" + new_content
                    filepath.write_text(combined, encoding="utf-8")
                else:
                    content = self.export_to_content(group_memos)
                    filepath.write_text(content, encoding="utf-8")
                
                files_created.append(str(filepath))
            
            return ", ".join(files_created)
        
        elif filename_pattern == "id":
            # One file per memo
            files_created = []
            for memo in memos:
                memo_id = memo.get("id", "unknown")
                filename = f"memo_{memo_id}.md"
                filepath = target_dir / filename
                
                content = self.export_to_content([memo])
                filepath.write_text(content, encoding="utf-8")
                files_created.append(str(filepath))
            
            return ", ".join(files_created)
        
        elif filename_pattern == "title":
            # Use first line as title
            files_created = []
            for memo in memos:
                content = memo.get("content", "")
                first_line = content.split("\n")[0][:50]
                # Sanitize filename
                safe_title = re.sub(r'[<>:"/\\|?*]', "", first_line)
                filename = f"{safe_title}.md"
                filepath = target_dir / filename
                
                content = self.export_to_content([memo])
                filepath.write_text(content, encoding="utf-8")
                files_created.append(str(filepath))
            
            return ", ".join(files_created)
        
        else:
            raise ValueError(f"Invalid filename_pattern: {filename_pattern}")

"""Template management for Memos MCP server."""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateManager:
    """Manages memo templates with variable substitution."""
    
    def __init__(self, template_dir: str):
        """
        Initialize template manager.
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = Path(template_dir).expanduser()
        
    def ensure_default_templates(self) -> None:
        """Ensure default templates exist in the template directory."""
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            
        # Check if directory is empty
        if not any(self.template_dir.iterdir()):
            # Copy default templates from package
            import shutil
            import importlib.resources
            
            # Try to find templates in package
            try:
                # Assuming 'templates' directory is at package root
                package_root = Path(__file__).parent.parent
                default_templates_dir = package_root / "templates"
                
                if default_templates_dir.exists():
                    for item in default_templates_dir.glob("*.md"):
                        shutil.copy2(item, self.template_dir)
            except Exception:
                # Fallback: create a basic template if copy fails
                basic_template = """# {{date}} 日记\n\n## 📝 今日记录\n\n- \n\n## ✅ 待办\n- [ ] \n"""
                (self.template_dir / "daily.md").write_text(basic_template, encoding="utf-8")
        
    def list_templates(self) -> list[str]:
        """
        List all available templates.
        
        Returns:
            List of template names (without .md extension)
        """
        if not self.template_dir.exists():
            return []
        
        templates = []
        for file in self.template_dir.glob("*.md"):
            templates.append(file.stem)
        
        return sorted(templates)
    
    def get_template_content(self, name: str) -> str:
        """
        Get template content by name.
        
        Args:
            name: Template name (without extension)
            
        Returns:
            Template content
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self.template_dir / f"{name}.md"
        
        if not template_path.exists():
            available = self.list_templates()
            raise FileNotFoundError(
                f"Template '{name}' not found. "
                f"Available templates: {', '.join(available) if available else 'none'}"
            )
        
        return template_path.read_text(encoding="utf-8")
    
    def render_template(
        self,
        name: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """
        Render template with variable substitution.
        
        Args:
            name: Template name
            variables: Custom variables to substitute
            
        Returns:
            Rendered template content
        """
        content = self.get_template_content(name)
        
        # Build variable map with built-in variables
        now = datetime.now()
        var_map = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "datetime": now.strftime("%Y-%m-%d %H:%M"),
            "weekday": now.strftime("%A"),
            "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
        }
        
        # Add custom variables
        if variables:
            var_map.update(variables)
        
        # Replace variables
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            return str(var_map.get(var_name, match.group(0)))
        
        rendered = re.sub(r"\{\{(\w+)\}\}", replace_var, content)
        
        return rendered

    def save_template(self, name: str, content: str) -> str:
        """
        Save a template.
        
        Args:
            name: Template name (without extension)
            content: Template content
            
        Returns:
            Path to the saved template
        """
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            
        file_path = self.template_dir / f"{name}.md"
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def delete_template(self, name: str) -> bool:
        """
        Delete a template.
        
        Args:
            name: Template name (without extension)
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.template_dir / f"{name}.md"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

# Memos MCP Server Enhanced

[English](#english) | [中文](#chinese)

<a name="english"></a>
## 🇬🇧 English

An enhanced [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for [Memos](https://usememos.com/), enabling LLMs (like Claude, Cursor, etc.) to interact seamlessly with your Memos knowledge base.

> **Privacy Note**: This project runs locally on your machine. Your Memos data is only accessed by the MCP client you authorize.

### ✨ Key Features

*   **Complete CRUD**: Create, read, update, and delete memos.
*   **Smart Search**: Support for natural language date filtering (e.g., "find notes from last week", "search for 'meeting' in 2024").
*   **Task Management**: Dedicated tools for managing TODO lists (`list_todos`, `create_todo`, `complete_todo`).
*   **Resource Management**: Upload files, manage attachments, and attach them to memos.
*   **Batch Operations**: Archive or delete multiple memos in one go.
*   **Template System**: Create memos from reusable templates with variable substitution.
*   **Export Tools**: Export content to Obsidian vaults or format for WeChat Official Accounts.

### 🚀 Quick Start

#### Prerequisites
*   A running [Memos](https://usememos.com/) instance (v0.22+ recommended).
*   An API Token from Memos (Settings -> Access Tokens).
*   [`uv`](https://github.com/astral-sh/uv) installed (recommended) or Python 3.10+.

#### Configuration (Claude Desktop / Cursor)

Add the following to your MCP configuration file:

```json
{
  "memos": {
    "command": "uvx",
    "args": ["memos-mcp-enhanced"],
    "env": {
      "MEMOS_INSTANCE_URL": "https://your-memos-url.com",
      "MEMOS_API_TOKEN": "your-api-token-here"
    }
  }
}
```

### 📦 Installation (Local Development)

1.  Clone the repository:
    ```bash
    git clone https://github.com/Mebigger/memos-mcp-enhanced.git
    cd memos-mcp-enhanced
    ```

2.  Create a `.env` file:
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

3.  Run the server:
    ```bash
    uv run memos-mcp
    ```

### 🛠️ Available Tools

The server exposes 26 tools including:
*   `search_memos`: Search with keywords and date ranges.
*   `create_memo` / `update_memo`: Manage memo content and metadata (including backdating).
*   `upload_resource` / `add_attachment`: Handle files.
*   `batch_operation`: Bulk actions.
*   `export_to_obsidian`: Sync to your local vault.

---

<a name="chinese"></a>
## 🇨🇳 中文

[Memos](https://usememos.com/) 的增强版 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 服务器。它赋予了 LLM（如 Claude, Cursor 等）读写和管理你 Memos 知识库的能力。

> **隐私说明**：此服务在您的本地机器上运行。您的 Memos 数据仅在您授权的 MCP 客户端中处理，不会上传到任何第三方服务器。

### ✨ 核心功能

*   **全功能 CRUD**: 创建、读取、更新、删除笔记。
*   **智能搜索**: 支持自然语言的日期过滤搜索（支持如 "查找上周的笔记"、"搜索去年的记录" 等自然语言）。
*   **待办管理**: 专门的 TODO 管理工具 (`list_todos`, `create_todo`, `complete_todo`)。
*   **附件管理**: 支持文件上传、管理及绑定到笔记。
*   **批量操作**: 支持批量归档、删除笔记。
*   **模板系统**: 内置模板引擎，支持参数替换，快速生成周报、日记等。
*   **导出工具**: 支持将笔记导出到 Obsidian 本地库，或格式化为微信公众号文章。

### � 快速开始

#### 前置要求
*   一个运行中的 [Memos](https://usememos.com/) 实例 (建议 v0.22+)。
*   Memos API Token (在 设置 -> Access Tokens 中获取)。
*   安装 [`uv`](https://github.com/astral-sh/uv) (推荐) 或 Python 3.10+。

#### 配置方式 (Claude Desktop / Cursor)

在您的 MCP 配置文件中添加以下内容：

```json
{
  "memos": {
    "command": "uvx",
    "args": ["memos-mcp-enhanced"],
    "env": {
      "MEMOS_INSTANCE_URL": "https://your-memos-url.com",
      "MEMOS_API_TOKEN": "your-api-token-here"
    }
  }
}
```

### 📦 本地开发安装

1.  克隆仓库：
    ```bash
    git clone https://github.com/Mebigger/memos-mcp-enhanced.git
    cd memos-mcp-enhanced
    ```

2.  配置环境变量：
    ```bash
    cp .env.example .env
    # 编辑 .env 文件填入你的 API 信息
    ```

3.  运行服务：
    ```bash
    uv run memos-mcp
    ```

### 🛠️ 可用工具

本服务提供 26 个增强工具，包括但不限于：
*   `search_memos`: 支持关键词和自然语言日期范围搜索。
*   `create_memo` / `update_memo`: 管理笔记内容、属性（支持修改显示时间）。
*   `upload_resource` / `add_attachment`: 文件上传与附件管理。
*   `batch_operation`: 批量处理。
*   `export_to_obsidian`: 导出到本地 Obsidian 库。

---

## License

MIT

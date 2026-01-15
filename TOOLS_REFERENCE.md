# Memos MCP 工具快速参考

## 📋 所有可用工具 (共 26 个)

### 📝 基础 CRUD 操作

1. **create_memo** - 创建新备忘录
   - 支持内容、可见性、标签、置顶等选项
   
2. **create_memo_with_attachments** - 创建带附件的备忘录
   - 一步完成文件上传和备忘录创建

3. **get_memo** - 获取单个备忘录详情
   - 通过 ID 获取完整的备忘录信息

4. **list_memos** - 列出备忘录
   - 支持分页和过滤

5. **search_memos** - 搜索备忘录
   - 支持关键词搜索和日期范围过滤
   - **支持自然语言日期！** (如 "昨天", "上周", "本月")

6. **update_memo** - 更新备忘录
   - 支持部分更新（只更新提供的字段）

7. **delete_memo** - 删除备忘录
   - 永久删除，无法撤销

### 🏷️ 标签管理

8. **list_tags** - 列出所有标签
   - 按使用频率排序

9. **get_memos_by_tag** - 按标签获取备忘录
   - 查找特定标签的所有备忘录

### 👤 用户和系统信息

10. **get_current_user** - 获取当前用户信息
    - 验证身份认证

11. **get_system_status** - 获取系统状态
    - 检查 Memos 实例健康状态和版本信息

### 📎 资源/附件管理

12. **upload_resource** - 上传文件资源
    - 上传文件到 Memos

13. **set_memo_resources** - 设置备忘录资源
    - 将上传的资源附加到备忘录

14. **list_memo_resources** - 列出备忘录资源
    - 查看备忘录的所有附件

15. **add_attachment** - 添加附件
    - 快捷方式：上传并附加文件

16. **remove_attachment** - 移除附件
    - 从备忘录中移除附件

### ✅ TODO 管理

17. **list_todos** - 列出待办事项
    - 支持按日期范围和置顶状态过滤

18. **create_todo** - 创建待办事项
    - 自动格式化为 Markdown 复选框

19. **complete_todo** - 完成待办事项
    - 标记为完成并归档

### 🔄 批量操作

20. **batch_operation** - 批量操作
    - 支持的操作：
      - `delete` - 批量删除
      - `add_tag` - 批量添加标签
      - `remove_tag` - 批量移除标签
      - `set_visibility` - 批量设置可见性
      - `pin` - 批量置顶
      - `unpin` - 批量取消置顶
      - `archive` - 批量归档
    - **重要**: 始终先预览 (confirm=False)！

### 📄 模板系统

21. **list_templates** - 列出所有模板
    - 查看可用的备忘录模板

22. **create_from_template** - 从模板创建备忘录
    - 支持变量替换

### 📤 导出功能

23. **export_to_obsidian** - 导出到 Obsidian
    - 支持两种模式：
      - `content` - 返回格式化内容
      - `file` - 直接写入文件
    - 文件名模式：`date`, `title`, `id`

24. **export_for_wechat** - 导出为微信格式
    - 纯文本格式，适合微信公众号
    - 可选包含标题和日期

## 🎯 常用场景示例

### 创建备忘录
```
create_memo(
    content="今天学习了 MCP 协议",
    visibility="PRIVATE",
    tags=["学习", "技术"],
    pinned=False
)
```

### 搜索备忘录（自然语言日期）
```
search_memos(
    query="学习",
    created_after="上周",
    created_before="今天"
)
```

### 创建待办事项
```
create_todo(
    content="完成项目文档\n准备会议材料\n回复邮件",
    due_date="明天",
    pinned=True
)
```

### 批量操作（先预览）
```
# 1. 预览
batch_operation(
    operation="add_tag",
    memo_ids=[1, 2, 3],
    tag="重要",
    confirm=False
)

# 2. 确认后执行
batch_operation(
    operation="add_tag",
    memo_ids=[1, 2, 3],
    tag="重要",
    confirm=True
)
```

### 从模板创建
```
create_from_template(
    template="daily_note",
    variables={"mood": "开心", "weather": "晴天"},
    tags=["日记"]
)
```

### 导出到 Obsidian
```
export_to_obsidian(
    memo_ids=[1, 2, 3],
    mode="file",
    filename_pattern="date",
    subfolder="Memos"
)
```

## 🔑 可见性选项

- `PRIVATE` - 私有（仅自己可见）
- `PUBLIC` - 公开（所有人可见）
- `PROTECTED` - 受保护（需要链接）

## 📅 自然语言日期支持

搜索和过滤支持以下自然语言表达：

- **相对日期**: "今天", "昨天", "明天", "上周", "本月"
- **具体日期**: "2024-01-15"
- **时间范围**: "最近7天", "过去30天"

## ⚠️ 重要提示

1. **批量操作**: 始终先用 `confirm=False` 预览结果
2. **删除操作**: 无法撤销，请谨慎使用
3. **API Token**: 保护好你的 API Token，不要分享
4. **文件上传**: 确保文件路径正确且文件存在

## 📚 更多信息

- 详细使用指南: `USER_GUIDE.md`
- 集成指南: `INTEGRATION_GUIDE.md`
- 项目说明: `README.md`

---

**生成时间**: 2026-01-14

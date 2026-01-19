# MCP 工具清单

## 📋 当前可用的 MCP 工具（共8个）

个人记忆系统 MCP Server 提供了以下8个工具，用于管理个人记忆、目标、承诺和洞察。

---

## 🔍 查询类工具（只读）

### 1. `memory_search` - 搜索历史记忆
**功能**: 根据关键词、类别和项目搜索记忆条目，支持全文搜索

**参数**:
- `query` (必需): 搜索关键词
- `category` (可选): 限定类别（goal/plan/commitment/insight/pattern/progress/decision）
- `project` (可选): 限定项目名称
- `limit` (可选): 返回数量，默认5，最大50

**使用场景**:
- "我的目标是什么？" → `memory_search(query="目标", category="goal")`
- "我们上次讨论过XX吗？" → `memory_search(query="XX")`
- "我的进展如何？" → `memory_search(category="progress")`

---

### 2. `memory_get` - 获取记忆详情
**功能**: 根据记忆ID获取完整的记忆条目信息

**参数**:
- `id` (必需): 记忆ID

**使用场景**:
- 获取特定记忆的完整内容
- 查看记忆的详细信息（标题、内容、类别、时间戳等）

---

### 3. `memory_get_project_context` - 加载项目上下文
**功能**: 获取项目相关的记忆和基准文档

**参数**:
- `project` (必需): 项目名称
- `include_baseline` (可选): 是否包含基准文档，默认true
- `recent_limit` (可选): 最近记录数量，默认5

**使用场景**:
- 加载项目相关的所有记忆
- 获取项目的基准文档和最近进展

---

### 4. `memory_list_projects` - 列出项目
**功能**: 列出所有项目，支持按状态过滤

**参数**:
- `status` (可选): 状态过滤（active/paused/completed/archived）

**使用场景**:
- 查看所有项目列表
- 按状态筛选项目

---

### 5. `memory_stats` - 获取统计信息
**功能**: 获取记忆系统的统计信息，包括总数、分类统计等

**参数**:
- `project` (可选): 项目名称（用于项目维度统计）

**使用场景**:
- 查看记忆总数
- 按类别统计记忆数量
- 项目维度的统计信息

---

## ✏️ 写入类工具（可修改）

### 6. `memory_add` - 添加新记忆
**功能**: 创建一个新的记忆条目，保存到数据库和JSON文件

**参数**:
- `category` (必需): 类别（identity/goal/plan/commitment/insight/principle/pattern/progress/decision/conversation）
- `title` (必需): 标题（简短）
- `content` (必需): 内容
- `project` (可选): 所属项目
- `importance` (可选): 重要性1-5，默认3

**使用场景**:
- "记住：我周二有禅修课" → `memory_add(category="commitment", title="周二禅修课", content="...")`
- 保存重要决定、目标、洞察等

---

### 7. `memory_update` - 更新记忆
**功能**: 更新现有记忆的标题、内容或归档状态

**参数**:
- `id` (必需): 记忆ID
- `title` (可选): 新标题
- `content` (可选): 新内容
- `archived` (可选): 是否归档

**使用场景**:
- 修改记忆内容
- 更新记忆标题
- 归档不需要的记忆

---

### 8. `memory_compress_conversation` - 压缩保存对话
**功能**: 将对话内容压缩为摘要，并提取关键决定、洞察和行动项

**参数**:
- `summary` (必需): 对话摘要
- `key_decisions` (可选): 关键决定列表
- `key_insights` (可选): 关键洞察列表
- `action_items` (可选): 行动项列表
- `project` (可选): 所属项目

**使用场景**:
- 对话结束时保存要点
- 提取关键信息并保存

---

## 🔧 关于 MCP Resources vs Tools

### 为什么 `list_mcp_resources` 返回空？

**MCP Resources** 和 **MCP Tools** 是两个不同的概念：

- **MCP Resources**: 用于提供可读取的资源（如文件、数据等），类似于"资源库"
- **MCP Tools**: 用于执行操作（如搜索、添加、更新等），类似于"功能函数"

个人记忆系统主要提供 **Tools**（工具），而不是 **Resources**（资源）。这是正常的设计选择，因为：

1. 所有功能都通过工具调用实现
2. 工具提供了完整的 CRUD 操作
3. 不需要额外的资源接口

### 如何验证工具是否可用？

#### 方法1: 在对话中测试
尝试询问：
- "我的目标是什么？"
- "记住：测试记忆"

如果AI能够调用工具并返回结果，说明工具正常工作。

#### 方法2: 检查 Cursor 开发者工具
1. 打开 Cursor
2. Help > Toggle Developer Tools
3. 查看 Console 标签
4. 查找 MCP 相关的日志

#### 方法3: 直接运行 MCP Server
```bash
cd memory-mcp-server
source venv/bin/activate
python main.py
```

如果服务器启动没有错误，说明配置正确。

---

## 📊 工具分类统计

| 类别 | 数量 | 工具名称 |
|------|------|----------|
| 查询类（只读） | 5 | memory_search, memory_get, memory_get_project_context, memory_list_projects, memory_stats |
| 写入类（可修改） | 3 | memory_add, memory_update, memory_compress_conversation |
| **总计** | **8** | - |

---

## 🎯 使用建议

1. **查询操作**: 使用 `memory_search` 进行大部分查询，支持全文搜索
2. **添加记忆**: 使用 `memory_add` 保存新记忆，注意选择合适的类别
3. **项目相关**: 使用 `memory_get_project_context` 加载项目上下文
4. **对话保存**: 使用 `memory_compress_conversation` 保存对话要点

---

## 📝 注意事项

- 所有工具都需要数据库已初始化
- 工具会自动初始化数据库（如果未初始化）
- 写入操作会同时更新数据库和JSON文件
- 搜索支持全文搜索（FTS5）

---

**最后更新**: 2026-01-11

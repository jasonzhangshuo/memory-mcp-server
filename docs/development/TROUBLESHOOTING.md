# MCP Server 故障排查指南

## 问题：显示 "No MCP resources available" 但工具调用成功

### 现象
- Cursor 界面显示 "No MCP resources available"
- 但 AI 最终成功调用了工具并保存了记录
- 说明 MCP Server 实际上在工作，但资源检查失败

### 可能原因

1. **Cursor 的 MCP 资源检查机制**
   - Cursor 可能在检查 MCP "resources"（不是 tools）
   - FastMCP 默认不提供 resources，只提供 tools
   - 这是正常的，不影响工具调用

2. **MCP Server 连接状态**
   - MCP Server 可能已连接，但资源检查失败
   - 工具调用仍然可以正常工作

3. **FastMCP 的实现**
   - FastMCP 主要提供 tools，不提供 resources
   - 这是设计上的差异，不影响功能

### 验证方法

#### 方法 1: 检查工具是否可用

在 Cursor 中尝试：
```
我的目标是什么？
```

如果 AI 能返回"核心目标：50岁退休"，说明工具调用正常。

#### 方法 2: 查看 Cursor 开发者工具

1. 打开 Cursor
2. Help > Toggle Developer Tools
3. 查看 Console 标签
4. 查找 MCP 相关的日志

#### 方法 3: 测试 MCP Server 直接运行

```bash
cd memory-mcp-server
source venv/bin/activate
python main.py
```

如果服务器启动没有错误，说明配置正确。

### 解决方案

#### 方案 1: 忽略资源检查（推荐）

如果工具调用正常工作，可以忽略 "No MCP resources available" 的提示。这是 Cursor 的资源检查机制，不影响工具功能。

#### 方案 2: 添加 MCP Resources（如果需要）

如果确实需要 resources，可以在 `main.py` 中添加：

```python
@mcp.resource("memory://{id}")
async def get_memory_resource(id: str) -> str:
    """Get memory as resource."""
    # 实现资源获取逻辑
    pass
```

但这不是必需的，因为工具已经提供了所有功能。

### 验证工具调用是否正常

#### 测试 1: 查询记忆
```
我的目标是什么？
```
**期望**: AI 调用 `memory_search` 并返回结果

#### 测试 2: 保存记忆
```
记住：我明天有重要会议
```
**期望**: AI 调用 `memory_add` 并确认保存

#### 测试 3: 项目上下文
```
加载 2026-baseline 项目的上下文
```
**期望**: AI 调用 `memory_get_project_context` 并返回项目信息

### 常见问题

#### Q: 为什么显示 "No MCP resources available"？
A: 这是 Cursor 的资源检查机制。FastMCP 主要提供 tools，不提供 resources。这不影响工具调用功能。

#### Q: 工具调用正常，但显示资源不可用，有问题吗？
A: 没有问题。只要工具调用正常工作，就可以忽略资源检查的提示。

#### Q: 如何确认 MCP Server 正常工作？
A: 测试工具调用功能。如果 AI 能正确调用工具并返回结果，说明一切正常。

### 总结

- ✅ **工具调用正常** = MCP Server 工作正常
- ⚠️ **"No MCP resources available"** = 只是资源检查提示，不影响功能
- ✅ **可以忽略资源检查提示**，专注于工具调用功能

如果工具调用都正常，说明系统工作正常，可以忽略资源检查的提示。

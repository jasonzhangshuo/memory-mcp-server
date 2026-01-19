# 快速测试指南

重启 Cursor 后，使用以下测试用例验证 MCP Server 是否正常工作。

## 🧪 测试用例（按优先级）

### 测试 1: 查询目标（最简单，应该能成功）

**在 Cursor 中输入**：
```
我的目标是什么？
```

**期望结果**：
- ✅ AI 识别到"我的目标"触发词
- ✅ AI 调用 `memory_search` 工具
- ✅ AI 返回："根据您的记忆，您的核心目标是：50岁退休。为50岁退休做好身体与精神的双重准备。不是'再赢一次'，而是'不再走错'。"

**如果成功**：说明 MCP Server 配置成功，Skill 触发正常！

**如果失败**：
- 检查 Cursor 开发者工具（Help > Toggle Developer Tools）中的错误
- 确认 AI 是否尝试调用了工具

---

### 测试 2: 保存记忆

**在 Cursor 中输入**：
```
记住：我周二有禅修课
```

**期望结果**：
- ✅ AI 识别到"记住"触发词
- ✅ AI 调用 `memory_add` 工具
- ✅ AI 确认："已记录：周二禅修课"

**如果成功**：说明写入功能正常！

---

### 测试 3: 历史查询（可能为空）

**在 Cursor 中输入**：
```
我们上次聊的戒糖，后来怎样了？
```

**期望结果**：
- ✅ AI 调用 `memory_search` 工具，query="戒糖"
- ✅ 返回空结果（因为种子数据中没有"戒糖"）
- ✅ AI 诚实告知："没有找到关于'戒糖'的相关记录"

**如果成功**：说明空结果处理正常！

---

### 测试 4: 空结果处理

**在 Cursor 中输入**：
```
我们讨论过量子计算吗？
```

**期望结果**：
- ✅ AI 调用 `memory_search` 工具
- ✅ 返回空结果
- ✅ AI 不编造内容，诚实告知未找到

---

## 🔍 如何判断是否调用了工具？

### 方法 1: 观察 AI 的回答

如果 AI 的回答：
- 包含具体的目标内容（"50岁退休"）
- 说明"根据您的记忆"
- 确认"已记录"

说明工具被调用了。

### 方法 2: 查看开发者工具

1. 打开 Cursor
2. Help > Toggle Developer Tools
3. 查看 Console 标签
4. 查找 MCP 相关的日志

### 方法 3: 检查数据库

```bash
cd memory-mcp-server
source venv/bin/activate
python -c "
import asyncio
from storage.db import search_memories
async def check():
    results = await search_memories('目标', limit=1)
    print(f'找到 {len(results)} 条记忆')
    if results:
        print(f'标题: {results[0][\"title\"]}')
asyncio.run(check())
"
```

## ⚠️ 常见问题

### 问题 1: AI 没有调用工具

**可能原因**：
- Skill description 触发失败
- MCP Server 未正确连接
- 需要优化触发词

**解决方案**：
- 检查 Cursor 开发者工具中的错误
- 尝试更明确的触发词（"记住：XXX"）

### 问题 2: 工具调用失败

**可能原因**：
- Python 路径错误
- 依赖未安装
- 数据库未初始化

**解决方案**：
```bash
cd memory-mcp-server
./quick_start.sh  # 重新验证环境
```

### 问题 3: 返回错误结果

**可能原因**：
- 数据库问题
- 搜索功能问题

**解决方案**：
```bash
cd memory-mcp-server
source venv/bin/activate
python test_mcp_tools.py  # 测试工具功能
```

## 📊 测试结果记录

| 测试 | 输入 | 是否调用工具 | 结果 | 备注 |
|------|------|------------|------|------|
| T1 | "我的目标是什么？" | ⬜ | ⬜ | |
| T2 | "记住：我周二有禅修课" | ⬜ | ⬜ | |
| T3 | "我们上次聊的戒糖，后来怎样了？" | ⬜ | ⬜ | |
| T4 | "我们讨论过量子计算吗？" | ⬜ | ⬜ | |

## 🎯 成功标准

- **最低要求**：测试 1（查询目标）必须成功
- **理想状态**：所有测试都能成功调用工具

## 💡 提示

- 如果测试 1 成功，说明配置完全正确！
- 如果测试 1 失败，检查开发者工具中的错误信息
- 可以尝试更明确的触发词，如"记住：XXX"

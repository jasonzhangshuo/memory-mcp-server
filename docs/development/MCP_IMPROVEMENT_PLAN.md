# MCP 服务器改进计划

基于 mcp-builder skill 的最佳实践，对 personal_memory MCP 服务器进行迭代改进。

## 当前问题分析

### 1. 错误处理不够完善
- ❌ 使用通用的 `Exception` 而不是具体的异常类型
- ❌ 错误消息不够具体和可操作
- ❌ 缺少针对不同错误类型的处理建议

### 2. 代码结构需要优化
- ❌ 错误处理逻辑分散在各个工具中
- ❌ 缺少统一的错误处理函数
- ❌ API 客户端错误处理可以更清晰

### 3. 文档和类型提示
- ✅ 已有 Pydantic 模型
- ✅ 已有工具描述
- ⚠️ 可以改进错误处理的文档说明

## 改进计划

### Phase 1: 改进错误处理（优先级：高）

#### 1.1 创建统一的错误处理函数
- 在 `sync/feishu_client.py` 中添加 `_handle_api_error()` 函数
- 支持不同类型的 HTTP 错误（404, 403, 401, 429 等）
- 提供具体的错误消息和解决建议

#### 1.2 改进 FeishuClient 的错误处理
- 使用 `httpx.HTTPStatusError` 而不是通用 Exception
- 提供更清晰的错误消息
- 区分不同类型的错误（权限、网络、API 等）

#### 1.3 改进工具层的错误处理
- 所有工具使用统一的错误处理模式
- 返回结构化的错误响应
- 包含可操作的建议

### Phase 2: 代码重构（优先级：中）

#### 2.1 提取公共功能
- 提取错误格式化逻辑
- 提取响应格式化逻辑
- 统一 JSON 响应格式

#### 2.2 改进类型提示
- 确保所有函数都有完整的类型提示
- 使用 TypedDict 或 Pydantic 模型定义返回类型

### Phase 3: 文档改进（优先级：低）

#### 3.1 改进工具文档
- 添加更详细的错误处理说明
- 添加使用示例
- 添加常见问题解答

## 实施步骤

1. ✅ 创建改进计划文档
2. ✅ 实施 Phase 1: 改进错误处理
   - ✅ 创建 `FeishuAPIError` 自定义异常类
   - ✅ 创建统一的 `_handle_api_error()` 错误处理函数
   - ✅ 改进 `FeishuClient._request()` 方法的错误处理
   - ✅ 更新所有飞书工具使用新的错误处理
3. ⏳ 实施 Phase 2: 代码重构
4. ⏳ 实施 Phase 3: 文档改进
5. ⏳ 测试所有改进
6. ⏳ 更新相关文档

## Phase 1 完成总结

### 已完成的改进

1. **创建自定义异常类 `FeishuAPIError`**
   - 包含 status_code, error_code, error_data, suggestion 字段
   - 提供结构化的错误信息

2. **统一的错误处理函数 `_handle_api_error()`**
   - 处理 `httpx.HTTPStatusError`（HTTP 状态码错误）
   - 处理 `httpx.TimeoutException`（超时错误）
   - 处理 `httpx.ConnectError`（连接错误）
   - 根据不同的状态码提供具体的解决建议

3. **改进 `FeishuClient._request()` 方法**
   - 使用 `response.raise_for_status()` 自动处理 HTTP 错误
   - 使用 `httpx` 的异常类型而不是通用 Exception
   - 提供更详细的错误信息和解决建议
   - 处理飞书 API 的业务状态码（code 字段）

4. **更新所有飞书工具**
   - `feishu_create_document.py` - 使用新的错误处理
   - `feishu_update_document.py` - 使用新的错误处理
   - `feishu_get_document.py` - 使用新的错误处理
   - 所有工具现在返回结构化的错误响应，包含 error_code, status_code, suggestion

### 改进效果

- ✅ 错误消息更具体和可操作
- ✅ 根据不同的错误类型提供针对性的解决建议
- ✅ 错误响应结构统一，便于客户端处理
- ✅ 符合 mcp-builder 最佳实践（使用具体异常类型，提供可操作的错误消息）

## 参考标准

- [MCP Best Practices](./.claude/skills/mcp-builder/reference/mcp_best_practices.md)
- [Python MCP Server Guide](./.claude/skills/mcp-builder/reference/python_mcp_server.md)

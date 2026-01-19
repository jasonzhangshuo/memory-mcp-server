# 飞书文档权限申请指南

## 当前状态

- ✅ **多维表格权限**：已开通（`bitable:app`）
- ❌ **文档权限**：未申请（需要申请才能写入文档）

## 飞书文档 API 权限

要往飞书里写文档，需要申请以下权限：

### 必需权限

| 权限标识 | 权限名称 | 说明 |
|---------|---------|------|
| `drive:drive` | 云空间完整权限 | 创建、读取、更新、删除文档（推荐） |
| `drive:drive:readonly` | 云空间只读权限 | 仅读取文档（如果只需要读取） |

### 文档操作权限细分

| 操作 | 所需权限 | API 端点 |
|------|---------|---------|
| 创建文档 | `drive:drive` | `POST /drive/v1/files` |
| 读取文档 | `drive:drive:readonly` 或 `drive:drive` | `GET /drive/v1/files/{file_token}` |
| 更新文档内容 | `drive:drive` | `PUT /drive/v1/files/{file_token}/content` |
| 删除文档 | `drive:drive` | `DELETE /drive/v1/files/{file_token}` |

## 申请步骤

### 方法 1: 直接点击链接申请（推荐）

访问以下链接，会自动跳转到权限申请页面：

```
https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=drive:drive&op_from=openapi&token_type=tenant
```

### 方法 2: 手动申请

1. **登录飞书开放平台**
   - 访问：https://open.feishu.cn/
   - 登录你的账号

2. **进入应用管理**
   - 找到你的应用：`cli_a9e9a4047fb8dbc4`
   - 点击进入应用详情

3. **申请权限**
   - 点击左侧菜单"权限管理"
   - **重要**：切换到"应用身份"标签页（不是"用户身份"）
   - 在搜索框输入：`drive:drive`
   - 找到"云空间完整权限"或"云空间只读权限"
   - 点击"申请权限"
   - 填写申请理由（例如：用于自动创建和更新个人知识管理文档）

4. **等待审核**
   - 通常几分钟内会通过
   - 审核通过后，权限状态会显示为"已开通"

## 权限说明

### 应用身份 vs 用户身份

- **应用身份权限**：用于 API 调用，应用可以代表自己操作
- **用户身份权限**：用于用户在飞书客户端中操作

**重要**：要使用 API 写入文档，必须申请**应用身份**权限。

### 权限范围

- `drive:drive`：可以访问应用有权限的所有云空间文件
- 需要确保应用被添加到目标文件夹的协作者中（如果需要访问特定文件夹）

## 申请后验证

### 1. 检查权限状态

在飞书开放平台：
- 进入应用 → 权限管理 → 应用身份
- 确认 `drive:drive` 显示为"已开通"（不是"已申请"）

### 2. 测试 API 连接

创建测试脚本验证权限：

```python
# test_drive_permission.py
import asyncio
from sync.feishu_client import FeishuClient

async def test_drive():
    client = FeishuClient()
    token = await client.get_access_token()
    
    # 测试创建文档
    url = "https://open.feishu.cn/open-apis/drive/v1/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # ... 测试代码

asyncio.run(test_drive())
```

## 实现文档写入功能

申请权限后，可以：

1. **扩展 FeishuClient**
   - 添加文档创建方法：`create_document()`
   - 添加文档更新方法：`update_document()`
   - 添加文档读取方法：`get_document()`

2. **创建文档工具**
   - 在 `tools/` 目录创建 `feishu_create_document.py`
   - 实现 MCP 工具，供 AI 调用

3. **使用场景**
   - 自动创建记忆摘要文档
   - 定期生成报告文档
   - 将对话内容保存为文档

## 注意事项

1. **权限生效时间**：申请后通常几分钟内生效，最长可能需要 10-15 分钟
2. **应用发布**：确保应用已发布（版本管理 → 发布）
3. **文件夹权限**：如果要写入特定文件夹，需要将应用添加为该文件夹的协作者
4. **API 限制**：注意飞书 API 的调用频率限制

## 相关文档

- [飞书开放平台 - 云空间 API](https://open.feishu.cn/document/server-docs/docs/drive-v1/overview)
- [飞书开放平台 - 权限说明](https://open.feishu.cn/document/ukTMukTMukTM/uYjL14iM2EjL24iM)

## 下一步

1. ✅ 申请 `drive:drive` 权限
2. ⏳ 等待审核通过
3. ⏳ 扩展 FeishuClient 支持文档操作
4. ⏳ 实现文档创建/更新工具
5. ⏳ 测试文档写入功能

# 飞书权限申请指南

## 问题

API 调用失败，错误信息显示需要"应用身份"权限。

## 解决方案

### 方法 1: 直接点击链接申请（推荐）

**多维表格权限**（已申请）：
```
https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=bitable:app:readonly,bitable:app,base:table:read&op_from=openapi&token_type=tenant
```

**文档权限**（如需写入文档，需要申请）：
```
https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=drive:drive&op_from=openapi&token_type=tenant
```

**同时申请多维表格和文档权限**：
```
https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=bitable:app,drive:drive&op_from=openapi&token_type=tenant
```

### 方法 2: 手动申请

1. 登录飞书开放平台：https://open.feishu.cn/
2. 进入你的应用：`cli_a9e9a4047fb8dbc4`
3. 点击左侧菜单"权限管理"
4. 切换到"应用身份"标签页（注意：不是"用户身份"）
5. 搜索以下权限之一并申请：
   - `bitable:app:readonly` - 多维表格只读权限（推荐）
   - `bitable:app` - 多维表格完整权限
   - `base:table:read` - 基础表格读取权限

### 重要提示

- ✅ **用户身份权限**：已开通（用于用户在飞书客户端中操作）
- ❌ **应用身份权限**：需要申请（用于 API 调用）

这两个权限是独立的，都需要申请才能正常使用。

## 申请后

1. 等待审核通过（通常几分钟内）
2. 重新运行测试脚本：`python test_feishu_connection.py`
3. 如果还有问题，检查应用是否需要"发布"

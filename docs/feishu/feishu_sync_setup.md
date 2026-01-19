# 飞书多维表格同步 - 配置指南

## ✅ 已完成的步骤

1. ✅ 创建飞书开放平台应用
2. ✅ 获取 App ID: `cli_a9e9a4047fb8dbc4`
3. ✅ 获取 App Secret: `AjRbHKjmortj1Vw4oq2idf5pzCqZXSNg`
4. ✅ 申请多维表格 API 权限（已开通）

## 📋 下一步：获取多维表格信息

### 步骤 1: 打开你的多维表格

1. 访问：https://my.feishu.cn/base?src_domain_uid=6805872094585307137
2. 或者从飞书应用中找到你创建的多维表格

### 步骤 2: 获取 App Token

1. 在多维表格页面，查看浏览器地址栏
2. URL 格式类似：`https://my.feishu.cn/base/xxxxxxxxxxxxx`
3. `xxxxxxxxxxxxx` 就是 `app_token`（也叫 base_id）
4. 复制这个值

### 步骤 3: 获取 Table ID

有两种方法：

**方法 A: 从 URL 获取**
- 如果 URL 中有 `table_id` 参数，直接复制

**方法 B: 通过 API 获取**
- 创建同步脚本后，会自动获取

### 步骤 4: 更新 .env 文件

将获取到的值填入 `.env` 文件：

```bash
FEISHU_APP_TOKEN=你的app_token
FEISHU_TABLE_ID=你的table_id（如果有）
```

## 🔧 配置说明

### 环境变量说明

- `FEISHU_APP_ID`: 飞书应用ID（已配置）
- `FEISHU_APP_SECRET`: 飞书应用密钥（已配置）
- `FEISHU_APP_TOKEN`: 多维表格的 app_token（待填写）
- `FEISHU_TABLE_ID`: 数据表的 table_id（可选，可通过 API 获取）
- `SYNC_INTERVAL`: 同步间隔（秒），默认3600（1小时）
- `SYNC_BATCH_SIZE`: 批量同步数量，默认50

## 📝 注意事项

1. **安全提示**：
   - `.env` 文件包含敏感信息，不要提交到 Git
   - 已添加到 `.gitignore`

2. **权限确认**：
   - 已确认多维表格权限已开通
   - 包括：创建、读取、更新、复制

3. **数据量限制**：
   - 免费版单表最多 2000 行
   - 当前记忆：79 条，在限制内

## 🚀 下一步

获取到 `app_token` 后，告诉我，我会：
1. 更新 `.env` 文件
2. 创建同步脚本
3. 测试 API 连接
4. 实现数据同步功能

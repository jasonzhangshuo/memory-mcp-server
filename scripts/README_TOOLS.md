# 工具脚本说明

## 📁 目录结构

```
scripts/
├── README.md          # 主要维护脚本说明
├── README_TOOLS.md    # 本文档：工具脚本说明
├── cleanup.py         # 清理工具（主要）
├── run_tests.sh       # 测试运行脚本（主要）
├── setup_cron.sh      # 定期任务设置
├── setup_auto_sync.sh # 自动同步设置
├── setup_mcp_config.sh# MCP 配置设置
├── quick_start.sh     # 快速启动
├── check_mcp_status.sh# MCP 状态检查
├── diagnose_mcp.sh    # MCP 诊断
│
├── tools/             # 工具脚本集合
│   ├── check_*.py     # 检查工具
│   ├── clean_*.py     # 清理工具
│   ├── diagnose_*.py  # 诊断工具
│   ├── delete_*.py    # 删除工具
│   ├── list_*.py      # 列表工具
│   ├── read_*.py      # 读取工具
│   ├── get_*.py       # 获取工具
│   └── view_*.py      # 查看工具
│
├── oauth/             # OAuth 相关工具
│   ├── oauth_auto.py  # 自动 OAuth
│   └── oauth_helper.py# OAuth 辅助工具
│
└── archived/          # 归档的过时脚本
    ├── verify_setup.py
    └── debug_fts.py
```

## 🛠️ 主要工具

### 维护工具（根目录）

| 脚本 | 用途 | 使用频率 |
|------|------|----------|
| `cleanup.py` | 清理无用数据 | 每月 |
| `run_tests.sh` | 运行测试 | 开发时 |
| `setup_cron.sh` | 设置定期任务 | 一次性 |

### 检查工具（tools/check_*.py）

- `check_all_permissions.py` - 检查所有权限
- `check_feishu_fields.py` - 检查飞书字段
- `check_feishu_records.py` - 检查飞书记录
- `check_feishu_sync_status.py` - 检查飞书同步状态

**使用示例：**
```bash
python scripts/tools/check_all_permissions.py
```

### 清理工具（tools/clean_*.py）

- `clean_daily_schedule.py` - 清理每日计划
- `clean_empty_records.py` - 清理空记录
- `clean_redundant_memories.py` - 清理冗余记忆

**使用示例：**
```bash
python scripts/tools/clean_empty_records.py
```

### 诊断工具（tools/diagnose_*.py）

- `diagnose_feishu_docs.py` - 诊断飞书文档
- `diagnose_mcp.py` - 诊断 MCP 连接

**使用示例：**
```bash
python scripts/tools/diagnose_mcp.py
```

### 删除工具（tools/delete_*.py）

- `delete_local_test_memories.py` - 删除本地测试记忆
- `delete_test_memories.py` - 删除测试记忆

**⚠️ 警告：** 使用前请确认，删除操作不可恢复

### 查看工具（tools/）

- `list_all_tables.py` - 列出所有表格
- `list_tools.py` - 列出所有工具
- `read_my_notes.py` - 读取我的笔记
- `read_xiaohongshu_table.py` - 读取小红书表格
- `get_top_notes.py` - 获取热门笔记
- `view_memories.py` - 查看记忆

**使用示例：**
```bash
python scripts/tools/view_memories.py
```

## 🔐 OAuth 工具

### oauth/oauth_auto.py
自动化 OAuth 认证流程

**使用示例：**
```bash
python scripts/oauth/oauth_auto.py
```

### oauth/oauth_helper.py
OAuth 辅助工具和函数

## 📦 归档脚本

`scripts/archived/` 中的脚本已过时或不再使用，保留仅供参考。

## 💡 使用建议

### 日常使用
主要使用根目录的维护脚本：
- `cleanup.py` - 定期清理
- `run_tests.sh` - 运行测试

### 问题排查
使用 tools/ 下的诊断和检查工具：
```bash
# 1. 检查 MCP 状态
python scripts/tools/diagnose_mcp.py

# 2. 检查飞书同步
python scripts/tools/check_feishu_sync_status.py

# 3. 查看记忆
python scripts/tools/view_memories.py
```

### 开发调试
使用 tools/ 下的各类工具：
```bash
# 列出所有工具
python scripts/tools/list_tools.py

# 列出所有表格
python scripts/tools/list_all_tables.py
```

## ⚠️ 注意事项

1. **删除工具**: 使用前请备份数据
2. **清理工具**: 建议先试运行（如果支持）
3. **OAuth 工具**: 需要配置相应的环境变量
4. **归档脚本**: 不建议使用，可能已过时

## 🔍 查找工具

### 按功能查找
- 检查相关: `scripts/tools/check_*.py`
- 清理相关: `scripts/tools/clean_*.py`
- 诊断相关: `scripts/tools/diagnose_*.py`
- 查看相关: `scripts/tools/{list,read,get,view}_*.py`

### 按问题查找
| 问题 | 使用工具 |
|------|---------|
| MCP 连接问题 | `diagnose_mcp.py` |
| 飞书同步问题 | `check_feishu_sync_status.py` |
| 查看记忆 | `view_memories.py` |
| 权限问题 | `check_all_permissions.py` |

---

**提示**: 大部分日常任务使用根目录的维护脚本即可，tools/ 下的工具主要用于特殊情况和问题排查。

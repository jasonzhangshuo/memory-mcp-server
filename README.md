# 个人记忆系统 (Personal Memory System)

基于 MCP (Model Context Protocol) 的个人记忆管理系统，支持记忆存储、搜索、分类和飞书同步。

## ✨ 核心功能

- 📝 **记忆管理**：添加、搜索、更新、获取记忆
- 🏷️ **智能分类**：自动分类建议，支持多种类别（insight, goal, decision, knowledge等）
- 🔍 **全文搜索**：FTS5 全文检索，支持中英文
- 🏷️ **标签系统**：灵活的标签管理和筛选
- 📊 **项目管理**：按项目组织记忆，支持项目上下文
- 🔄 **飞书同步**：自动同步到飞书多维表格

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 MCP

在 Claude Desktop 的配置文件中添加：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "personal-memory": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/memory-mcp-server/main.py"]
    }
  }
}
```

### 3. 启动使用

重启 Claude Desktop 后，即可在对话中使用记忆功能：

- "记住：今天学习了 Python 异步编程"
- "我之前说过什么关于项目计划的？"
- "列出所有关于工作的记忆"

## 📖 文档

### 核心文档
- **[MAINTENANCE.md](MAINTENANCE.md)** - 系统维护指南
- **[CHANGELOG.md](CHANGELOG.md)** - 更新日志
- **[优化总结.md](优化总结.md)** - 最新优化说明

### 详细文档
- **[docs/](docs/)** - 完整文档目录
  - `docs/development/` - 开发配置文档
  - `docs/feishu/` - 飞书集成文档
  - `docs/guides/` - 使用指南
  - `docs/archive/` - 历史文档

### 维护工具
- **[scripts/README.md](scripts/README.md)** - 维护脚本使用说明

## 🛠️ 维护工具

### 清理工具
```bash
# 清理无用数据（试运行）
python scripts/cleanup.py --dry-run

# 执行清理
python scripts/cleanup.py
```

### 测试工具
```bash
# 运行所有测试（使用独立测试数据库）
./scripts/run_tests.sh

# 运行特定测试
./scripts/run_tests.sh regression   # 回归测试
./scripts/run_tests.sh stability    # 稳定性测试
./scripts/run_tests.sh performance  # 性能测试
```

## 📊 系统状态

- ✅ 核心功能完善
- ✅ 测试隔离机制
- ✅ 自动化清理工具
- ✅ 飞书同步支持
- ✅ 完整文档体系

## 🏗️ 项目结构

```
memory-mcp-server/
├── README.md              # 本文档
├── CHANGELOG.md           # 更新日志
├── MAINTENANCE.md         # 维护指南
├── config.py              # 环境配置
├── main.py                # MCP Server 入口
├── models.py              # 数据模型
├── requirements.txt       # 依赖列表
│
├── tools/                 # MCP 工具实现
│   ├── memory_add.py
│   ├── memory_search.py
│   ├── memory_update.py
│   ├── memory_get.py
│   └── ...
│
├── storage/               # 存储层
│   ├── db.py             # 数据库操作
│   └── projects.py       # 项目管理
│
├── sync/                  # 飞书同步
│   ├── feishu_client.py
│   └── sync_to_feishu.py
│
├── scripts/               # 维护脚本
│   ├── cleanup.py        # 清理工具
│   ├── run_tests.sh      # 测试脚本
│   └── README.md         # 脚本文档
│
├── docs/                  # 文档目录
│   ├── development/      # 开发文档
│   ├── feishu/          # 飞书文档
│   ├── guides/          # 使用指南
│   └── archive/         # 历史文档
│
├── tests/                 # 测试套件
│   ├── test_regression.py
│   ├── stability_score.py
│   └── test_performance.py
│
├── memory.db             # 生产数据库
└── entries/              # 记忆条目（JSON）
```

## 🔒 数据安全

- 本地存储，数据完全由你掌控
- 支持定期备份（参考 MAINTENANCE.md）
- 测试数据完全隔离，不会污染生产数据

## 🆘 获取帮助

- 维护问题：查看 [MAINTENANCE.md](MAINTENANCE.md)
- 飞书同步：查看 [docs/feishu/](docs/feishu/)
- 开发配置：查看 [docs/development/](docs/development/)
- 历史记录：查看 [CHANGELOG.md](CHANGELOG.md)

## 📝 版本

当前版本：v1.2

- v1.0 (2026-01-11): 基础功能
- v1.1 (2026-01-17): 智能分类与冲突检测
- v1.2 (2026-01-17): 清理工具与测试隔离

---

**最后更新**: 2026-01-17

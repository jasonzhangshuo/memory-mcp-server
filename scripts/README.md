# 维护脚本说明

本目录包含用于维护个人记忆系统的工具脚本。

## 📁 脚本列表

### 1. cleanup.py - 清理工具

**功能：**
- 清理无用的 JSON 文件（数据库中未引用的）
- 清理 FTS5 索引中的过期数据
- 清理空目录

**使用方法：**

```bash
# 试运行模式（推荐先运行，查看将要清理的内容）
python scripts/cleanup.py --dry-run

# 实际清理
python scripts/cleanup.py
```

**运行时机：**
- 删除大量记忆后
- 定期维护（建议每月一次）
- 发现搜索变慢时

**输出示例：**
```
============================================================
🧹 个人记忆系统清理工具
============================================================

⚠️  运行模式: 试运行（不会实际删除任何内容）

============================================================
1️⃣  清理无用的 JSON 文件
============================================================
💾 数据库中有效记忆: 15 条

📁 扫描结果:
   总文件数: 20
   保留: 15 个
   无用: 5 个 (2.5 KB)

⚠️  试运行模式，不实际删除

无用文件列表:
  - entries/2026/01/xxx.json (500 bytes)
  ...

============================================================
📊 清理汇总
============================================================

将要清理:
  - JSON 文件: 5 个 (2.5 KB)
  - FTS5 记录: 5 条
  - 空目录: 0 个

提示: 运行 'python scripts/cleanup.py' 执行实际清理
```

---

### 2. run_tests.sh - 测试运行脚本

**功能：**
- 使用独立的测试数据库运行测试
- 避免污染生产数据
- 自动清理测试数据

**使用方法：**

```bash
# 运行所有测试
./scripts/run_tests.sh

# 仅运行回归测试
./scripts/run_tests.sh regression

# 仅运行稳定性测试
./scripts/run_tests.sh stability

# 仅运行性能测试
./scripts/run_tests.sh performance
```

**特性：**
- ✅ 自动设置测试环境变量 `TEST_MODE=true`
- ✅ 使用独立的 `test_memory.db` 数据库
- ✅ 测试完成后自动清理测试数据
- ✅ 不会影响生产数据 `memory.db`

**测试类型说明：**

| 测试类型 | 说明 | 耗时 |
|---------|------|------|
| regression | 回归测试：验证核心功能 | ~10s |
| stability | 稳定性测试：检查规则遵循率 | ~30s |
| performance | 性能测试：批量写入压力测试 | ~2min |

**输出示例：**
```
======================================
🧪 个人记忆系统测试套件
======================================

✅ 已激活虚拟环境
✅ 已设置测试模式环境变量

======================================
运行测试套件
======================================

1️⃣  回归测试
--------------------------------------
⚠️  测试模式: 使用测试数据库 test_memory.db
✅ 测试 1: 添加记忆... 通过
✅ 测试 2: 搜索记忆... 通过
...

======================================
🧹 清理测试数据
======================================
✅ 已删除测试数据库
✅ 已删除测试条目目录

======================================
✅ 测试完成！
======================================
```

---

## 🔧 配置说明

### config.py - 环境配置

系统通过 `config.py` 区分生产环境和测试环境：

**生产环境（默认）：**
- 数据库: `memory.db`
- 条目目录: `entries/`

**测试环境（设置 TEST_MODE=true）：**
- 数据库: `test_memory.db`
- 条目目录: `test_entries/`

**手动切换测试模式：**

```python
# 在 Python 脚本中
import config
config.setup_test_mode()

# 或通过环境变量
import os
os.environ['TEST_MODE'] = 'true'
```

---

## 📋 最佳实践

### 定期维护

建议每月运行一次清理脚本：

```bash
# 1. 先查看要清理的内容
python scripts/cleanup.py --dry-run

# 2. 确认无误后执行清理
python scripts/cleanup.py
```

### 测试前后

开发新功能时：

```bash
# 1. 运行测试验证功能
./scripts/run_tests.sh

# 2. 如果需要调试，保留测试数据
export TEST_MODE=true
python tests/test_regression.py
# 不会自动清理，可以手动检查 test_memory.db

# 3. 手动清理测试数据
rm -f test_memory.db
rm -rf test_entries/
```

### 故障排查

如果遇到搜索问题：

```bash
# 1. 检查数据一致性
python -c "
import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('memory.db') as db:
        cursor = await db.execute('SELECT COUNT(*) FROM memories')
        main_count = (await cursor.fetchone())[0]
        cursor = await db.execute('SELECT COUNT(*) FROM memories_fts')
        fts_count = (await cursor.fetchone())[0]
        print(f'主表: {main_count}, FTS5: {fts_count}')

asyncio.run(check())
"

# 2. 运行清理
python scripts/cleanup.py

# 3. 如果问题持续，重建 FTS5 索引
sqlite3 memory.db "DELETE FROM memories_fts; INSERT INTO memories_fts(id, title, content) SELECT id, title, content FROM memories;"
```

---

## ⚠️ 注意事项

1. **清理前备份**：虽然清理脚本只删除无用文件，但建议定期备份 `memory.db`
2. **测试隔离**：始终使用 `run_tests.sh` 运行测试，避免直接运行测试脚本
3. **生产数据**：不要在生产环境设置 `TEST_MODE=true`
4. **手动清理**：如果手动删除了数据库记录，记得运行清理脚本清理对应的 JSON 文件

---

## 🆘 故障恢复

### 误删数据

如果不小心删除了重要记忆：

1. 立即停止所有操作
2. 查找最近的备份
3. 检查飞书同步表格（如果启用了同步）

### 数据库损坏

如果数据库损坏：

```bash
# 1. 备份当前数据库
cp memory.db memory.db.backup

# 2. 尝试修复
sqlite3 memory.db "PRAGMA integrity_check;"

# 3. 如果无法修复，从飞书重新导入
# （需要实现导入功能）
```

---

## 📞 获取帮助

如果遇到问题，请检查：
1. 日志输出
2. 数据库文件权限
3. 磁盘空间
4. Python 环境和依赖

更多信息请参考主 README.md。

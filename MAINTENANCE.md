# 系统维护指南

本文档说明如何维护个人记忆系统，保持其健康运行。

## 📋 目录

1. [清理工具](#清理工具)
2. [测试隔离](#测试隔离)
3. [定期维护](#定期维护)
4. [故障排查](#故障排查)
5. [备份策略](#备份策略)

---

## 🧹 清理工具

### 为什么需要清理？

在以下情况下，系统会产生无用文件：

1. **删除记忆后**：JSON 文件不会自动删除
2. **测试期间**：测试脚本可能创建大量数据
3. **索引不同步**：FTS5 索引可能包含已删除记忆的引用

### 使用清理脚本

```bash
# 查看将要清理的内容（推荐）
python scripts/cleanup.py --dry-run

# 执行清理
python scripts/cleanup.py
```

### 清理内容

| 清理项 | 说明 | 风险 |
|-------|------|------|
| 无用 JSON 文件 | 数据库未引用的文件 | ✅ 安全 |
| FTS5 过期记录 | 索引中的过期数据 | ✅ 安全 |
| 空目录 | entries 下的空目录 | ✅ 安全 |

**注意**：清理脚本只删除确认无用的数据，不会影响有效记忆。

---

## 🧪 测试隔离

### 为什么需要隔离？

直接运行测试脚本会：

- ❌ 污染生产数据库
- ❌ 创建大量测试记忆
- ❌ 影响 FTS5 索引

### 使用测试脚本

```bash
# 运行所有测试（推荐）
./scripts/run_tests.sh

# 运行特定测试
./scripts/run_tests.sh regression   # 回归测试
./scripts/run_tests.sh stability    # 稳定性测试
./scripts/run_tests.sh performance  # 性能测试
```

### 测试隔离机制

测试脚本会自动：

1. ✅ 设置 `TEST_MODE=true` 环境变量
2. ✅ 使用独立的 `test_memory.db`
3. ✅ 使用独立的 `test_entries/` 目录
4. ✅ 测试完成后清理测试数据

### 手动控制测试模式

如果需要调试测试：

```bash
# 启用测试模式
export TEST_MODE=true

# 运行测试（不会自动清理）
python tests/test_regression.py

# 检查测试数据
sqlite3 test_memory.db "SELECT COUNT(*) FROM memories"

# 手动清理
rm -rf test_memory.db test_entries/
```

---

## 🗓️ 定期维护

### 维护清单

建议每月执行一次：

```bash
# 1. 备份数据库
cp memory.db backups/memory_$(date +%Y%m%d).db

# 2. 运行清理
python scripts/cleanup.py --dry-run  # 先检查
python scripts/cleanup.py             # 再清理

# 3. 检查数据一致性
python -c "
import asyncio
import aiosqlite

async def check():
    async with aiosqlite.connect('memory.db') as db:
        # 主表记录数
        cursor = await db.execute('SELECT COUNT(*) FROM memories')
        main_count = (await cursor.fetchone())[0]
        
        # FTS5 记录数
        cursor = await db.execute('SELECT COUNT(*) FROM memories_fts')
        fts_count = (await cursor.fetchone())[0]
        
        # JSON 文件数
        import os
        json_count = sum(1 for root, dirs, files in os.walk('entries') 
                        for f in files if f.endswith('.json'))
        
        print(f'主表: {main_count}, FTS5: {fts_count}, JSON: {json_count}')
        
        if main_count == fts_count == json_count:
            print('✅ 数据一致性检查通过')
        else:
            print('⚠️  数据不一致，建议运行清理脚本')

asyncio.run(check())
"

# 4. 运行测试（可选）
./scripts/run_tests.sh regression
```

### 自动化维护（可选）

使用 cron 定期清理：

```bash
# 设置定期任务
./scripts/setup_cron.sh
```

---

## 🔧 故障排查

### 搜索返回结果不完整

**症状**：搜索只返回部分记忆，但数据库中确实有更多记录。

**原因**：
1. entry_path 路径错误
2. JSON 文件丢失
3. FTS5 索引不同步

**解决方案**：

```bash
# 1. 检查数据一致性
sqlite3 memory.db "
SELECT 
    (SELECT COUNT(*) FROM memories) as main_count,
    (SELECT COUNT(*) FROM memories_fts) as fts_count
"

# 2. 检查 entry_path
sqlite3 memory.db "SELECT id, title, entry_path FROM memories LIMIT 5"

# 3. 检查 JSON 文件是否存在
python -c "
import sqlite3
import os

conn = sqlite3.connect('memory.db')
cursor = conn.execute('SELECT id, entry_path FROM memories')

missing = []
for row in cursor:
    if not os.path.exists(row[1]):
        missing.append((row[0], row[1]))

if missing:
    print(f'❌ 缺失 {len(missing)} 个 JSON 文件:')
    for id, path in missing[:10]:
        print(f'  - {id}: {path}')
else:
    print('✅ 所有 JSON 文件都存在')
"

# 4. 如果是路径问题，批量修复
# 例如：将 'Jason记忆' 替换为 'Jasonmemory'
sqlite3 memory.db "
UPDATE memories 
SET entry_path = REPLACE(entry_path, '旧路径', '新路径');
SELECT changes();
"

# 5. 重建 FTS5 索引
sqlite3 memory.db "
DELETE FROM memories_fts;
INSERT INTO memories_fts(id, title, content) 
SELECT id, title, content FROM memories;
"

# 6. 运行清理脚本
python scripts/cleanup.py
```

### 测试污染了生产数据

**症状**：生产数据库中出现了大量测试数据。

**解决方案**：

```bash
# 1. 立即停止所有测试进程
ps aux | grep test | grep -v grep | awk '{print $2}' | xargs kill

# 2. 识别测试数据（通常标题包含"测试"）
sqlite3 memory.db "SELECT COUNT(*) FROM memories WHERE title LIKE '%测试%'"

# 3. 删除测试数据
sqlite3 memory.db "
DELETE FROM memories WHERE title LIKE '%测试%';
SELECT changes();
"

# 4. 清理无用文件
python scripts/cleanup.py

# 5. 重新同步到飞书（如果启用）
python -c "
import asyncio
from models import MemorySyncToFeishuInput
from tools.memory_sync_to_feishu import memory_sync_to_feishu

asyncio.run(memory_sync_to_feishu(MemorySyncToFeishuInput(dry_run=False)))
"
```

### 飞书同步失败

**症状**：飞书同步卡住或失败。

**解决方案**：

```bash
# 1. 检查 token 是否有效
cat .user_token.json | python -m json.tool

# 2. 测试飞书连接
python -c "
import asyncio
from sync.feishu_client import FeishuClient

async def test():
    try:
        client = FeishuClient()
        token = await client.get_access_token()
        print(f'✅ Token 有效: {token[:20]}...')
        
        result = await client.list_records(page_size=1)
        print(f'✅ 读取成功: {len(result.get(\"items\", []))} 条')
    except Exception as e:
        print(f'❌ 连接失败: {e}')

asyncio.run(test())
"

# 3. 如果 token 过期，重新授权
# （需要手动访问飞书授权页面）

# 4. 禁用自动同步（如果频繁失败）
# 修改 memory_add 函数，注释掉 auto_sync 调用
```

---

## 💾 备份策略

### 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash
# 每日备份脚本

BACKUP_DIR="$HOME/backups/memory"
mkdir -p "$BACKUP_DIR"

# 备份数据库
DATE=$(date +%Y%m%d_%H%M%S)
cp memory.db "$BACKUP_DIR/memory_$DATE.db"

# 只保留最近 30 天的备份
find "$BACKUP_DIR" -name "memory_*.db" -mtime +30 -delete

echo "✅ 备份完成: memory_$DATE.db"
```

### 添加到 crontab

```bash
# 每天凌晨 3 点备份
0 3 * * * cd /path/to/memory-mcp-server && bash scripts/backup.sh
```

### 手动备份

```bash
# 完整备份（数据库 + 条目）
tar -czf memory_backup_$(date +%Y%m%d).tar.gz memory.db entries/

# 仅备份数据库
cp memory.db memory_backup_$(date +%Y%m%d).db
```

### 恢复备份

```bash
# 恢复数据库
cp memory_backup_20260117.db memory.db

# 恢复完整备份
tar -xzf memory_backup_20260117.tar.gz
```

---

## 📊 健康检查脚本

创建 `scripts/health_check.py`：

```python
#!/usr/bin/env python3
"""系统健康检查脚本"""

import asyncio
import aiosqlite
import os
from pathlib import Path

async def health_check():
    print("=" * 60)
    print("🏥 个人记忆系统健康检查")
    print("=" * 60)
    print()
    
    issues = []
    
    # 1. 检查数据库文件
    if not os.path.exists("memory.db"):
        issues.append("❌ 数据库文件不存在")
    else:
        print("✅ 数据库文件存在")
        
        # 检查数据一致性
        async with aiosqlite.connect("memory.db") as db:
            cursor = await db.execute("SELECT COUNT(*) FROM memories")
            main_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM memories_fts")
            fts_count = (await cursor.fetchone())[0]
            
            print(f"   主表记录: {main_count}")
            print(f"   FTS5 记录: {fts_count}")
            
            if main_count != fts_count:
                issues.append(f"⚠️  索引不同步：主表 {main_count}，FTS5 {fts_count}")
    
    # 2. 检查 JSON 文件
    if not os.path.exists("entries"):
        issues.append("❌ 条目目录不存在")
    else:
        json_count = sum(1 for root, dirs, files in os.walk("entries")
                        for f in files if f.endswith(".json"))
        print(f"✅ JSON 文件: {json_count} 个")
        
        if main_count != json_count:
            issues.append(f"⚠️  文件数不匹配：数据库 {main_count}，JSON {json_count}")
    
    # 3. 检查配置文件
    if not os.path.exists(".env"):
        issues.append("⚠️  .env 配置文件不存在")
    else:
        print("✅ .env 配置文件存在")
    
    # 4. 检查虚拟环境
    if not os.path.exists("venv"):
        issues.append("⚠️  虚拟环境不存在")
    else:
        print("✅ 虚拟环境存在")
    
    print()
    print("=" * 60)
    
    if issues:
        print("⚠️  发现以下问题：")
        for issue in issues:
            print(f"  {issue}")
        print()
        print("建议运行: python scripts/cleanup.py")
    else:
        print("✅ 系统状态健康")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(health_check())
```

运行健康检查：

```bash
python scripts/health_check.py
```

---

## 🆘 紧急恢复

如果系统出现严重问题：

1. **立即停止所有操作**
2. **备份当前状态**（即使已损坏）
3. **从最近的备份恢复**
4. **运行健康检查**
5. **重新同步飞书数据**（如果备份不完整）

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. 检查日志输出
2. 运行健康检查脚本
3. 查看测试报告
4. 参考 `scripts/README.md`

更多信息请参考主 README.md。

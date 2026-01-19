# 更新日志

## [2026-01-17] - 系统清理与测试隔离

### 🎯 背景

在进行性能测试时，由于测试脚本失控，导致系统产生了大量无用数据：
- 1334 条测试记忆记录
- 1401 个无用 JSON 文件
- FTS5 索引包含大量过期数据
- entry_path 路径错误导致部分记忆无法搜索

### ✅ 已完成

#### 1. 数据清理

- **清理测试数据**
  - 删除 1334 条测试记忆记录
  - 删除 1401 个无用 JSON 文件（约 700KB）
  - 重建 FTS5 索引（从 1404 条减少到 15 条）
  
- **修复数据问题**
  - 修复 entry_path 路径错误（"Jason记忆" → "Jasonmemory"）
  - 恢复 11 条"丢失"的记忆（实际是路径错误导致搜索跳过）
  - 删除空数据库文件 `memories.db`

- **重新同步飞书**
  - 删除飞书中的 28 条测试记录
  - 重新同步 15 条真实记忆到飞书
  - 验证本地与飞书数据一致性

#### 2. 清理工具

新增 `scripts/cleanup.py` 脚本：

- ✅ 清理无用的 JSON 文件（数据库中未引用的）
- ✅ 清理 FTS5 索引中的过期数据
- ✅ 清理空目录
- ✅ 支持 `--dry-run` 试运行模式
- ✅ 详细的清理报告

**使用方法：**
```bash
# 试运行（推荐先运行）
python scripts/cleanup.py --dry-run

# 实际清理
python scripts/cleanup.py
```

#### 3. 测试隔离

新增测试隔离机制，避免测试数据污染生产数据：

- **配置系统** (`config.py`)
  - 通过 `TEST_MODE` 环境变量区分生产/测试环境
  - 测试模式使用独立的 `test_memory.db` 和 `test_entries/`
  - 生产模式使用 `memory.db` 和 `entries/`

- **测试脚本** (`scripts/run_tests.sh`)
  - 自动设置 `TEST_MODE=true`
  - 自动清理测试前的旧数据
  - 自动清理测试后的新数据
  - 支持运行特定类型的测试（regression/stability/performance）

- **数据库隔离**
  - 修改 `storage/db.py` 使用 `config.py` 的配置
  - 测试和生产完全隔离，互不影响

**使用方法：**
```bash
# 运行所有测试
./scripts/run_tests.sh

# 运行特定测试
./scripts/run_tests.sh regression
./scripts/run_tests.sh stability
./scripts/run_tests.sh performance
```

#### 4. 其他工具

- **定期维护脚本** (`scripts/setup_cron.sh`)
  - 帮助设置 cron 定期清理任务
  - 建议每月运行一次清理

- **文档完善**
  - `scripts/README.md`: 维护脚本使用说明
  - `MAINTENANCE.md`: 系统维护指南
  - `CHANGELOG.md`: 本更新日志

- **.gitignore 更新**
  - 添加测试数据忽略规则
  - 添加用户 token 忽略规则

### 📊 系统状态

**清理前：**
- 本地记忆：1404 条（含 1334 条测试数据）
- JSON 文件：1416 个
- FTS5 索引：1404 条
- 飞书记录：28 条（含测试数据）

**清理后：**
- 本地记忆：15 条（纯真实数据）✅
- JSON 文件：15 个 ✅
- FTS5 索引：15 条 ✅
- 飞书记录：15 条 ✅

### 🔍 问题根因

1. **性能测试脚本失控**
   - 测试脚本在后台持续运行 12+ 分钟
   - 每秒写入约 2 条记忆，累计 1334 条
   - 每次写入都触发飞书自动同步（耗时 3 秒）

2. **entry_path 路径错误**
   - 部分记忆的 entry_path 包含错误路径
   - `search_memories` 函数依赖 JSON 文件存在
   - 导致 11 条记忆"丢失"（实际是被跳过）

3. **测试数据未隔离**
   - 测试直接使用生产数据库
   - 没有自动清理机制
   - 导致测试数据污染生产环境

### 🛡️ 预防措施

现在已实施以下措施：

1. **测试隔离**
   - 必须通过 `run_tests.sh` 运行测试
   - 测试使用独立数据库
   - 自动清理测试数据

2. **定期清理**
   - 提供清理脚本和文档
   - 建议每月运行一次
   - 可设置 cron 自动执行

3. **数据一致性**
   - 清理脚本验证主表/FTS5/JSON 一致性
   - 修复 entry_path 路径问题
   - 维护指南提供故障排查步骤

### 📝 使用建议

1. **运行测试时**
   ```bash
   # 始终使用测试脚本
   ./scripts/run_tests.sh
   
   # 不要直接运行
   python tests/test_performance.py  # ❌ 会污染生产数据
   ```

2. **定期维护**
   ```bash
   # 每月一次
   python scripts/cleanup.py --dry-run  # 先检查
   python scripts/cleanup.py             # 再清理
   ```

3. **删除大量记忆后**
   ```bash
   # 立即运行清理
   python scripts/cleanup.py
   ```

4. **数据异常时**
   ```bash
   # 运行健康检查（待实现）
   python scripts/health_check.py
   
   # 运行清理
   python scripts/cleanup.py
   
   # 如果问题持续，参考 MAINTENANCE.md
   ```

### 🚀 下一步

可选的改进方向（未实施）：

1. **禁用自动同步**
   - 当前每次 `memory_add` 都自动同步飞书（耗时 3 秒）
   - 可改为批量同步或手动触发

2. **健康检查脚本**
   - 自动检查数据一致性
   - 提供修复建议

3. **备份自动化**
   - 定期自动备份数据库
   - 保留 N 天的备份

4. **从飞书导入**
   - 如果本地数据丢失，可从飞书恢复

### 📚 相关文档

- `scripts/README.md` - 维护脚本使用说明
- `MAINTENANCE.md` - 完整的维护指南
- `.gitignore` - 已更新，忽略测试数据

---

## [历史版本]

### [2026-01-11] - v1.0 初始版本

- 基础记忆管理功能
- 类别扩展（knowledge, reference, digest）
- 标签支持
- 飞书同步

### [2026-01-17] - v1.1 智能判定与冲突检测

- 智能分类建议
- 冲突检测
- 过期标记
- 测试套件（回归、稳定性、性能）

# MCP Server 配置详细指南

## 🎯 配置目标

在 Cursor 中配置 personal_memory MCP Server，让 AI 能够调用记忆工具。

## 📋 配置步骤

### 方法 1: 自动配置（推荐）

运行自动配置脚本：

```bash
cd memory-mcp-server
./setup_mcp_config.sh
```

脚本会自动：
1. 检测项目路径和 Python 路径
2. 创建或更新 Cursor 配置文件
3. 备份现有配置（如果存在）

### 方法 2: 手动配置

#### 步骤 1: 找到配置文件位置

**macOS 路径**:
```
~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

#### 步骤 2: 创建或编辑配置文件

如果文件不存在，创建它；如果存在，编辑它。

#### 步骤 3: 添加配置内容

```json
{
  "mcpServers": {
    "personal_memory": {
      "command": "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/venv/bin/python",
      "args": [
        "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/main.py"
      ],
      "env": {}
    }
  }
}
```

**重要**: 请将路径替换为您的实际路径！

#### 步骤 4: 获取正确的路径

运行以下命令获取路径：

```bash
cd memory-mcp-server
source venv/bin/activate
echo "Python 路径: $(which python)"
echo "项目路径: $(pwd)/main.py"
```

#### 步骤 5: 验证配置

1. 保存配置文件
2. **完全重启 Cursor**（重要！）
3. 在 Cursor 中尝试使用记忆功能

## 🔍 验证配置是否成功

### 方法 1: 查看 Cursor 日志

1. 打开 Cursor
2. 打开开发者工具（Help > Toggle Developer Tools）
3. 查看 Console 标签
4. 查找 MCP Server 相关的日志

### 方法 2: 测试功能

在 Cursor 中尝试以下对话：

**测试 1: 查询目标**
```
我的目标是什么？
```

**期望**: AI 应该调用 `memory_search` 工具，并返回"核心目标：50岁退休"

**测试 2: 保存记忆**
```
记住：我周二有禅修课
```

**期望**: AI 应该调用 `memory_add` 工具，并确认"已记录"

## ⚠️ 常见问题

### 问题 1: 配置文件找不到

**解决方案**:
```bash
# 创建配置目录
mkdir -p ~/Library/Application\ Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/

# 创建配置文件
touch ~/Library/Application\ Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

### 问题 2: Python 路径错误

**解决方案**:
- 使用虚拟环境中的 Python（推荐）: `venv/bin/python`
- 或使用系统 Python: `/usr/bin/python3` 或 `/opt/homebrew/bin/python3`

**检查 Python 路径**:
```bash
cd memory-mcp-server
source venv/bin/activate
which python  # 复制这个路径
```

### 问题 3: 配置后没有生效

**解决方案**:
1. **完全关闭并重启 Cursor**（不只是重新加载窗口）
2. 检查配置文件 JSON 格式是否正确
3. 检查路径是否正确（使用绝对路径）
4. 查看 Cursor 开发者工具中的错误信息

### 问题 4: MCP Server 无法启动

**解决方案**:
1. 手动测试 MCP Server:
   ```bash
   cd memory-mcp-server
   source venv/bin/activate
   python main.py
   ```
   如果报错，说明服务器本身有问题

2. 检查依赖是否安装:
   ```bash
   pip install -r requirements.txt
   ```

3. 检查数据库是否初始化:
   ```bash
   python storage/seed.py
   ```

## 📝 配置文件示例（完整版）

如果您的配置文件中已经有其他 MCP Server，可以这样添加：

```json
{
  "mcpServers": {
    "existing_server": {
      "command": "...",
      "args": [...]
    },
    "personal_memory": {
      "command": "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/venv/bin/python",
      "args": [
        "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/main.py"
      ],
      "env": {}
    }
  }
}
```

## 🎉 配置成功后

配置成功后，您应该能够：

1. ✅ 在 Cursor 中查询记忆（"我的目标是什么"）
2. ✅ 在 Cursor 中保存记忆（"记住：XXX"）
3. ✅ AI 会自动调用相应的工具

## 📞 需要帮助？

如果遇到问题：
1. 运行 `./setup_mcp_config.sh` 自动配置
2. 运行 `./quick_start.sh` 验证环境
3. 查看 Cursor 开发者工具中的错误信息
4. 检查 `MCP_CONFIG.md` 获取更多信息

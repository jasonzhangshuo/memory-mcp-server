# MCP Server 配置指南

## Cursor 配置

在 Cursor 中配置 MCP Server，需要在 Cursor 的设置文件中添加配置。

### 配置文件位置

- macOS: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`
- 或者通过 Cursor 设置界面配置

### 配置内容

```json
{
  "mcpServers": {
    "personal_memory": {
      "command": "python",
      "args": [
        "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/main.py"
      ],
      "env": {}
    }
  }
}
```

**注意**：请将路径替换为您的实际项目路径。

### 验证配置

1. 重启 Cursor
2. 打开开发者工具查看 MCP Server 连接状态
3. 尝试使用记忆相关功能，观察是否调用了工具

## Claude Desktop 配置

如果使用 Claude Desktop，需要在配置文件中添加：

### 配置文件位置

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

### 配置内容

```json
{
  "mcpServers": {
    "personal_memory": {
      "command": "python",
      "args": [
        "/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/main.py"
      ]
    }
  }
}
```

## 测试 MCP Server

运行以下命令测试 MCP Server 是否正常工作：

```bash
cd memory-mcp-server
source venv/bin/activate
python main.py
```

如果看到服务器启动信息，说明配置正确。

## 故障排查

1. **Python 路径问题**
   - 确保使用虚拟环境中的 Python：`venv/bin/python`
   - 或使用完整路径

2. **依赖问题**
   - 确保已安装所有依赖：`pip install -r requirements.txt`

3. **数据库问题**
   - 确保已运行种子数据初始化：`python storage/seed.py`

4. **权限问题**
   - 确保脚本有执行权限：`chmod +x main.py`

# MCP 服务器设置指南

## 问题：MCP服务器没有出现在Cursor中

如果 `personal_memory` 没有出现在Cursor的MCP服务器列表中，请按照以下步骤操作：

## 方法1：通过Cursor UI界面添加（推荐）

1. **打开Cursor设置**
   - 在Cursor中，点击界面上的 "Add a Custom MCP Server" 按钮
   - 或者通过设置菜单进入MCP配置

2. **添加MCP服务器**
   - 服务器名称：`personal_memory`
   - 命令：`/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/venv/bin/python`
   - 参数：`/Users/zhangshuo/Library/Mobile Documents/com~apple~CloudDocs/Jason记忆/memory-mcp-server/main.py`

3. **保存并重启**
   - 保存配置
   - **完全退出Cursor**（Command+Q，不要只是关闭窗口）
   - 重新打开Cursor

## 方法2：手动编辑配置文件

如果UI界面不可用，可以手动编辑配置文件：

1. **打开配置文件**
   ```bash
   open ~/Library/Application\ Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   ```

2. **确保配置内容正确**
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

3. **完全重启Cursor**
   - 完全退出Cursor（Command+Q）
   - 重新打开Cursor

## 验证是否成功

1. **检查MCP服务器列表**
   - 在Cursor的MCP设置中，应该能看到 `personal_memory` 服务器
   - 应该显示有8个工具可用

2. **测试功能**
   - 在对话中尝试："我的目标是什么？"
   - 如果AI能返回"核心目标：50岁退休"，说明MCP工具正常工作

3. **查看开发者工具**
   - Help > Toggle Developer Tools
   - 查看Console中是否有MCP相关的错误

## 常见问题

### Q: 配置文件存在但服务器不出现？
A: 
1. 确保完全重启了Cursor（不是重新加载窗口）
2. 检查配置文件JSON格式是否正确
3. 尝试通过UI界面重新添加

### Q: 服务器出现但工具不可用？
A:
1. 检查Python路径是否正确
2. 检查依赖是否安装：`pip install -r requirements.txt`
3. 查看开发者工具中的错误信息

### Q: 如何确认MCP服务器正在运行？
A:
1. 查看Cursor的MCP服务器列表，服务器应该显示为"已启用"
2. 测试工具调用功能
3. 查看开发者工具中的MCP连接日志

## 快速测试命令

```bash
# 测试MCP服务器是否能启动
cd memory-mcp-server
source venv/bin/activate
python main.py
```

如果看到FastMCP的启动信息，说明服务器本身没问题。

# 自动同步任务指南

## ✅ 已设置

自动同步任务已成功设置！

## 📋 任务信息

- **执行时间**: 每天 23:30（晚上11点30分）
- **任务类型**: macOS LaunchAgent
- **配置文件**: `~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist`
- **日志文件**: `memory-mcp-server/sync.log`
- **错误日志**: `memory-mcp-server/sync_error.log`

## 🔧 管理命令

### 查看任务状态
```bash
launchctl list | grep memory-sync
```

### 查看日志
```bash
# 查看同步日志
tail -f memory-mcp-server/sync.log

# 查看错误日志
tail -f memory-mcp-server/sync_error.log
```

### 重新加载任务
```bash
launchctl unload ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
launchctl load ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
```

### 卸载任务
```bash
launchctl unload ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
rm ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
```

### 修改执行时间

编辑配置文件：
```bash
open ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
```

修改 `Hour` 和 `Minute` 字段，然后重新加载任务。

## ⚠️ 注意事项

1. **电脑需要开机**: 定时任务只在电脑开机时执行
2. **用户需要登录**: 需要用户登录状态
3. **网络连接**: 需要网络连接才能同步到飞书

## 🧪 测试

如果想立即测试同步是否正常，可以手动运行：

```bash
cd memory-mcp-server
source venv/bin/activate
python sync/sync_to_feishu.py
```

## 📝 同步特点

- ✅ **增量同步**: 自动跳过已同步的记录
- ✅ **错误处理**: 失败的记录会记录在错误日志中
- ✅ **自动重试**: 如果某次同步失败，下次会继续尝试

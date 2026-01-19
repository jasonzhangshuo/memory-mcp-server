# 飞书同步机制说明

## 当前状态：手动触发

目前的同步机制是**手动触发**的，需要运行以下命令：

```bash
cd memory-mcp-server
source venv/bin/activate
python sync/sync_to_feishu.py
```

## 同步特点

- ✅ **增量同步**：自动跳过已同步的记录
- ✅ **批量处理**：一次同步所有新记录
- ✅ **错误处理**：失败的记录会显示错误信息

## 自动同步方案

如果需要实现自动同步，有以下几种方案：

### 方案 1: 定时任务（Cron）

在 macOS/Linux 上使用 `crontab`：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每小时同步一次）
0 * * * * cd /path/to/memory-mcp-server && /path/to/venv/bin/python sync/sync_to_feishu.py >> /path/to/sync.log 2>&1
```

### 方案 2: 系统定时任务（macOS LaunchAgent）

创建 LaunchAgent 配置文件：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jason.memory-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/memory-mcp-server/sync/sync_to_feishu.py</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

### 方案 3: Python 定时任务（推荐）

创建一个后台服务，使用 `schedule` 或 `APScheduler` 库实现定时同步。

## 推荐方案

对于个人使用，建议：
- **手动同步**：需要时手动运行（当前方式）
- **定时同步**：如果需要，可以设置每天或每小时自动同步

需要我帮你实现自动同步功能吗？

#!/bin/bash
# 设置自动同步任务 - 每天23:30执行

set -e

echo "=========================================="
echo "设置飞书自动同步任务"
echo "=========================================="
echo ""

# 获取项目路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_PATH="$SCRIPT_DIR"
PYTHON_PATH="$PROJECT_PATH/venv/bin/python"
SYNC_SCRIPT="$PROJECT_PATH/sync/sync_to_feishu.py"

echo "📁 项目路径: $PROJECT_PATH"
echo "🐍 Python 路径: $PYTHON_PATH"
echo "📝 同步脚本: $SYNC_SCRIPT"
echo ""

# 检查文件是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 错误: Python 路径不存在"
    echo "   请先创建虚拟环境: python3 -m venv venv"
    exit 1
fi

if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "❌ 错误: 同步脚本不存在"
    exit 1
fi

# LaunchAgent 目录
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.jason.memory-sync.feishu.plist"

echo "📝 LaunchAgent 文件: $PLIST_FILE"
echo ""

# 创建 LaunchAgents 目录（如果不存在）
mkdir -p "$LAUNCH_AGENTS_DIR"

# 创建 plist 文件
cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jason.memory-sync.feishu</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SYNC_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_PATH</string>
    <key>StandardOutPath</key>
    <string>$PROJECT_PATH/sync.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_PATH/sync_error.log</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent 配置文件已创建"
echo ""

# 加载 LaunchAgent
echo "🔄 加载定时任务..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "✅ 定时任务已设置"
echo ""
echo "=========================================="
echo "✅ 设置完成！"
echo "=========================================="
echo ""
echo "📋 任务信息:"
echo "   执行时间: 每天 23:30"
echo "   日志文件: $PROJECT_PATH/sync.log"
echo "   错误日志: $PROJECT_PATH/sync_error.log"
echo ""
echo "🔧 管理命令:"
echo "   查看状态: launchctl list | grep memory-sync"
echo "   卸载任务: launchctl unload $PLIST_FILE"
echo "   重新加载: launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
echo "   查看日志: tail -f $PROJECT_PATH/sync.log"
echo ""

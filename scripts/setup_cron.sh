#!/bin/bash
# 设置定期清理任务（可选）

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "🕒 设置定期清理任务"
echo "======================================"
echo ""

# 定期清理脚本路径
CLEANUP_SCRIPT="$PROJECT_ROOT/scripts/cleanup.py"

# 检查脚本是否存在
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "❌ 找不到清理脚本: $CLEANUP_SCRIPT"
    exit 1
fi

echo "清理脚本位置: $CLEANUP_SCRIPT"
echo ""

# 创建 cron 任务
# 每月1号凌晨2点运行清理
CRON_CMD="0 2 1 * * cd $PROJECT_ROOT && /usr/bin/python3 scripts/cleanup.py >> logs/cleanup.log 2>&1"

echo "建议的 cron 任务（每月1号凌晨2点）:"
echo "$CRON_CMD"
echo ""

# 询问是否添加
read -p "是否添加到 crontab？(y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 创建日志目录
    mkdir -p "$PROJECT_ROOT/logs"
    
    # 检查是否已存在相同任务
    if crontab -l 2>/dev/null | grep -q "scripts/cleanup.py"; then
        echo "⚠️  已存在类似的定期任务，请手动检查 crontab"
        echo ""
        echo "运行以下命令查看现有任务:"
        echo "  crontab -l"
    else
        # 添加到 crontab
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✅ 已添加定期清理任务"
        echo ""
        echo "查看当前 crontab:"
        crontab -l | tail -5
    fi
else
    echo "⏭️  跳过自动设置"
    echo ""
    echo "如需手动设置，运行:"
    echo "  crontab -e"
    echo ""
    echo "然后添加以下行:"
    echo "  $CRON_CMD"
fi

echo ""
echo "======================================"
echo "💡 其他选项"
echo "======================================"
echo ""
echo "如果不想使用 cron，也可以："
echo "1. 手动定期运行: python scripts/cleanup.py"
echo "2. 使用 launchd (macOS): 创建 ~/Library/LaunchAgents/com.memory.cleanup.plist"
echo "3. 在开发流程中运行: 例如在部署前/后"
echo ""

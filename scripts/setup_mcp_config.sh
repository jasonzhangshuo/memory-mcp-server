#!/bin/bash
# 自动配置 MCP Server 的脚本

set -e

echo "=========================================="
echo "MCP Server 配置助手"
echo "=========================================="
echo ""

# 获取项目路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_PATH="$SCRIPT_DIR/main.py"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

echo "📁 项目路径: $PROJECT_PATH"
echo "🐍 Python 路径: $PYTHON_PATH"
echo ""

# 检查 Python 路径是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 错误: 虚拟环境中的 Python 不存在"
    echo "   请先运行: ./quick_start.sh"
    exit 1
fi

# Cursor 配置文件路径
CURSOR_CONFIG_DIR="$HOME/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings"
CURSOR_CONFIG_FILE="$CURSOR_CONFIG_DIR/cline_mcp_settings.json"

echo "📝 配置文件位置: $CURSOR_CONFIG_FILE"
echo ""

# 创建配置目录（如果不存在）
mkdir -p "$CURSOR_CONFIG_DIR"

# 检查配置文件是否存在
if [ -f "$CURSOR_CONFIG_FILE" ]; then
    echo "⚠️  配置文件已存在，将备份为: ${CURSOR_CONFIG_FILE}.backup"
    cp "$CURSOR_CONFIG_FILE" "${CURSOR_CONFIG_FILE}.backup"
fi

# 创建配置内容
CONFIG_JSON=$(cat <<EOF
{
  "mcpServers": {
    "personal_memory": {
      "command": "$PYTHON_PATH",
      "args": [
        "$PROJECT_PATH"
      ],
      "env": {}
    }
  }
}
EOF
)

# 写入配置文件
echo "$CONFIG_JSON" > "$CURSOR_CONFIG_FILE"

echo "✅ 配置文件已创建/更新"
echo ""
echo "配置内容:"
echo "$CONFIG_JSON" | python3 -m json.tool
echo ""
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 重启 Cursor"
echo "2. 在 Cursor 中测试记忆功能"
echo "3. 尝试说: '我的目标是什么'"
echo ""
echo "如果遇到问题，可以查看备份文件:"
echo "   ${CURSOR_CONFIG_FILE}.backup"
echo ""

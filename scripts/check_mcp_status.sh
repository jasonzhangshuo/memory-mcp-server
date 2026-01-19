#!/bin/bash
# 检查 MCP Server 状态的脚本

echo "=========================================="
echo "MCP Server 状态检查"
echo "=========================================="
echo ""

# 1. 检查配置文件
echo "1️⃣  检查配置文件..."
CONFIG_FILE="$HOME/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "   ✅ 配置文件存在"
    echo "   位置: $CONFIG_FILE"
    echo ""
    echo "   配置内容:"
    cat "$CONFIG_FILE" | python3 -m json.tool 2>/dev/null || cat "$CONFIG_FILE"
else
    echo "   ❌ 配置文件不存在"
    echo "   位置: $CONFIG_FILE"
    echo "   请运行: ./setup_mcp_config.sh"
fi
echo ""

# 2. 检查 Python 路径
echo "2️⃣  检查 Python 路径..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

if [ -f "$PYTHON_PATH" ]; then
    echo "   ✅ Python 路径存在"
    echo "   路径: $PYTHON_PATH"
    echo "   版本: $($PYTHON_PATH --version 2>&1)"
else
    echo "   ❌ Python 路径不存在"
    echo "   路径: $PYTHON_PATH"
    echo "   请先创建虚拟环境: python3 -m venv venv"
fi
echo ""

# 3. 检查 main.py
echo "3️⃣  检查 main.py..."
MAIN_FILE="$SCRIPT_DIR/main.py"

if [ -f "$MAIN_FILE" ]; then
    echo "   ✅ main.py 存在"
    echo "   路径: $MAIN_FILE"
else
    echo "   ❌ main.py 不存在"
    echo "   路径: $MAIN_FILE"
fi
echo ""

# 4. 检查依赖
echo "4️⃣  检查依赖..."
if [ -f "$PYTHON_PATH" ]; then
    cd "$SCRIPT_DIR"
    source venv/bin/activate 2>/dev/null
    if python -c "import fastmcp" 2>/dev/null; then
        echo "   ✅ fastmcp 已安装"
    else
        echo "   ❌ fastmcp 未安装"
        echo "   请运行: pip install -r requirements.txt"
    fi
fi
echo ""

# 5. 检查数据库
echo "5️⃣  检查数据库..."
DB_FILE="$SCRIPT_DIR/memory.db"

if [ -f "$DB_FILE" ]; then
    echo "   ✅ 数据库文件存在"
    echo "   路径: $DB_FILE"
    SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
    echo "   大小: $SIZE"
else
    echo "   ⚠️  数据库文件不存在（首次运行会自动创建）"
    echo "   路径: $DB_FILE"
fi
echo ""

# 6. 测试 MCP Server 初始化
echo "6️⃣  测试 MCP Server 初始化..."
if [ -f "$PYTHON_PATH" ] && [ -f "$MAIN_FILE" ]; then
    cd "$SCRIPT_DIR"
    source venv/bin/activate 2>/dev/null
    OUTPUT=$(python -c "
import sys
sys.path.insert(0, '.')
try:
    from main import mcp
    print('✅ MCP Server 可以正常导入')
    print(f'   名称: {mcp.name}')
except Exception as e:
    print(f'❌ MCP Server 导入失败: {e}')
    sys.exit(1)
" 2>&1)
    echo "$OUTPUT"
else
    echo "   ⚠️  无法测试（Python 或 main.py 不存在）"
fi
echo ""

# 7. 检查运行中的进程
echo "7️⃣  检查运行中的 MCP 进程..."
MCP_PROCESSES=$(ps aux | grep -i "main.py\|personal_memory" | grep -v grep | wc -l | tr -d ' ')
if [ "$MCP_PROCESSES" -gt 0 ]; then
    echo "   ⚠️  发现 $MCP_PROCESSES 个相关进程（MCP 服务器通常由 Cursor 按需启动）"
    ps aux | grep -i "main.py\|personal_memory" | grep -v grep
else
    echo "   ℹ️  没有发现运行中的进程（这是正常的）"
    echo "   MCP Server 由 Cursor 按需启动，不是独立进程"
fi
echo ""

# 总结
echo "=========================================="
echo "📋 总结"
echo "=========================================="
echo ""
echo "MCP Server 工作原理:"
echo "  - MCP Server 不是独立运行的进程"
echo "  - Cursor 在需要调用工具时启动 Python 脚本"
echo "  - 通过 stdio (标准输入输出) 进行通信"
echo ""
echo "验证方法:"
echo "  1. 确保配置文件正确"
echo "  2. 完全重启 Cursor"
echo "  3. 在 Cursor 中测试: '我的目标是什么？'"
echo "  4. 查看 Cursor 开发者工具中的日志"
echo ""

#!/bin/bash
# MCP Server 诊断脚本

echo "=========================================="
echo "MCP Server 诊断报告"
echo "=========================================="
echo ""

# 1. 检查配置文件
echo "1️⃣  配置文件检查"
CONFIG_FILE="$HOME/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "   ✅ 配置文件存在"
    echo "   位置: $CONFIG_FILE"
    echo ""
    echo "   配置内容:"
    cat "$CONFIG_FILE" | python3 -m json.tool 2>/dev/null || echo "   ⚠️  JSON格式可能有问题"
else
    echo "   ❌ 配置文件不存在"
fi
echo ""

# 2. 检查Python路径
echo "2️⃣  Python路径检查"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
if [ -f "$PYTHON_PATH" ]; then
    echo "   ✅ Python路径存在: $PYTHON_PATH"
    echo "   版本: $($PYTHON_PATH --version 2>&1)"
else
    echo "   ❌ Python路径不存在: $PYTHON_PATH"
fi
echo ""

# 3. 检查main.py
echo "3️⃣  main.py检查"
MAIN_FILE="$SCRIPT_DIR/main.py"
if [ -f "$MAIN_FILE" ]; then
    echo "   ✅ main.py存在: $MAIN_FILE"
else
    echo "   ❌ main.py不存在: $MAIN_FILE"
fi
echo ""

# 4. 测试MCP服务器启动
echo "4️⃣  MCP服务器启动测试"
if [ -f "$PYTHON_PATH" ] && [ -f "$MAIN_FILE" ]; then
    cd "$SCRIPT_DIR"
    source venv/bin/activate 2>/dev/null
    timeout 3 $PYTHON_PATH "$MAIN_FILE" 2>&1 | head -10 &
    SERVER_PID=$!
    sleep 2
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "   ✅ MCP服务器可以启动"
        kill $SERVER_PID 2>/dev/null
    else
        echo "   ⚠️  MCP服务器启动测试超时（这可能是正常的）"
    fi
else
    echo "   ⏭️  跳过（Python或main.py不存在）"
fi
echo ""

# 5. 检查依赖
echo "5️⃣  依赖检查"
if [ -f "$PYTHON_PATH" ]; then
    cd "$SCRIPT_DIR"
    source venv/bin/activate 2>/dev/null
    if $PYTHON_PATH -c "import fastmcp" 2>/dev/null; then
        echo "   ✅ fastmcp已安装"
    else
        echo "   ❌ fastmcp未安装"
    fi
fi
echo ""

# 6. 建议
echo "=========================================="
echo "🔧 建议的修复步骤"
echo "=========================================="
echo ""
echo "如果MCP服务器没有出现在Cursor中，请尝试："
echo ""
echo "1. 完全重启Cursor（完全退出应用，不要只是关闭窗口）"
echo "2. 检查Cursor开发者工具（Help > Toggle Developer Tools）中的错误"
echo "3. 尝试通过Cursor的UI界面添加MCP服务器（点击'Add a Custom MCP Server'）"
echo "4. 确保配置文件路径正确："
echo "   $CONFIG_FILE"
echo ""
echo "如果仍然不行，可以尝试："
echo "5. 删除配置文件，然后通过Cursor UI重新添加"
echo "6. 检查Cursor版本是否支持MCP"
echo ""

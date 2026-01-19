#!/bin/bash
# 测试运行脚本：使用独立的测试数据库，避免污染生产数据

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "🧪 个人记忆系统测试套件"
echo "======================================"
echo ""

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 激活虚拟环境
if [ -d "venv/bin" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
else
    echo "❌ 找不到虚拟环境，请先运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 设置测试模式环境变量
export TEST_MODE=true
echo "✅ 已设置测试模式环境变量"
echo ""

# 清理旧的测试数据
if [ -f "test_memory.db" ]; then
    echo "🗑️  清理旧的测试数据库..."
    rm -f test_memory.db
fi

if [ -d "test_entries" ]; then
    echo "🗑️  清理旧的测试条目目录..."
    rm -rf test_entries
fi
echo ""

# 运行测试
echo "======================================"
echo "运行测试套件"
echo "======================================"
echo ""

# 解析命令行参数
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    "regression")
        echo "运行回归测试..."
        python tests/test_regression.py
        ;;
    "stability")
        echo "运行稳定性测试..."
        python tests/stability_score.py
        ;;
    "performance")
        echo "运行性能测试..."
        python tests/test_performance.py
        ;;
    "all")
        echo "运行所有测试..."
        echo ""
        echo "1️⃣  回归测试"
        echo "--------------------------------------"
        python tests/test_regression.py
        echo ""
        echo "2️⃣  稳定性测试"
        echo "--------------------------------------"
        python tests/stability_score.py
        echo ""
        # 性能测试可选（因为耗时较长）
        read -p "是否运行性能测试？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "3️⃣  性能测试"
            echo "--------------------------------------"
            python tests/test_performance.py
        else
            echo "⏭️  跳过性能测试"
        fi
        ;;
    *)
        echo "❌ 未知的测试类型: $TEST_TYPE"
        echo ""
        echo "用法: $0 [test_type]"
        echo ""
        echo "可用的测试类型:"
        echo "  all         - 运行所有测试（默认）"
        echo "  regression  - 仅运行回归测试"
        echo "  stability   - 仅运行稳定性测试"
        echo "  performance - 仅运行性能测试"
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "🧹 清理测试数据"
echo "======================================"

# 清理测试数据
if [ -f "test_memory.db" ]; then
    rm -f test_memory.db
    echo "✅ 已删除测试数据库"
fi

if [ -d "test_entries" ]; then
    rm -rf test_entries
    echo "✅ 已删除测试条目目录"
fi

echo ""
echo "======================================"
echo "✅ 测试完成！"
echo "======================================"

# 取消测试模式
unset TEST_MODE

#!/usr/bin/env python3
"""测试所有 MCP 工具的参数格式

验证所有工具是否能正确接受参数（不再需要 params 包装）。
"""

import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_all_tools():
    """测试所有工具"""
    print("=" * 60)
    print("测试所有 MCP 工具")
    print("=" * 60)
    
    from main import mcp
    from storage.db import init_db
    
    # 初始化数据库
    await init_db()
    
    tests = [
        {
            "name": "memory_search",
            "func": "search_tool",
            "args": {"query": "目标", "category": "goal", "limit": 1}
        },
        {
            "name": "memory_list_projects",
            "func": "list_projects_tool",
            "args": {}
        },
        {
            "name": "memory_stats",
            "func": "stats_tool",
            "args": {}
        },
    ]
    
    results = []
    
    for test in tests:
        print(f"\n测试 {test['name']}...")
        try:
            # 动态获取工具函数
            tool_func = getattr(mcp, test['func'], None)
            if tool_func is None:
                # 尝试从 main 模块导入
                import main
                tool_func = getattr(main, test['func'], None)
            
            if tool_func is None:
                print(f"  ✗ 找不到工具函数 {test['func']}")
                results.append({"name": test['name'], "status": "error", "message": "找不到工具函数"})
                continue
            
            # 检查工具参数格式
            params = tool_func.parameters.get('properties', {})
            if 'params' in params:
                print(f"  ✗ 仍有 params 包装")
                results.append({"name": test['name'], "status": "error", "message": "仍有 params 包装"})
            else:
                print(f"  ✓ 参数格式正确")
                print(f"    参数: {list(params.keys())}")
                results.append({"name": test['name'], "status": "ok"})
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            results.append({"name": test['name'], "status": "error", "message": str(e)})
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    ok_count = sum(1 for r in results if r['status'] == 'ok')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    for result in results:
        status_icon = "✓" if result['status'] == 'ok' else "✗"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result['status'] == 'error' and 'message' in result:
            print(f"    {result['message']}")
    
    print(f"\n总计: {ok_count} 成功, {error_count} 失败")
    
    if error_count == 0:
        print("\n✅ 所有工具参数格式正确！")
        print("现在需要重启 Cursor 来测试实际调用。")
    else:
        print("\n⚠️  部分工具仍有问题，需要修复。")
    
    return error_count == 0

if __name__ == "__main__":
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)

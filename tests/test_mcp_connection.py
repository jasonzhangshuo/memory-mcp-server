#!/usr/bin/env python3
"""测试 MCP Server 连接和工具调用

模拟 Cursor 调用 MCP 工具的过程，验证工具是否能被正确调用。
"""

import sys
import json
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_tool_call():
    """测试工具调用"""
    print("=" * 60)
    print("测试 MCP 工具调用")
    print("=" * 60)
    
    try:
        from main import mcp
        from models import MemorySearchInput
        
        # 创建参数对象
        params = MemorySearchInput(
            query="目标",
            category="goal",
            limit=5
        )
        
        print(f"\n参数对象:")
        print(f"  query: {params.query}")
        print(f"  category: {params.category}")
        print(f"  limit: {params.limit}")
        
        # 转换为字典（MCP 协议可能需要的格式）
        params_dict = params.model_dump(exclude_none=True)
        print(f"\n参数字典:")
        print(json.dumps(params_dict, ensure_ascii=False, indent=2))
        
        # 直接调用工具函数（模拟 MCP 调用）
        print("\n直接调用工具函数...")
        from tools.memory_search import memory_search
        result = await memory_search(params)
        
        result_data = json.loads(result)
        print(f"\n✓ 工具调用成功")
        print(f"  状态: {result_data.get('status')}")
        print(f"  结果数量: {result_data.get('count', 0)}")
        
        if result_data.get('count', 0) > 0:
            first_result = result_data.get('results', [])[0]
            print(f"\n第一个结果:")
            print(f"  标题: {first_result.get('title')}")
            print(f"  内容: {first_result.get('content', '')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 工具调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tool_call())
    sys.exit(0 if success else 1)

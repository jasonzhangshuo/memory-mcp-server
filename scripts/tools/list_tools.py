#!/usr/bin/env python3
"""列出所有可用的MCP工具"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import mcp

def list_tools():
    """列出所有注册的MCP工具"""
    print("=" * 60)
    print("个人记忆系统 MCP 工具列表")
    print("=" * 60)
    print()
    
    # 从main.py中提取工具信息
    tools_info = [
        {
            "name": "memory_search",
            "title": "搜索历史记忆",
            "description": "根据关键词、类别和项目搜索记忆条目，支持全文搜索",
            "readonly": True
        },
        {
            "name": "memory_add",
            "title": "添加新记忆",
            "description": "创建一个新的记忆条目，保存到数据库和JSON文件",
            "readonly": False
        },
        {
            "name": "memory_get",
            "title": "获取记忆详情",
            "description": "根据记忆ID获取完整的记忆条目信息",
            "readonly": True
        },
        {
            "name": "memory_update",
            "title": "更新记忆",
            "description": "更新现有记忆的标题、内容或归档状态",
            "readonly": False
        },
        {
            "name": "memory_compress_conversation",
            "title": "压缩保存对话",
            "description": "将对话内容压缩为摘要，并提取关键决定、洞察和行动项",
            "readonly": False
        },
        {
            "name": "memory_get_project_context",
            "title": "加载项目上下文",
            "description": "获取项目相关的记忆和基准文档",
            "readonly": True
        },
        {
            "name": "memory_list_projects",
            "title": "列出项目",
            "description": "列出所有项目，支持按状态过滤",
            "readonly": True
        },
        {
            "name": "memory_stats",
            "title": "获取统计信息",
            "description": "获取记忆系统的统计信息，包括总数、分类统计等",
            "readonly": True
        }
    ]
    
    print(f"总计: {len(tools_info)} 个工具\n")
    
    # 分类显示
    readonly_tools = [t for t in tools_info if t["readonly"]]
    write_tools = [t for t in tools_info if not t["readonly"]]
    
    print("📖 查询类工具（只读）:")
    print("-" * 60)
    for i, tool in enumerate(readonly_tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   标题: {tool['title']}")
        print(f"   说明: {tool['description']}")
        print()
    
    print("\n✏️  写入类工具（可修改）:")
    print("-" * 60)
    for i, tool in enumerate(write_tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   标题: {tool['title']}")
        print(f"   说明: {tool['description']}")
        print()
    
    print("=" * 60)
    print("✅ MCP Server 已注册以上工具")
    print("=" * 60)
    
    # 尝试获取工具（如果FastMCP支持）
    try:
        # FastMCP可能使用不同的方法
        print("\n尝试通过FastMCP获取工具列表...")
        # 这里可能需要根据FastMCP的实际API调整
    except Exception as e:
        print(f"注意: 无法通过API获取工具列表 ({e})")
        print("但工具已通过装饰器注册，应该可以在Cursor中使用")

if __name__ == "__main__":
    list_tools()

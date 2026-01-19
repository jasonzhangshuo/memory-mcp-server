"""Regression tests for personal memory system.

测试所有基础功能是否正常工作。
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, add_memory, search_memories, get_memory
from tools.memory_add import memory_add
from tools.memory_search import memory_search
from tools.memory_get import memory_get
from tools.memory_update import memory_update
from tools.memory_list_tags import memory_list_tags
from tools.memory_summarize import memory_summarize
from models import (
    MemoryAddInput,
    MemorySearchInput,
    MemoryGetInput,
    MemoryUpdateInput,
    MemoryListTagsInput,
    MemorySummarizeInput
)


async def test_basic_add_search():
    """测试基础添加和搜索功能"""
    print("测试：基础添加和搜索...")
    
    # 添加测试记忆
    add_params = MemoryAddInput(
        category="insight",
        title="测试记忆",
        content="这是一个测试记忆内容",
        project="测试项目",
        importance=3,
        tags=["测试", "回归"]
    )
    result_str = await memory_add(add_params)
    result = json.loads(result_str)
    
    assert result["status"] == "success", "添加失败"
    memory_id = result["id"]
    print(f"  ✓ 添加成功，ID: {memory_id}")
    
    # 搜索测试
    search_params = MemorySearchInput(
        query="测试",
        limit=10
    )
    search_result_str = await memory_search(search_params)
    search_result = json.loads(search_result_str)
    
    assert search_result["status"] == "success", "搜索失败"
    assert search_result["count"] > 0, "未找到测试记忆"
    print(f"  ✓ 搜索成功，找到 {search_result['count']} 条")
    
    return memory_id


async def test_category_extensions():
    """测试新增类别（knowledge/reference/digest）"""
    print("测试：新增类别...")
    
    categories = ["knowledge", "reference", "digest"]
    for category in categories:
        add_params = MemoryAddInput(
            category=category,
            title=f"测试{category}",
            content=f"这是{category}类别的测试内容",
            project="knowledge-base",
            tags=["测试"]
        )
        result_str = await memory_add(add_params)
        result = json.loads(result_str)
        
        assert result["status"] == "success", f"{category} 类别添加失败"
        print(f"  ✓ {category} 类别添加成功")
    
    # 验证检索
    for category in categories:
        search_params = MemorySearchInput(
            query="",
            category=category,
            limit=5
        )
        search_result_str = await memory_search(search_params)
        search_result = json.loads(search_result_str)
        
        assert search_result["status"] == "success", f"{category} 类别搜索失败"
        print(f"  ✓ {category} 类别检索成功")


async def test_tags_support():
    """测试标签支持"""
    print("测试：标签支持...")
    
    # 添加带标签的记忆
    add_params = MemoryAddInput(
        category="knowledge",
        title="带标签的测试",
        content="测试标签功能",
        tags=["标签1", "标签2", "测试"]
    )
    result_str = await memory_add(add_params)
    result = json.loads(result_str)
    
    assert result["status"] == "success", "带标签添加失败"
    print("  ✓ 带标签添加成功")
    
    # 按标签搜索
    search_params = MemorySearchInput(
        query="",
        tags=["标签1"],
        limit=10
    )
    search_result_str = await memory_search(search_params)
    search_result = json.loads(search_result_str)
    
    assert search_result["status"] == "success", "标签搜索失败"
    print(f"  ✓ 标签搜索成功，找到 {search_result['count']} 条")
    
    # 列出标签
    list_tags_params = MemoryListTagsInput()
    tags_result_str = await memory_list_tags(list_tags_params)
    tags_result = json.loads(tags_result_str)
    
    assert tags_result["status"] == "success", "列出标签失败"
    assert len(tags_result["tags"]) > 0, "未找到标签"
    print(f"  ✓ 列出标签成功，共 {len(tags_result['tags'])} 个标签")


async def test_update_and_get():
    """测试更新和获取功能"""
    print("测试：更新和获取...")
    
    # 先添加
    add_params = MemoryAddInput(
        category="insight",
        title="待更新的记忆",
        content="原始内容"
    )
    result_str = await memory_add(add_params)
    result = json.loads(result_str)
    memory_id = result["id"]
    
    # 更新
    update_params = MemoryUpdateInput(
        id=memory_id,
        title="已更新的记忆",
        content="更新后的内容"
    )
    update_result_str = await memory_update(update_params)
    update_result = json.loads(update_result_str)
    
    assert update_result["status"] == "success", "更新失败"
    print("  ✓ 更新成功")
    
    # 获取
    get_params = MemoryGetInput(id=memory_id)
    get_result_str = await memory_get(get_params)
    get_result = json.loads(get_result_str)
    
    assert get_result["status"] == "success", "获取失败"
    assert get_result["entry"]["title"] == "已更新的记忆", "更新未生效"
    print("  ✓ 获取成功，内容已更新")


async def test_summarize():
    """测试总结功能"""
    print("测试：总结功能...")
    
    summarize_params = MemorySummarizeInput(
        save_as_digest=False
    )
    result_str = await memory_summarize(summarize_params)
    result = json.loads(result_str)
    
    assert result["status"] == "success", "总结生成失败"
    assert "summary" in result, "总结结果格式错误"
    print("  ✓ 总结生成成功")


async def run_all_tests():
    """运行所有回归测试"""
    print("=" * 60)
    print("回归测试套件")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    tests = [
        ("基础功能", test_basic_add_search),
        ("类别扩展", test_category_extensions),
        ("标签支持", test_tags_support),
        ("更新和获取", test_update_and_get),
        ("总结功能", test_summarize),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n[{test_name}]")
            await test_func()
            passed += 1
            print(f"  ✓ {test_name} 通过")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test_name} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果：通过 {passed}/{len(tests)}，失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

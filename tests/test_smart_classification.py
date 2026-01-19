"""Smart classification tests.

测试智能分类判定功能。
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.memory_suggest_category import memory_suggest_category
from models import MemorySuggestCategoryInput


# 测试用例
TEST_CASES = {
    "明确 insight": [
        {
            "title": "我发现我总是研究替代到达",
            "content": "我意识到自己有一个模式，就是爱研究不爱到达",
            "expected": "insight",
            "min_confidence": 0.8
        },
        {
            "title": "我决定每天冥想10分钟",
            "content": "我决定从今天开始，每天冥想10分钟",
            "expected": "insight",
            "min_confidence": 0.8
        },
        {
            "title": "我的目标",
            "content": "我的目标是50岁退休，为这个目标做好身体和精神准备",
            "expected": "insight",
            "min_confidence": 0.7
        },
    ],
    "明确 knowledge": [
        {
            "title": "八步骤三种禅修的核心要点",
            "content": "这篇文章讲八步骤很清晰，来源：《修学要领》第三章",
            "expected": "knowledge",
            "min_confidence": 0.8
        },
        {
            "title": "Claude关于AI的回答",
            "content": "这个回答很好，链接：https://example.com",
            "expected": "knowledge",
            "min_confidence": 0.8
        },
        {
            "title": "学习方法",
            "content": "这是一种有效的学习方法，可以参考书籍《XXX》",
            "expected": "knowledge",
            "min_confidence": 0.7
        },
    ],
    "模糊场景": [
        {
            "title": "我看了这篇文章，发现很有启发",
            "content": "我看了这篇文章，发现很有启发，决定要实践",
            "expected": "insight",  # 可能偏向 insight
            "min_confidence": 0.6  # 置信度应该较低
        },
        {
            "title": "学习笔记",
            "content": "今天学习了八步骤，我的理解是...",
            "expected": None,  # 不确定
            "min_confidence": 0.6
        },
    ]
}


async def test_classification(test_name: str, test_cases: list):
    """测试分类判定"""
    print(f"\n测试：{test_name}")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        params = MemorySuggestCategoryInput(
            title=test_case["title"],
            content=test_case["content"]
        )
        
        result_str = await memory_suggest_category(params)
        result = json.loads(result_str)
        
        if result["status"] != "success":
            print(f"  ✗ 用例 {i} 失败：{result.get('message', '未知错误')}")
            failed += 1
            continue
        
        suggestion = result.get("suggestion", {})
        suggested_category = suggestion.get("suggested_category")
        confidence = suggestion.get("confidence", 0)
        expected = test_case.get("expected")
        min_confidence = test_case.get("min_confidence", 0.5)
        
        # 检查置信度
        if confidence < min_confidence:
            print(f"  ✗ 用例 {i} 置信度不足：{confidence} < {min_confidence}")
            failed += 1
            continue
        
        # 如果有预期值，检查是否匹配
        if expected and suggested_category != expected:
            print(f"  ✗ 用例 {i} 分类不匹配：期望 {expected}，得到 {suggested_category}（置信度 {confidence}）")
            failed += 1
            continue
        
        print(f"  ✓ 用例 {i}：{suggested_category}（置信度 {confidence}）")
        passed += 1
    
    return passed, failed


async def run_all_tests():
    """运行所有智能判定测试"""
    print("=" * 60)
    print("智能分类判定测试")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    for test_name, test_cases in TEST_CASES.items():
        passed, failed = await test_classification(test_name, test_cases)
        total_passed += passed
        total_failed += failed
    
    print("\n" + "=" * 60)
    print(f"测试结果：通过 {total_passed}，失败 {total_failed}")
    accuracy = total_passed / (total_passed + total_failed) * 100 if (total_passed + total_failed) > 0 else 0
    print(f"准确率：{accuracy:.1f}%")
    print("=" * 60)
    
    # 验收标准：准确率 >80%
    return accuracy >= 80.0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

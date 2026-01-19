"""Memory suggest category tool implementation.

智能建议分类（insight vs knowledge），使用关键词检测和语义分析。
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import MemorySuggestCategoryInput


# Insight 特征关键词
INSIGHT_KEYWORDS = [
    "我发现", "我意识到", "我觉得", "我认为", "我决定", "我要",
    "我的", "我", "自己", "个人", "感悟", "理解", "觉察",
    "原来", "悟到", "意识到", "发现", "决定", "承诺"
]

# Knowledge 特征关键词
KNOWLEDGE_KEYWORDS = [
    "文章", "资料", "回答", "来源", "链接", "书籍", "视频",
    "课程", "教程", "方法", "理论", "概念", "定义",
    "http://", "https://", "来源：", "出处：", "参考："
]


def count_keywords(text: str, keywords: list) -> int:
    """统计关键词出现次数（支持部分匹配）"""
    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        if keyword.lower() in text_lower:
            count += 1
    return count


def analyze_content_features(title: str, content: str) -> Dict:
    """分析内容特征，判断是 insight 还是 knowledge"""
    
    # 合并标题和内容
    full_text = f"{title} {content}"
    
    # 1. 关键词检测
    insight_score = count_keywords(full_text, INSIGHT_KEYWORDS)
    knowledge_score = count_keywords(full_text, KNOWLEDGE_KEYWORDS)
    
    # 2. 第一人称检测
    first_person_patterns = [
        r"我[发现|意识到|觉得|认为|决定|要|的]",
        r"自己[的|会|能]",
        r"个人[的|理解|感悟]"
    ]
    first_person_count = sum(len(re.findall(pattern, full_text)) for pattern in first_person_patterns)
    
    # 3. 来源信息检测
    source_patterns = [
        r"http[s]?://",
        r"来源[：:]",
        r"出处[：:]",
        r"参考[：:]",
        r"《.*》",
        r"作者[：:]"
    ]
    source_count = sum(len(re.findall(pattern, full_text)) for pattern in source_patterns)
    
    # 4. 计算综合得分
    # Insight 得分：关键词 + 第一人称
    insight_total = insight_score + first_person_count * 0.5
    
    # Knowledge 得分：关键词 + 来源信息
    knowledge_total = knowledge_score + source_count * 1.0
    
    # 5. 判断分类
    if insight_total > knowledge_total:
        suggested_category = "insight"
        score_diff = insight_total - knowledge_total
    else:
        suggested_category = "knowledge"
        score_diff = knowledge_total - insight_total
    
    # 6. 计算置信度（0-1）
    total_score = insight_total + knowledge_total
    if total_score == 0:
        confidence = 0.5  # 无法判断，置信度低
    else:
        # 得分差异越大，置信度越高
        confidence = min(0.95, 0.5 + (score_diff / max(total_score, 1)) * 0.45)
    
    # 7. 生成原因说明
    reasons = []
    if insight_score > 0:
        reasons.append(f"检测到 {insight_score} 个个人表达关键词")
    if first_person_count > 0:
        reasons.append(f"包含 {first_person_count} 处第一人称表达")
    if knowledge_score > 0:
        reasons.append(f"检测到 {knowledge_score} 个知识库特征关键词")
    if source_count > 0:
        reasons.append(f"包含 {source_count} 处来源信息")
    
    if not reasons:
        reasons.append("内容特征不明显")
    
    reason = "；".join(reasons)
    
    # 8. 如果置信度低，提供备选方案
    alternative = None
    if confidence < 0.8:
        alternative = "knowledge" if suggested_category == "insight" else "insight"
    
    return {
        "suggested_category": suggested_category,
        "confidence": round(confidence, 2),
        "reason": reason,
        "alternative": alternative,
        "scores": {
            "insight_score": insight_total,
            "knowledge_score": knowledge_total
        }
    }


async def memory_suggest_category(params: MemorySuggestCategoryInput) -> str:
    """智能建议分类（insight vs knowledge）。
    
    分析内容特征，自动判断应该归类为个人记忆（insight）还是知识库（knowledge）。
    使用关键词检测和内容特征分析。
    
    Args:
        params: 参数对象
            - title: 标题
            - content: 内容
    
    Returns:
        JSON格式的建议结果，包括建议分类、置信度、原因等
    """
    try:
        result = analyze_content_features(params.title, params.content)
        
        return json.dumps({
            "status": "success",
            "suggestion": result
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"分类建议失败: {str(e)}",
            "suggestion": "请检查输入参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)

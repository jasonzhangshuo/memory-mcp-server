"""Memory check conflicts tool implementation.

检测内容矛盾、过时和重复内容。
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import search_memories
from tools.memory_get import memory_get
from models import MemoryCheckConflictsInput
from utils.similarity import calculate_similarity, find_similar_pairs


def detect_contradictions(new_entry: dict, existing_entries: List[dict]) -> List[dict]:
    """检测内容矛盾。
    
    通过语义相似度 + 关键词匹配找出可能矛盾的条目。
    """
    contradictions = []
    
    new_text = f"{new_entry.get('title', '')} {new_entry.get('content', '')}"
    new_category = new_entry.get('category', '')
    
    # 只检测相同类别的条目（如 decision, goal 等）
    if new_category not in ['decision', 'goal', 'commitment', 'plan']:
        return contradictions
    
    for existing in existing_entries:
        if existing.get('id') == new_entry.get('id'):
            continue
        
        existing_category = existing.get('category', '')
        if existing_category != new_category:
            continue
        
        existing_text = f"{existing.get('title', '')} {existing.get('content', '')}"
        
        # 计算相似度
        similarity = calculate_similarity(new_text, existing_text)
        
        # 如果相似度高（>0.6）但内容有差异，可能是矛盾
        if similarity > 0.6 and similarity < 0.95:
            # 检查是否有数值或状态的改变
            # 简单检测：如果标题相似但内容有数值差异，可能是矛盾
            title_similarity = calculate_similarity(
                new_entry.get('title', ''),
                existing.get('title', '')
            )
            
            if title_similarity > 0.7:
                contradictions.append({
                    "type": "contradict",
                    "severity": "medium",
                    "current_entry": new_entry,
                    "related_entry": existing,
                    "similarity": round(similarity, 2),
                    "suggestion": f"发现可能矛盾：新条目与 {existing.get('title', '')} 相似但内容有差异，是否更新旧条目？"
                })
    
    return contradictions


def detect_outdated(entries: List[dict]) -> List[dict]:
    """检测过时内容。
    
    检测目标、计划等是否已过期。
    """
    outdated = []
    now = datetime.now()
    
    for entry in entries:
        category = entry.get('category', '')
        created_at = entry.get('created_at', '')
        
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if created_date.tzinfo:
                created_date = created_date.replace(tzinfo=None)
        except:
            continue
        
        # 检测目标（goal）是否已过期
        if category == 'goal':
            # 检查目标中是否包含时间信息
            content = entry.get('content', '')
            title = entry.get('title', '')
            
            # 简单检测：如果标题或内容包含"50岁"、"2026年"等时间信息
            # 这里简化处理，实际可以更智能地解析时间
            age_mentioned = any(keyword in title or keyword in content 
                               for keyword in ['50岁', '50', '2026', '2027', '2028'])
            
            if age_mentioned:
                # 检查是否已过6个月未更新
                months_old = (now - created_date).days / 30
                if months_old > 6:
                    outdated.append({
                        "type": "outdated",
                        "severity": "high",
                        "entry": entry,
                        "age_months": round(months_old, 1),
                        "suggestion": f"目标 '{title}' 已创建 {round(months_old, 1)} 个月，是否需要更新状态？"
                    })
        
        # 检测计划（plan）是否已过期
        elif category == 'plan':
            months_old = (now - created_date).days / 30
            if months_old > 3:  # 计划3个月未更新视为可能过期
                outdated.append({
                    "type": "outdated",
                    "severity": "medium",
                    "entry": entry,
                    "age_months": round(months_old, 1),
                    "suggestion": f"计划 '{entry.get('title', '')}' 已创建 {round(months_old, 1)} 个月，是否已完成或需要更新？"
                })
    
    return outdated


def detect_duplicates(entries: List[dict], threshold: float = 0.8) -> List[dict]:
    """检测重复内容。
    
    使用相似度算法找出重复条目。
    """
    duplicates = []
    
    # 准备文本数据
    text_data = []
    for entry in entries:
        entry_id = entry.get('id', '')
        title = entry.get('title', '')
        content = entry.get('content', '')
        full_text = f"{title} {content}"
        text_data.append((entry_id, full_text, entry))
    
    # 找出相似对
    similar_pairs = find_similar_pairs(text_data, threshold=threshold)
    
    for entry1, entry2, similarity in similar_pairs:
        duplicates.append({
            "type": "duplicate",
            "severity": "medium",
            "entry1": entry1,
            "entry2": entry2,
            "similarity": round(similarity, 2),
            "suggestion": f"发现重复内容（相似度 {round(similarity, 2)}）：'{entry1.get('title', '')}' 与 '{entry2.get('title', '')}' 高度相似，是否合并？"
        })
    
    return duplicates


async def memory_check_conflicts(params: MemoryCheckConflictsInput) -> str:
    """检测冲突内容。
    
    检测内容矛盾、过时和重复内容。
    如果提供了 new_entry_id，检测新内容与现有内容的冲突。
    否则，全面扫描指定范围。
    
    Args:
        params: 参数对象
            - new_entry_id: 新条目ID（写入时检测）
            - category: 限定类别
            - project: 限定项目
            - check_type: 检测类型列表（contradict/outdated/duplicate）
    
    Returns:
        JSON格式的冲突报告
    """
    try:
        conflicts = []
        
        # 如果提供了 new_entry_id，获取新条目
        new_entry = None
        if params.new_entry_id:
            from tools.memory_get import memory_get
            from models import MemoryGetInput
            get_result_str = await memory_get(MemoryGetInput(id=params.new_entry_id))
            get_result = json.loads(get_result_str)
            if get_result.get("status") == "success":
                new_entry = get_result.get("entry")
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"未找到ID为 {params.new_entry_id} 的条目"
                }, ensure_ascii=False, indent=2)
        
        # 检索相关条目
        if new_entry:
            # 检测新条目与现有条目的冲突
            # 搜索相似主题的条目
            query = new_entry.get('title', '')[:20]  # 使用标题前20字作为搜索词
            existing_entries = await search_memories(
                query=query,
                category=params.category or new_entry.get('category'),
                project=params.project or new_entry.get('project'),
                tags=None,
                limit=50
            )
            
            # 检测矛盾
            if 'contradict' in (params.check_type or ['contradict', 'outdated', 'duplicate']):
                contradictions = detect_contradictions(new_entry, existing_entries)
                conflicts.extend(contradictions)
        else:
            # 全面扫描
            existing_entries = await search_memories(
                query="",
                category=params.category,
                project=params.project,
                tags=None,
                limit=1000
            )
        
        # 检测过时内容
        if 'outdated' in (params.check_type or ['contradict', 'outdated', 'duplicate']):
            outdated_list = detect_outdated(existing_entries)
            conflicts.extend(outdated_list)
        
        # 检测重复内容
        if 'duplicate' in (params.check_type or ['contradict', 'outdated', 'duplicate']):
            duplicates = detect_duplicates(existing_entries, threshold=0.8)
            conflicts.extend(duplicates)
        
        return json.dumps({
            "status": "success",
            "count": len(conflicts),
            "conflicts": conflicts
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"冲突检测失败: {str(e)}",
            "suggestion": "请检查参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)

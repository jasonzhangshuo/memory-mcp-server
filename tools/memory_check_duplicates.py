"""Memory check duplicates tool implementation.

检测重复内容。
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import search_memories
from models import MemoryCheckDuplicatesInput
from utils.similarity import find_similar_pairs


async def memory_check_duplicates(params: MemoryCheckDuplicatesInput) -> str:
    """检测重复内容。
    
    使用文本相似度算法找出重复条目。
    
    Args:
        params: 参数对象
            - category: 限定类别（可选）
            - project: 限定项目（可选）
            - similarity_threshold: 相似度阈值（0-1），默认0.8
    
    Returns:
        JSON格式的重复内容报告
    """
    try:
        # 检索相关条目
        entries = await search_memories(
            query="",
            category=params.category,
            project=params.project,
            tags=None,
            limit=1000
        )
        
        if len(entries) < 2:
            return json.dumps({
                "status": "success",
                "count": 0,
                "message": "条目数量不足，无法检测重复",
                "duplicates": []
            }, ensure_ascii=False, indent=2)
        
        # 准备文本数据
        text_data = []
        for entry in entries:
            entry_id = entry.get('id', '')
            title = entry.get('title', '')
            content = entry.get('content', '')
            text_data.append((entry_id, f"{title} {content}", entry))
        
        # 找出相似对
        similar_pairs = find_similar_pairs(text_data, threshold=params.similarity_threshold or 0.8)
        
        # 格式化结果
        duplicates = []
        for entry1, entry2, similarity in similar_pairs:
            duplicates.append({
                "entry1": {
                    "id": entry1.get('id'),
                    "title": entry1.get('title'),
                    "category": entry1.get('category'),
                    "created_at": entry1.get('created_at')
                },
                "entry2": {
                    "id": entry2.get('id'),
                    "title": entry2.get('title'),
                    "category": entry2.get('category'),
                    "created_at": entry2.get('created_at')
                },
                "similarity": round(similarity, 2),
                "suggestion": f"发现重复内容（相似度 {round(similarity, 2)}）：'{entry1.get('title', '')}' 与 '{entry2.get('title', '')}' 高度相似，是否合并？"
            })
        
        return json.dumps({
            "status": "success",
            "count": len(duplicates),
            "duplicates": duplicates
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"重复检测失败: {str(e)}",
            "suggestion": "请检查参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)

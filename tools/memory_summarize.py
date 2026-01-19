"""Memory summarize tool implementation."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import search_memories, list_tags, add_memory
from models import MemorySummarizeInput


async def memory_summarize(params: MemorySummarizeInput) -> str:
    """生成阶段性总结。
    
    按日期范围/项目/标签检索记忆，统计高频主题和标签，提取关键洞察，
    生成结构化总结文本。可选保存为digest类别条目。
    
    Args:
        params: 参数对象
            - start_date: 开始日期 YYYY-MM-DD（可选）
            - end_date: 结束日期 YYYY-MM-DD（可选）
            - project: 限定项目（可选）
            - tags: 限定标签（可选）
            - save_as_digest: 是否保存为digest条目（默认False）
    
    Returns:
        JSON格式的总结内容，包括高频主题、关键洞察等
    """
    try:
        # Build search query
        query = ""
        if params.start_date or params.end_date:
            # Date-based search: search by date range in content or use created_at filter
            # For simplicity, we'll search all and filter by date in Python
            query = ""
        
        # Search memories
        all_results = await search_memories(
            query=query,
            category=None,
            project=params.project,
            tags=params.tags,
            limit=1000  # Get more results for summary
        )
        
        # Filter by date if specified
        filtered_results = []
        for result in all_results:
            created_at = result.get("created_at", "")
            if params.start_date and created_at < params.start_date:
                continue
            if params.end_date and created_at > params.end_date:
                continue
            filtered_results.append(result)
        
        if not filtered_results:
            return json.dumps({
                "status": "success",
                "message": "指定条件下没有找到相关记录",
                "summary": {
                    "period": f"{params.start_date or '开始'} ~ {params.end_date or '结束'}",
                    "total_count": 0,
                    "high_frequency_topics": [],
                    "key_insights": [],
                    "tags_summary": []
                }
            }, ensure_ascii=False, indent=2)
        
        # Analyze results
        # 1. Count categories
        category_counts = {}
        for result in filtered_results:
            cat = result.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # 2. Extract tags and count
        tag_counts = {}
        for result in filtered_results:
            tags = result.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 3. Extract key insights (from insight/decision/goal categories)
        key_insights = []
        for result in filtered_results:
            cat = result.get("category", "")
            if cat in ["insight", "decision", "goal"]:
                title = result.get("title", "")
                if title:
                    key_insights.append({
                        "category": cat,
                        "title": title,
                        "created_at": result.get("created_at", "")
                    })
        
        # 4. Get high frequency topics (top categories and tags)
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Build summary text
        period_str = ""
        if params.start_date or params.end_date:
            period_str = f"{params.start_date or '开始'} ~ {params.end_date or '结束'}"
        else:
            period_str = "全部时间"
        
        summary_text = f"""## 总结周期
{period_str}

## 本期重点
- 共 {len(filtered_results)} 条记录
- 主要类别：{', '.join([f"{cat}({count}次)" for cat, count in sorted_categories[:3]])}

## 高频主题
"""
        for tag, count in sorted_tags[:5]:
            summary_text += f"- {tag}（出现{count}次）\n"
        
        summary_text += "\n## 关键洞察\n"
        for insight in key_insights[:5]:
            summary_text += f"- [{insight['category']}] {insight['title']}\n"
        
        summary_text += "\n## 待深入方向\n"
        summary_text += "- 根据高频主题和关键洞察，确定下一步学习重点\n"
        
        summary_result = {
            "status": "success",
            "summary": {
                "period": period_str,
                "total_count": len(filtered_results),
                "category_counts": dict(sorted_categories),
                "high_frequency_topics": [{"name": tag, "count": count} for tag, count in sorted_tags],
                "key_insights": key_insights[:10],
                "tags_summary": [{"name": tag, "count": count} for tag, count in sorted_tags]
            },
            "summary_text": summary_text
        }
        
        # Save as digest if requested
        if params.save_as_digest:
            import uuid
            digest_title = f"{period_str} 总结"
            if params.project:
                digest_title = f"{params.project} - {digest_title}"
            
            memory_id = str(uuid.uuid4())
            digest_entry = await add_memory(
                memory_id=memory_id,
                category="digest",
                title=digest_title,
                content=summary_text,
                project=params.project or "digest",
                importance=4,
                source_type="claude_ai",
                tags=["总结", "复盘"] + (params.tags or [])
            )
            
            summary_result["digest_saved"] = True
            summary_result["digest_result"] = {
                "id": memory_id,
                "entry": digest_entry
            }
        else:
            summary_result["digest_saved"] = False
        
        return json.dumps(summary_result, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"生成总结失败: {str(e)}",
            "suggestion": "请检查参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)

"""Memory compress conversation tool implementation."""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import add_memory
from models import MemoryCompressConversationInput
from sync.sync_to_feishu import auto_sync_memory_to_feishu


async def memory_compress_conversation(params: MemoryCompressConversationInput) -> str:
    """压缩保存对话。
    
    将对话内容压缩为摘要，并提取关键决定、洞察和行动项。
    保存为 conversation 类别的记忆条目。
    
    Phase 2 策略：在冷启动阶段（前2周），偏向多记录，确保不遗漏重要信息。
    尽量提取所有关键决定、洞察和行动项，宁可多记录也不要遗漏。
    """
    try:
        # 构建内容
        content_parts = [params.summary]
        
        if params.key_decisions:
            content_parts.append("\n\n关键决定:")
            for i, decision in enumerate(params.key_decisions, 1):
                content_parts.append(f"{i}. {decision}")
        
        if params.key_insights:
            content_parts.append("\n\n关键洞察:")
            for i, insight in enumerate(params.key_insights, 1):
                content_parts.append(f"{i}. {insight}")
        
        if params.action_items:
            content_parts.append("\n\n行动项:")
            for i, item in enumerate(params.action_items, 1):
                content_parts.append(f"{i}. {item}")
        
        content = "\n".join(content_parts)
        
        # 生成标题（从摘要中提取前30字）
        title = params.summary[:30] + ("..." if len(params.summary) > 30 else "")
        
        # 保存记忆
        memory_id = str(uuid.uuid4())
        entry = await add_memory(
            memory_id=memory_id,
            category="conversation",
            title=title,
            content=content,
            project=params.project,
            importance=3,
            source_type="claude_ai"
        )
        
        # 自动同步到飞书（静默模式，失败不影响保存）
        await auto_sync_memory_to_feishu(entry, silent=True)
        
        return json.dumps({
            "status": "success",
            "message": "对话已压缩保存",
            "id": memory_id,
            "entry": entry
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"保存失败: {str(e)}",
            "suggestion": "请检查输入参数是否正确，或稍后重试"
        }, ensure_ascii=False, indent=2)

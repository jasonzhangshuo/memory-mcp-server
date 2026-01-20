"""Feishu archive to memory tool implementation."""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import FeishuArchiveToMemoryInput
from storage.db import add_memory


async def feishu_archive_to_memory(params: FeishuArchiveToMemoryInput) -> str:
    """将分析后的飞书消息归档到记忆系统。
    
    先调用 add_memory 写入永久记忆库，再标记消息为已归档。
    
    Args:
        params: 输入参数
            - message_id: 飞书消息 ID
            - analyzed_title: AI 分析后的标题
            - analyzed_content: AI 分析后的内容
            - category: 记忆类别，默认 conversation
            - tags: 标签列表
            - importance: 重要性 1-5，默认3
            - project: 所属项目
    
    Returns:
        JSON 格式的归档结果
    """
    try:
        # 1) Add to memory system
        memory_id = f"feishu_{params.message_id}_{uuid.uuid4().hex[:8]}"
        
        memory_entry = await add_memory(
            memory_id=memory_id,
            category=params.category or "conversation",
            title=params.analyzed_title,
            content=params.analyzed_content,
            project=params.project,
            importance=params.importance or 3,
            source_type="feishu_im",
            tags=params.tags or []
        )
        
        # 2) Mark message as archived in temp inbox
        base_url = os.getenv("FEISHU_WEBHOOK_BASE_URL", "https://webhook.jason2026.top")
        token = os.getenv("FEISHU_WEBHOOK_READ_TOKEN", "")
        
        if token:
            try:
                url = f"{base_url}/feishu/temp_inbox/{params.message_id}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.patch(
                        url,
                        params={"token": token},
                        json={"archived": True}
                    )
                    response.raise_for_status()
            except Exception as e:
                # Non-critical: memory already saved, just log the error
                print(f"⚠️  标记归档失败（已写入记忆）: {e}")
        
        return json.dumps({
            "status": "success",
            "memory_id": memory_id,
            "message": "已归档到记忆系统",
            "details": {
                "title": params.analyzed_title,
                "category": params.category or "conversation",
                "importance": params.importance or 3,
                "tags": params.tags or []
            }
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"归档失败: {str(e)}",
            "suggestion": "请检查记忆系统是否正常"
        }, ensure_ascii=False, indent=2)

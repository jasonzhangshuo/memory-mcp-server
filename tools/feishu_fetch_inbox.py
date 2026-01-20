"""Feishu fetch inbox tool implementation."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import FeishuFetchInboxInput


async def feishu_fetch_inbox(params: FeishuFetchInboxInput) -> str:
    """拉取飞书临时收件箱消息。
    
    从服务器临时收件箱拉取未归档的飞书消息，供 AI 分析决策。
    
    Args:
        params: 输入参数
            - limit: 返回数量，默认10
            - include_archived: 是否包含已归档，默认False
    
    Returns:
        JSON 格式的消息列表
    """
    try:
        # Get webhook server URL and token from env
        base_url = os.getenv("FEISHU_WEBHOOK_BASE_URL", "https://webhook.jason2026.top")
        token = os.getenv("FEISHU_WEBHOOK_READ_TOKEN", "")
        
        if not token:
            return json.dumps({
                "status": "error",
                "message": "缺少 FEISHU_WEBHOOK_READ_TOKEN 环境变量",
                "suggestion": "请在 .env 文件中设置 FEISHU_WEBHOOK_READ_TOKEN"
            }, ensure_ascii=False, indent=2)
        
        # Build request URL
        url = f"{base_url}/feishu/temp_inbox"
        params_dict = {
            "limit": params.limit or 10,
            "include_archived": str(params.include_archived or False).lower(),
            "token": token
        }
        
        # Make HTTP request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params_dict)
            response.raise_for_status()
            data = response.json()
        
        if not data.get("ok"):
            return json.dumps({
                "status": "error",
                "message": "服务器返回错误",
                "data": data
            }, ensure_ascii=False, indent=2)
        
        items = data.get("items", [])
        
        if not items:
            return json.dumps({
                "status": "success",
                "count": 0,
                "message": "暂无新消息",
                "items": []
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success",
            "count": len(items),
            "items": items
        }, ensure_ascii=False, indent=2)
    
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "status": "error",
            "message": f"HTTP 错误: {e.response.status_code}",
            "suggestion": "请检查服务器状态和 token 是否正确"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"拉取失败: {str(e)}",
            "suggestion": "请检查网络连接和服务器状态"
        }, ensure_ascii=False, indent=2)

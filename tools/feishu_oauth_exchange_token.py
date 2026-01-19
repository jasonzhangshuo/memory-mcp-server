"""飞书 OAuth 授权码换取 token 工具"""

import json
from sync.feishu_client import FeishuClient
from models import FeishuOAuthExchangeTokenInput


async def feishu_oauth_exchange_token(params: FeishuOAuthExchangeTokenInput) -> str:
    """使用 OAuth 授权码换取 user_access_token
    
    Args:
        params: 参数对象
            - code: OAuth 授权码（从授权回调 URL 中获取）
    
    Returns:
        user_access_token 信息
    """
    client = FeishuClient()
    
    try:
        token_data = await client.exchange_user_access_token(params.code)
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 7200)
        
        return json.dumps({
            "status": "success",
            "message": "成功获取 user_access_token！",
            "token_info": {
                "access_token_preview": f"{access_token[:20]}..." if access_token else None,
                "refresh_token_preview": f"{refresh_token[:20]}..." if refresh_token else None,
                "expires_in": expires_in,
                "expires_in_hours": expires_in // 3600
            },
            "note": "Token 已保存到客户端，现在可以使用用户身份访问你的文档库了！",
            "next_steps": [
                "user_access_token 会自动刷新（当过期时）",
                "如果 refresh_token 也过期，需要重新授权",
                "使用 feishu_list_documents 工具时，设置 use_user_token=True 可以使用用户身份"
            ]
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"换取 token 失败: {str(e)}",
            "suggestions": [
                "检查 code 是否正确且未过期",
                "确认 redirect_uri 是否与授权时一致",
                "确认应用权限是否已开通"
            ]
        }, ensure_ascii=False, indent=2)

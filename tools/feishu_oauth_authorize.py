"""飞书 OAuth 授权工具"""

import json
from sync.feishu_client import FeishuClient
from models import FeishuOAuthAuthorizeInput


async def feishu_oauth_authorize(params: FeishuOAuthAuthorizeInput) -> str:
    """生成飞书 OAuth 授权链接
    
    用户需要：
    1. 访问返回的授权链接
    2. 完成授权后，从回调 URL 中获取 code 参数
    3. 使用 feishu_oauth_exchange_token 工具将 code 换取 user_access_token
    
    Args:
        params: 参数对象
            - redirect_uri: 授权后的回调地址（需要在飞书开放平台配置）
            - state: 可选的状态参数，用于防止 CSRF 攻击
    
    Returns:
        授权链接 URL 和使用说明
    """
    client = FeishuClient()
    auth_url = client.get_oauth_authorize_url(
        redirect_uri=params.redirect_uri,
        state=params.state
    )
    
    return json.dumps({
        "status": "success",
        "authorize_url": auth_url,
        "instructions": {
            "step1": "在浏览器中打开上面的授权链接",
            "step2": "登录飞书账号并完成授权",
            "step3": "授权完成后，飞书会重定向到你配置的 redirect_uri",
            "step4": "从重定向 URL 中提取 code 参数（格式：?code=xxxxx）",
            "step5": "使用 feishu_oauth_exchange_token 工具，将 code 换取 user_access_token"
        },
        "note": "redirect_uri 必须在飞书开放平台的应用设置中配置"
    }, ensure_ascii=False, indent=2)

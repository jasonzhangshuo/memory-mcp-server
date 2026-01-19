"""列出飞书群聊"""

import json
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuListChatsInput


async def feishu_list_chats(params: FeishuListChatsInput) -> str:
    """列出当前应用可见的群聊列表。

    Args:
        params: 参数对象
            - page_size: 每页数量
            - page_token: 分页 token（可选）
            - use_user_token: 是否使用用户身份 token

    Returns:
        JSON 格式的群聊列表
    """
    try:
        client = FeishuClient()
        result = await client.list_chats(
            page_size=params.page_size,
            page_token=params.page_token,
            use_user_token=bool(params.use_user_token),
        )
        return json.dumps({
            "status": "success",
            "message": "群聊列表获取成功",
            "data": result,
        }, ensure_ascii=False, indent=2)

    except FeishuAPIError as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. IM 权限是否已开通 2. 应用是否已加入群"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"获取群聊列表失败: {str(e)}",
            "suggestion": "请检查：1. 网络连接 2. 参数是否合法"
        }, ensure_ascii=False, indent=2)

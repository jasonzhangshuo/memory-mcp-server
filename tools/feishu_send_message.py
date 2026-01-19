"""发送飞书消息（IM）"""

import json
from sync.feishu_client import FeishuClient, FeishuAPIError
from models import FeishuSendMessageInput


async def feishu_send_message(params: FeishuSendMessageInput) -> str:
    """发送飞书 IM 消息。

    Args:
        params: 参数对象
            - receive_id_type: chat_id/open_id/user_id/email
            - receive_id: 对应接收者 ID
            - msg_type: 消息类型（默认 text）
            - content: 消息内容（text 传纯文本；其他类型传 JSON 字符串）
            - use_user_token: 是否使用用户身份 token

    Returns:
        JSON 格式的发送结果
    """
    try:
        client = FeishuClient()

        receive_id_type = params.receive_id_type
        receive_id = params.receive_id
        msg_type = params.msg_type or "text"

        allowed_receive_id_types = {"chat_id", "open_id", "user_id", "email"}
        if receive_id_type not in allowed_receive_id_types:
            raise ValueError(f"receive_id_type 不合法: {receive_id_type}")

        # 处理 content
        if msg_type == "text":
            content_payload = {"text": params.content}
        else:
            try:
                content_payload = json.loads(params.content)
            except json.JSONDecodeError:
                raise ValueError("非 text 类型的 content 必须是 JSON 字符串")

        result = await client.send_message(
            receive_id_type=receive_id_type,
            receive_id=receive_id,
            msg_type=msg_type,
            content=content_payload,
            use_user_token=bool(params.use_user_token),
        )

        return json.dumps({
            "status": "success",
            "message": "消息已发送",
            "data": result,
        }, ensure_ascii=False, indent=2)

    except FeishuAPIError as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "error_code": e.error_code,
            "status_code": e.status_code,
            "suggestion": e.suggestion or "请检查：1. IM 权限是否已开通 2. 接收者 ID 是否正确 3. 机器人是否已加入群/是否被用户启用"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"发送消息失败: {str(e)}",
            "suggestion": "请检查：1. receive_id_type/receive_id 是否正确 2. 消息内容格式是否正确 3. 网络是否正常"
        }, ensure_ascii=False, indent=2)

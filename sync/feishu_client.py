"""飞书多维表格 API 客户端"""

import os
import httpx
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 飞书 API 配置
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID")
FEISHU_DEFAULT_FOLDER_TOKEN = os.getenv("FEISHU_DEFAULT_FOLDER_TOKEN")  # 默认文件夹 token（None 表示使用应用身份创建在根目录）

# Token 文件路径
USER_TOKEN_FILE = Path(__file__).parent.parent / ".user_token.json"


class FeishuAPIError(Exception):
    """飞书 API 调用异常"""
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 error_code: Optional[str] = None, error_data: Optional[Dict] = None,
                 suggestion: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.error_data = error_data
        self.suggestion = suggestion


def _handle_api_error(e: Exception, endpoint: str = "") -> FeishuAPIError:
    """统一的 API 错误处理函数
    
    Args:
        e: 原始异常
        endpoint: API 端点（用于错误消息）
    
    Returns:
        FeishuAPIError: 格式化的错误异常
    """
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        error_code = "N/A"
        error_msg = f"HTTP {status_code}"
        error_data = {}
        suggestion = ""
        
        # 尝试解析错误响应
        try:
            result = e.response.json()
            error_code = result.get("code", "N/A")
            error_msg = result.get("msg", error_msg)
            error_data = result.get("data", {})
        except:
            error_msg = e.response.text[:200] if e.response.text else error_msg
        
        # 根据状态码提供具体建议
        if status_code == 400:
            suggestion = "请检查：1. 请求参数是否正确 2. API 端点是否正确 3. 数据格式是否符合要求"
        elif status_code == 401:
            suggestion = "请检查：1. App ID 或 App Secret 是否正确 2. Token 是否已过期 3. 是否需要重新获取 token"
        elif status_code == 403:
            suggestion = "请检查：1. 应用权限是否已申请并开通（应用身份权限）2. 应用是否已发布 3. 是否有访问该资源的权限"
        elif status_code == 404:
            suggestion = "请检查：1. API 端点是否正确 2. 资源 ID 是否存在 3. 权限是否已开通（如文档权限 drive:drive）"
        elif status_code == 429:
            suggestion = "请求频率过高，请稍后重试"
        elif status_code >= 500:
            suggestion = "飞书服务器错误，请稍后重试或联系飞书技术支持"
        else:
            suggestion = "请检查网络连接和 API 配置"
        
        return FeishuAPIError(
            message=f"API 调用失败 ({endpoint}): {error_msg}",
            status_code=status_code,
            error_code=str(error_code),
            error_data=error_data,
            suggestion=suggestion
        )
    
    elif isinstance(e, httpx.TimeoutException):
        return FeishuAPIError(
            message=f"请求超时 ({endpoint})",
            suggestion="请检查网络连接，或稍后重试"
        )
    
    elif isinstance(e, httpx.ConnectError):
        return FeishuAPIError(
            message=f"连接失败 ({endpoint})",
            suggestion="请检查网络连接和飞书 API 服务状态"
        )
    
    else:
        return FeishuAPIError(
            message=f"未预期的错误 ({endpoint}): {str(e)}",
            suggestion="请检查错误日志或联系技术支持"
        )


class FeishuClient:
    """飞书多维表格 API 客户端"""
    
    def __init__(self):
        self.app_id = FEISHU_APP_ID
        self.app_secret = FEISHU_APP_SECRET
        self.app_token = FEISHU_APP_TOKEN
        self.table_id = FEISHU_TABLE_ID
        self.default_folder_token = FEISHU_DEFAULT_FOLDER_TOKEN  # 默认文件夹 token
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        # 用户身份 token
        self.user_access_token: Optional[str] = None
        self.user_token_expires_at: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        
        if not all([self.app_id, self.app_secret, self.app_token]):
            raise ValueError("缺少必要的飞书配置，请检查 .env 文件")
        
        # 尝试从文件加载用户 token
        self._load_user_token()
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """获取访问令牌"""
        # 如果 token 未过期且不强制刷新，直接返回
        if not force_refresh and self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # 获取新 token
        url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取 token 失败: {data.get('msg')}")
            
            self.access_token = data["tenant_access_token"]
            # token 有效期通常是 2 小时，这里设置 1.5 小时后过期
            from datetime import timedelta
            self.token_expires_at = datetime.now() + timedelta(hours=1, minutes=30)
            
            return self.access_token
    
    def _load_user_token(self):
        """从文件加载用户身份 token"""
        if USER_TOKEN_FILE.exists():
            try:
                with open(USER_TOKEN_FILE, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)

                self.user_access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")

                # 计算过期时间
                from datetime import timedelta
                # 检查是否有保存的创建时间
                saved_at = token_data.get("saved_at")
                expires_in = token_data.get("expires_in", 7200)

                if saved_at:
                    # 如果有保存时间，根据保存时间计算过期时间
                    saved_time = datetime.fromisoformat(saved_at)
                    self.user_token_expires_at = saved_time + timedelta(seconds=expires_in)

                    # 检查是否已过期
                    if datetime.now() >= self.user_token_expires_at:
                        print(f"⚠️  用户 token 已过期，将在首次使用时自动刷新")
                        self.user_access_token = None  # 标记为需要刷新
                    else:
                        remaining = (self.user_token_expires_at - datetime.now()).total_seconds()
                        print(f"✅ 已从文件加载用户身份 token（剩余 {int(remaining/60)} 分钟）")
                else:
                    # 如果没有保存时间，假设是刚保存的（向后兼容）
                    self.user_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                    print(f"✅ 已从文件加载用户身份 token（假设为最新）")

            except Exception as e:
                print(f"⚠️  加载用户 token 失败: {e}")
    
    def _save_user_token(self, token_data: Dict[str, Any]):
        """保存用户身份 token 到文件"""
        try:
            # 添加保存时间戳，用于准确计算过期时间
            token_data_with_timestamp = {
                **token_data,
                "saved_at": datetime.now().isoformat()
            }

            with open(USER_TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(token_data_with_timestamp, f, indent=2, ensure_ascii=False)

            expires_in = token_data.get("expires_in", 7200)
            print(f"💾 用户 token 已保存到: {USER_TOKEN_FILE}")
            print(f"   有效期: {expires_in} 秒 ({int(expires_in/60)} 分钟)")
        except Exception as e:
            print(f"⚠️  保存用户 token 失败: {e}")
    
    def get_oauth_authorize_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """生成 OAuth 授权链接
        
        Args:
            redirect_uri: 授权后的回调地址（需要在飞书开放平台配置）
            state: 可选的状态参数，用于防止 CSRF 攻击
        
        Returns:
            授权链接 URL
        """
        import urllib.parse
        
        params = {
            "app_id": self.app_id,
            "redirect_uri": redirect_uri
        }
        if state:
            params["state"] = state
        
        query_string = urllib.parse.urlencode(params)
        return f"https://open.feishu.cn/open-apis/authen/v1/index?{query_string}"
    
    async def exchange_user_access_token(self, code: str) -> Dict[str, Any]:
        """使用授权码换取 user_access_token
        
        Args:
            code: OAuth 授权码
        
        Returns:
            包含 access_token, refresh_token 等信息
        """
        url = f"{FEISHU_API_BASE}/authen/v1/access_token"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取 user_access_token 失败: {data.get('msg')}")
            
            token_data = data.get("data", {})
            self.user_access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            # 设置过期时间（通常是 7200 秒，即 2 小时）
            expires_in = token_data.get("expires_in", 7200)
            from datetime import timedelta
            self.user_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 提前 5 分钟过期
            
            # 保存到文件
            self._save_user_token(token_data)
            
            return token_data
    
    async def refresh_user_access_token(self) -> str:
        """刷新 user_access_token
        
        Returns:
            新的 user_access_token
        """
        if not self.refresh_token:
            raise Exception("没有 refresh_token，请重新授权")
        
        url = f"{FEISHU_API_BASE}/authen/v1/refresh_access_token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"刷新 user_access_token 失败: {data.get('msg')}")
            
            token_data = data.get("data", {})
            self.user_access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)  # 可能返回新的 refresh_token
            
            expires_in = token_data.get("expires_in", 7200)
            from datetime import timedelta
            self.user_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            # 保存到文件
            self._save_user_token(token_data)
            
            return self.user_access_token
    
    async def get_user_access_token(self, force_refresh: bool = False) -> str:
        """获取用户身份访问令牌

        自动处理 token 过期和刷新逻辑。

        Args:
            force_refresh: 是否强制刷新

        Returns:
            user_access_token

        Raises:
            Exception: 如果 token 过期且无法刷新
        """
        # 如果 token 未过期且不强制刷新，直接返回
        if not force_refresh and self.user_access_token and self.user_token_expires_at:
            remaining = (self.user_token_expires_at - datetime.now()).total_seconds()
            if remaining > 0:
                # Token 还有效
                if remaining < 300:  # 剩余不到5分钟，提前刷新
                    print(f"⚠️  用户 token 即将过期（剩余 {int(remaining)} 秒），提前刷新")
                    try:
                        return await self.refresh_user_access_token()
                    except Exception as e:
                        print(f"⚠️  提前刷新失败: {e}，继续使用当前 token")
                        return self.user_access_token
                else:
                    # Token 仍然有效，直接返回
                    return self.user_access_token

        # Token 已过期或不存在，尝试刷新
        if self.refresh_token:
            try:
                print(f"🔄 用户 token 已过期，使用 refresh_token 刷新...")
                return await self.refresh_user_access_token()
            except Exception as e:
                print(f"❌ 刷新 token 失败: {e}")
                # 检查是否是 refresh_token 过期
                if "expired" in str(e).lower() or "invalid" in str(e).lower():
                    raise Exception(
                        "refresh_token 已过期或无效，请重新进行 OAuth 授权。\n"
                        "使用 feishu_oauth_authorize 工具生成授权链接。"
                    )
                else:
                    raise Exception(f"刷新 token 失败: {str(e)}")

        # 没有 refresh_token
        raise Exception(
            "user_access_token 不存在或已过期，且没有 refresh_token。\n"
            "请使用 feishu_oauth_authorize 工具重新进行 OAuth 授权。"
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        use_user_token: bool = False
    ) -> Dict[str, Any]:
        """发送 API 请求
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            data: 请求体数据（用于 POST/PUT）
            params: URL 参数（用于 GET/DELETE）
            use_user_token: 是否使用用户身份 token（默认 False，使用应用身份 token）
        
        Returns:
            API 响应的 data 部分
        
        Raises:
            FeishuAPIError: API 调用失败时抛出
        """
        try:
            # 根据参数选择使用应用身份或用户身份 token
            if use_user_token:
                try:
                    token = await self.get_user_access_token()
                except Exception as e:
                    raise FeishuAPIError(
                        f"无法获取用户身份 token: {str(e)}",
                        suggestion="请先进行 OAuth 授权，获取 user_access_token"
                    )
            else:
                token = await self.get_access_token()
            
            url = f"{FEISHU_API_BASE}{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 设置超时时间
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                # 发送请求
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"不支持的 HTTP 方法: {method}")
                
                # 检查 HTTP 状态码
                response.raise_for_status()
                
                # 解析 JSON 响应
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    raise FeishuAPIError(
                        message=f"API 返回非 JSON 响应: {response.text[:500]}",
                        status_code=response.status_code,
                        suggestion="请检查 API 端点是否正确，或联系飞书技术支持"
                    )
                
                # 检查业务状态码（飞书 API 使用 code 字段表示业务状态）
                if result.get("code") != 0:
                    error_code = result.get("code", "N/A")
                    error_msg = result.get("msg", "未知错误")
                    error_data = result.get("data", {})
                    
                    # 根据错误代码提供建议
                    suggestion = ""
                    if error_code == 99991400:  # 频率限制
                        suggestion = "请求频率过高（每秒最多3次），请使用指数退避算法重试，或降低调用频率"
                    elif error_code == 1770029:  # block not support to create
                        suggestion = "请检查 block_type 是否正确（文本块应为 2）"
                    elif error_code in [99991663, 99991664]:  # 权限相关
                        suggestion = "请检查应用权限是否已申请并开通（应用身份权限）"
                    
                    raise FeishuAPIError(
                        message=f"API 调用失败: {error_msg}",
                        status_code=response.status_code,
                        error_code=str(error_code),
                        error_data=error_data,
                        suggestion=suggestion or "请检查请求参数和权限配置"
                    )
                
                return result
                
        except httpx.HTTPStatusError as e:
            raise _handle_api_error(e, endpoint)
        except httpx.TimeoutException as e:
            raise _handle_api_error(e, endpoint)
        except httpx.ConnectError as e:
            raise _handle_api_error(e, endpoint)
        except FeishuAPIError:
            # 重新抛出 FeishuAPIError
            raise
        except Exception as e:
            # 其他未预期的错误
            raise _handle_api_error(e, endpoint)

    # ==================== IM 消息（需要 im:message 权限）====================

    async def send_message(
        self,
        receive_id_type: str,
        receive_id: str,
        msg_type: str,
        content: Dict[str, Any],
        use_user_token: bool = False
    ) -> Dict[str, Any]:
        """发送 IM 消息

        Args:
            receive_id_type: chat_id/open_id/user_id/email
            receive_id: 对应接收者 ID
            msg_type: 消息类型（text / post 等）
            content: 消息内容（字典对象）
            use_user_token: 是否使用用户身份 token（默认 False）
        """
        # IM 消息接口通过 query 参数传入 receive_id_type
        endpoint = f"/im/v1/messages?receive_id_type={receive_id_type}"
        data = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content, ensure_ascii=False),
        }

        result = await self._request("POST", endpoint, data=data, use_user_token=use_user_token)
        return result.get("data", {})

    async def list_chats(
        self,
        page_size: int = 50,
        page_token: Optional[str] = None,
        use_user_token: bool = False
    ) -> Dict[str, Any]:
        """列出当前应用可见的群聊列表"""
        endpoint = "/im/v1/chats"
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        result = await self._request("GET", endpoint, params=params, use_user_token=use_user_token)
        return result.get("data", {})
    
    async def list_tables(self) -> List[Dict]:
        """列出多维表格中的所有数据表"""
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables"
        result = await self._request("GET", endpoint)
        return result.get("data", {}).get("items", [])
    
    async def get_table_fields(self, table_id: Optional[str] = None) -> List[Dict]:
        """获取数据表的字段列表"""
        table_id = table_id or self.table_id
        if not table_id:
            raise ValueError("需要指定 table_id")
        
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields"
        result = await self._request("GET", endpoint)
        return result.get("data", {}).get("items", [])
    
    async def create_record(
        self,
        fields: Dict[str, Any],
        table_id: Optional[str] = None,
        use_field_id: bool = False
    ) -> Dict[str, Any]:
        """创建记录
        
        Args:
            fields: 字段数据（字段名称或字段ID作为key）
            table_id: 数据表ID
            use_field_id: 是否使用字段ID（默认False，使用字段名称）
        """
        table_id = table_id or self.table_id
        if not table_id:
            raise ValueError("需要指定 table_id")
        
        # 如果使用字段ID，需要先获取字段映射
        if use_field_id:
            field_list = await self.get_table_fields(table_id)
            field_name_to_id = {f.get("field_name"): f.get("field_id") for f in field_list}
            # 转换字段名称到字段ID
            fields_by_id = {}
            for name, value in fields.items():
                field_id = field_name_to_id.get(name)
                if field_id:
                    fields_by_id[field_id] = value
            fields = fields_by_id
        
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        data = {"fields": fields}
        
        result = await self._request("POST", endpoint, data=data)
        return result.get("data", {}).get("record", {})
    
    async def update_record(
        self,
        record_id: str,
        fields: Dict[str, Any],
        table_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新记录"""
        table_id = table_id or self.table_id
        if not table_id:
            raise ValueError("需要指定 table_id")
        
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
        data = {"fields": fields}
        result = await self._request("PUT", endpoint, data=data)
        return result.get("data", {}).get("record", {})
    
    async def delete_record(
        self,
        record_id: str,
        table_id: Optional[str] = None
    ) -> bool:
        """删除记录"""
        table_id = table_id or self.table_id
        if not table_id:
            raise ValueError("需要指定 table_id")
        
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
        await self._request("DELETE", endpoint)
        return True
    
    async def list_records(
        self,
        table_id: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出记录"""
        table_id = table_id or self.table_id
        if not table_id:
            raise ValueError("需要指定 table_id")
        
        endpoint = f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        
        result = await self._request("GET", endpoint, params=params)
        return result.get("data", {})
    
    # ==================== 文档操作（需要 drive:drive 权限）====================
    
    async def create_document(
        self,
        title: str,
        content: str,
        folder_token: Optional[str] = None,
        use_user_token: bool = False
    ) -> Dict[str, Any]:
        """创建飞书文档

        使用 drive API 创建文档，确保文档可访问。

        Args:
            title: 文档标题
            content: 文档内容（Markdown 格式）
            folder_token: 文件夹 token（可选，如果不指定则使用默认文件夹或根目录）
            use_user_token: 是否使用用户身份 token（访问用户云盘需要设置为 True）

        Returns:
            创建的文档信息，包含 file_token

        Raises:
            FeishuAPIError: 如果文档创建失败
        """
        # 使用 docx API 创建文档（需要 docx:document 权限）
        endpoint = "/docx/v1/documents"
        data = {
            "title": title,
        }

        # 确定使用哪个文件夹 token
        target_folder_token = folder_token or self.default_folder_token

        # 如果指定了文件夹，添加到请求中
        if target_folder_token:
            data["folder_token"] = target_folder_token
            print(f"📁 目标文件夹 token: {target_folder_token}")
            print(f"🔑 使用{'用户身份' if use_user_token else '应用身份'} token")
        else:
            print("⚠️  未指定文件夹 token，文档将创建在默认位置")

        try:
            result = await self._request("POST", endpoint, data=data, use_user_token=use_user_token)
            # 调试：打印完整响应
            import json as json_module
            print(f"🔍 创建文档API完整响应: {json_module.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查响应中是否包含文件夹信息
            document_data = result.get("data", {}).get("document", {})
            if document_data:
                print(f"✅ 文档创建成功，document_id: {document_data.get('document_id')}")
                if target_folder_token:
                    print(f"📁 文档应该创建在文件夹: {target_folder_token}")
            
            # 检查响应中的错误码
            if result.get("code") != 0:
                error_code = result.get("code")
                error_msg = result.get("msg", "未知错误")
                raise FeishuAPIError(
                    message=f"文档创建失败：{error_msg} (错误码: {error_code})",
                    status_code=500,
                    error_code=str(error_code),
                    suggestion=f"请检查：1. 错误码 {error_code} 的含义 2. 文档权限是否已开通 3. 应用是否已发布"
                )
        except FeishuAPIError as e:
            # 如果是频率限制错误，提供明确的提示
            if e.error_code == "99991400":
                raise FeishuAPIError(
                    message=f"文档创建失败：请求频率过高（{e.message}）",
                    status_code=e.status_code,
                    error_code=e.error_code,
                    suggestion="请等待几秒钟后重试，或降低API调用频率（每秒最多3次）"
                )
            # 如果是权限错误，提供更明确的提示
            elif e.status_code == 403 or (e.error_code and "999916" in str(e.error_code)):
                raise FeishuAPIError(
                    message=f"文档创建失败：权限不足（{str(e)}）",
                    status_code=e.status_code,
                    error_code=e.error_code,
                    suggestion="请检查：1. 文档权限（创建及编辑新版文档 或 创建新版文档）是否已开通（应用身份权限）2. 应用是否已发布 3. 申请权限链接：https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=docx:document&op_from=openapi&token_type=tenant"
                )
            else:
                raise
        
        # 检查完整的响应结构
        import json as json_module
        print(f"🔍 响应结构检查:")
        print(f"   - result keys: {list(result.keys())}")
        print(f"   - result['data']: {result.get('data', {})}")
        print(f"   - result['data']['document']: {result.get('data', {}).get('document', {})}")
        
        document_id = result.get("data", {}).get("document", {}).get("document_id")
        
        # 验证 document_id 是否存在
        if not document_id:
            # 打印完整响应以便调试
            print(f"❌ 未找到 document_id，完整响应: {json_module.dumps(result, indent=2, ensure_ascii=False)}")
            raise FeishuAPIError(
                message="文档创建失败：未返回 document_id",
                status_code=500,
                error_code="NO_DOCUMENT_ID",
                suggestion=f"请检查：1. 文档权限（docx:document）是否已开通 2. API 调用是否成功 3. 应用是否已发布 4. 完整响应: {json_module.dumps(result, indent=2, ensure_ascii=False)}"
            )
        
        print(f"✅ 获取到 document_id: {document_id}")
        
        # 验证文档是否真的创建成功（使用 docx API 获取文档信息）
        print(f"🔍 开始验证文档是否存在: {document_id}")
        try:
            verify_endpoint = f"/docx/v1/documents/{document_id}"
            verify_result = await self._request("GET", verify_endpoint)
            verified_doc = verify_result.get("data", {}).get("document", {})
            print(f"🔍 验证响应: {json_module.dumps(verify_result, indent=2, ensure_ascii=False)}")
            if not verified_doc:
                print(f"❌ 验证失败：文档数据为空")
                raise FeishuAPIError(
                    message="文档创建失败：无法验证文档是否存在",
                    status_code=500,
                    error_code="DOCUMENT_VERIFY_FAILED",
                    suggestion="请检查：1. 文档权限（docx:document）是否已开通 2. 应用是否已发布 3. 网络连接是否正常 4. 完整验证响应: " + json_module.dumps(verify_result, indent=2, ensure_ascii=False)
                )
            print(f"✅ 文档验证成功: {verified_doc.get('title', 'N/A')}")
        except FeishuAPIError as e:
            print(f"❌ 验证失败: {str(e)} (status: {e.status_code}, error_code: {e.error_code})")
            # 如果验证失败，抛出更详细的错误
            if e.status_code == 404:
                raise FeishuAPIError(
                    message=f"文档创建失败：文档不存在（404）。document_id: {document_id}。错误: {str(e)}",
                    status_code=404,
                    error_code=e.error_code,
                    suggestion="请检查：1. 文档权限（docx:document）是否已开通 2. 应用是否已发布 3. 可能需要等待几秒钟后重试 4. document_id 是否正确 5. 文档可能创建在了应用无法访问的位置"
                )
            else:
                raise
        
        # 设置文档权限：使组织内获得链接的人可编辑（这样用户才能在浏览器中访问）
        # 注意：应用创建的文档默认只有应用可以访问，需要设置权限才能让用户在浏览器中访问
        try:
            # 使用 drive API 设置文档权限
            # 注意：docx API 创建的文档，document_id 可以直接用作 file_token
            permission_endpoint = f"/drive/v1/permissions/{document_id}/public"
            permission_data = {
                "link_share_entity": "tenant_editable"  # 组织内获得链接的人可编辑
            }
            try:
                await self._request("PATCH", permission_endpoint, data=permission_data)
                print(f"✅ 已设置文档权限：组织内获得链接的人可编辑")
            except FeishuAPIError as e:
                # 如果设置权限失败，记录警告但不阻止文档创建
                print(f"⚠️  警告：无法设置文档权限: {str(e)} (status: {e.status_code}, error_code: {e.error_code})")
                print(f"   提示：文档已创建，但可能无法在浏览器中访问。可能需要手动设置权限或添加协作者")
        except Exception as e:
            # 如果设置权限失败，记录警告但不阻止文档创建
            print(f"⚠️  警告：设置文档权限时出错: {e}")
        
        # 更新文档内容
        # 注意：根据API文档，创建文档接口不支持带内容创建，需要先创建空文档，再更新内容
        if content:
            try:
                content_success = await self.update_document_content(document_id, content, use_user_token=use_user_token)
                if not content_success:
                    # 内容更新失败，但文档已创建
                    raise FeishuAPIError(
                        message=f"文档已创建，但内容更新失败",
                        status_code=500,
                        error_code="CONTENT_UPDATE_FAILED",
                        suggestion="请检查：1. 是否具有'创建及编辑新版文档'权限（不仅仅是'创建新版文档'）2. 文档权限是否已开通 3. 应用是否已发布"
                    )
            except FeishuAPIError as e:
                # 如果是权限错误，提供更明确的提示
                if e.status_code == 403 or (e.error_code and "999916" in str(e.error_code)):
                    raise FeishuAPIError(
                        message=f"文档已创建，但内容更新失败：权限不足（{str(e)}）",
                        status_code=e.status_code,
                        error_code=e.error_code,
                        suggestion="请检查：1. 是否具有'创建及编辑新版文档'权限（应用身份权限）2. 应用是否已发布 3. 申请权限链接：https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=docx:document&op_from=openapi&token_type=tenant"
                    )
                else:
                    raise

        # 注意：使用 docx API 创建的文档，document_id 可以直接用于访问
        # 但如果文档无法访问，可能需要：
        # 1. 检查 docx:document 权限是否已开通（应用身份权限）
        # 2. 确保应用已发布
        # 3. 文档创建后可能需要等待几秒钟才能访问
        
        # 返回格式与原来保持一致
        # 注意：docx API 返回的是 document_id，可以直接用于访问文档 URL
        return {
            "file": {
                "token": document_id,
                "name": title
            }
        }
    
    async def move_file_to_folder(
        self,
        file_token: str,
        folder_token: str
    ) -> bool:
        """将文件/文档移动到指定文件夹
        
        Args:
            file_token: 文件/文档的 token
            folder_token: 目标文件夹的 token
        
        Returns:
            是否移动成功
        """
        endpoint = f"/drive/v1/files/{file_token}/move"
        data = {
            "type": "docx",  # 文档类型
            "folder_token": folder_token
        }
        
        try:
            result = await self._request("POST", endpoint, data=data)
            # 移动操作返回 task_id，表示异步任务
            task_id = result.get("task_id")
            if task_id:
                print(f"📦 移动任务已创建，task_id: {task_id}")
                # 注意：移动是异步操作，可能需要等待
                return True
            else:
                print(f"⚠️  移动操作未返回 task_id")
                return False
        except FeishuAPIError as e:
            # 如果是权限错误，提供更明确的提示
            if e.status_code == 403:
                print(f"⚠️  移动文档失败：权限不足（403）")
                print(f"   提示：可能需要 drive:drive 权限才能移动文档")
            elif e.status_code == 404:
                print(f"⚠️  移动文档失败：文件或文件夹不存在（404）")
                print(f"   提示：请检查 file_token 和 folder_token 是否正确")
            else:
                print(f"⚠️  移动文档失败: {str(e)} (status: {e.status_code}, error_code: {e.error_code})")
            return False
        except Exception as e:
            print(f"⚠️  移动文档时出错: {e}")
            return False
    
    def _markdown_to_feishu_blocks(self, content: str) -> List[Dict[str, Any]]:
        """将 Markdown 内容转换为飞书文档块格式
        
        Args:
            content: Markdown 格式的内容
        
        Returns:
            飞书文档块列表
        """
        blocks = []
        lines = content.split('\n')
        i = 0
        in_code_block = False
        code_block_language = ""
        code_block_content = []
        in_list = False
        list_type = None  # 'bullet' or 'ordered'
        list_items = []
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 处理代码块
            if stripped.startswith('```'):
                if in_code_block:
                    # 结束代码块
                    if code_block_content:
                        # 飞书代码块语言代码：1=PlainText, 2=ABAP, 3=Ada, 4=Apache, 5=Apex, ...
                        # 如果未指定语言，使用 1 (PlainText)
                        language_code = 1  # 默认 PlainText
                        if code_block_language:
                            # 常见语言映射（可以根据需要扩展）
                            lang_map = {
                                'python': 11, 'py': 11,
                                'javascript': 12, 'js': 12,
                                'java': 13,
                                'cpp': 14, 'c++': 14,
                                'c': 15,
                                'go': 16,
                                'rust': 17,
                                'php': 18,
                                'ruby': 19,
                                'swift': 20,
                                'kotlin': 21,
                                'typescript': 22, 'ts': 22,
                                'sql': 23,
                                'html': 24,
                                'css': 25,
                                'json': 26,
                                'xml': 27,
                                'markdown': 28, 'md': 28,
                                'bash': 29, 'shell': 29, 'sh': 29,
                            }
                            language_code = lang_map.get(code_block_language.lower(), 1)
                        
                        blocks.append({
                            "block_type": 14,  # code block
                            "code": {
                                "language": language_code,
                                "elements": [
                                    {
                                        "text_run": {
                                            "content": '\n'.join(code_block_content)
                                        }
                                    }
                                ]
                            }
                        })
                    code_block_content = []
                    code_block_language = ""
                    in_code_block = False
                else:
                    # 开始代码块
                    in_code_block = True
                    code_block_language = stripped[3:].strip()  # 提取语言标识
                i += 1
                continue
            
            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue
            
            # 处理分割线
            if re.match(r'^[-*_]{3,}$', stripped):
                blocks.append({
                    "block_type": 22,  # divider
                    "divider": {}  # divider块需要有divider字段
                })
                i += 1
                continue
            
            # 处理标题 (# 标题)
            heading_match = re.match(r'^(#{1,9})\s+(.+)$', stripped)
            if heading_match:
                # 如果有未完成的列表，先结束它
                if in_list:
                    blocks.extend(self._create_list_blocks(list_items, list_type))
                    list_items = []
                    in_list = False
                
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                # 解析行内格式（粗体、斜体）
                elements = self._parse_inline_formatting(text)
                
                # 标题块使用 heading1-heading9 字段，block_type 为 3-11
                # block_type: 3=heading1, 4=heading2, ..., 11=heading9
                heading_field = f"heading{level}"
                block_data = {
                    "block_type": 2 + level,  # 3-11 for heading1-heading9
                    heading_field: {
                        "elements": elements
                    }
                }
                blocks.append(block_data)
                i += 1
                continue
            
            # 处理引用 (> 引用内容)
            if stripped.startswith('>'):
                # 如果有未完成的列表，先结束它
                if in_list:
                    blocks.extend(self._create_list_blocks(list_items, list_type))
                    list_items = []
                    in_list = False
                
                quote_text = stripped[1:].strip()
                elements = self._parse_inline_formatting(quote_text)
                blocks.append({
                    "block_type": 15,  # quote (引用块)
                    "quote": {
                        "elements": elements
                    }
                })
                i += 1
                continue
            
            # 处理无序列表 (- 或 * 开头)
            bullet_match = re.match(r'^[-*]\s+(.+)$', stripped)
            if bullet_match:
                if not in_list or list_type != 'bullet':
                    # 如果有未完成的列表，先结束它
                    if in_list:
                        blocks.extend(self._create_list_blocks(list_items, list_type))
                        list_items = []
                    in_list = True
                    list_type = 'bullet'
                
                item_text = bullet_match.group(1)
                list_items.append(item_text)
                i += 1
                continue
            
            # 处理有序列表 (1. 开头)
            ordered_match = re.match(r'^\d+\.\s+(.+)$', stripped)
            if ordered_match:
                if not in_list or list_type != 'ordered':
                    # 如果有未完成的列表，先结束它
                    if in_list:
                        blocks.extend(self._create_list_blocks(list_items, list_type))
                        list_items = []
                    in_list = True
                    list_type = 'ordered'
                
                item_text = ordered_match.group(1)
                list_items.append(item_text)
                i += 1
                continue
            
            # 处理普通段落
            if stripped:
                # 如果有未完成的列表，先结束它
                if in_list:
                    blocks.extend(self._create_list_blocks(list_items, list_type))
                    list_items = []
                    in_list = False
                
                elements = self._parse_inline_formatting(stripped)
                blocks.append({
                    "block_type": 2,  # text paragraph
                    "text": {
                        "elements": elements
                    }
                })
            # 空行：如果有未完成的列表，结束它
            elif in_list:
                blocks.extend(self._create_list_blocks(list_items, list_type))
                list_items = []
                in_list = False
            
            i += 1
        
        # 处理文件末尾未完成的列表或代码块
        if in_code_block and code_block_content:
            language_code = 1  # 默认 PlainText
            if code_block_language:
                lang_map = {
                    'python': 11, 'py': 11,
                    'javascript': 12, 'js': 12,
                    'java': 13,
                    'cpp': 14, 'c++': 14,
                    'c': 15,
                    'go': 16,
                    'rust': 17,
                    'php': 18,
                    'ruby': 19,
                    'swift': 20,
                    'kotlin': 21,
                    'typescript': 22, 'ts': 22,
                    'sql': 23,
                    'html': 24,
                    'css': 25,
                    'json': 26,
                    'xml': 27,
                    'markdown': 28, 'md': 28,
                    'bash': 29, 'shell': 29, 'sh': 29,
                }
                language_code = lang_map.get(code_block_language.lower(), 1)
            
            blocks.append({
                "block_type": 14,  # code block
                "code": {
                    "language": language_code,
                    "elements": [
                        {
                            "text_run": {
                                "content": '\n'.join(code_block_content)
                            }
                        }
                    ]
                }
            })
        
        if in_list and list_items:
            blocks.extend(self._create_list_blocks(list_items, list_type))
        
        return blocks
    
    def _parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """解析行内格式（粗体、斜体等）
        
        Args:
            text: 包含 Markdown 格式的文本
        
        Returns:
            飞书文档元素列表
        """
        elements = []
        # 使用正则表达式匹配粗体、斜体、删除线等
        # 匹配模式：**粗体**、*斜体*、~~删除线~~
        pattern = r'(\*\*([^*]+)\*\*|\*([^*]+)\*|~~([^~]+)~~|`([^`]+)`)'
        
        last_pos = 0
        for match in re.finditer(pattern, text):
            # 添加匹配前的普通文本
            if match.start() > last_pos:
                plain_text = text[last_pos:match.start()]
                if plain_text:
                    elements.append({
                        "text_run": {
                            "content": plain_text
                        }
                    })
            
            # 处理匹配的格式
            if match.group(2):  # **粗体**
                elements.append({
                    "text_run": {
                        "content": match.group(2),
                        "text_element_style": {
                            "bold": True
                        }
                    }
                })
            elif match.group(3):  # *斜体*
                elements.append({
                    "text_run": {
                        "content": match.group(3),
                        "text_element_style": {
                            "italic": True
                        }
                    }
                })
            elif match.group(4):  # ~~删除线~~
                elements.append({
                    "text_run": {
                        "content": match.group(4),
                        "text_element_style": {
                            "strikeThrough": True
                        }
                    }
                })
            elif match.group(5):  # `代码`
                elements.append({
                    "text_run": {
                        "content": match.group(5),
                        "text_element_style": {
                            "codeInline": True
                        }
                    }
                })
            
            last_pos = match.end()
        
        # 添加剩余的普通文本
        if last_pos < len(text):
            plain_text = text[last_pos:]
            if plain_text:
                elements.append({
                    "text_run": {
                        "content": plain_text
                    }
                })
        
        # 如果没有匹配到任何格式，返回纯文本
        if not elements:
            elements.append({
                "text_run": {
                    "content": text
                }
            })
        
        return elements
    
    def _create_list_blocks(self, items: List[str], list_type: str) -> List[Dict[str, Any]]:
        """创建列表块
        
        Args:
            items: 列表项文本列表
            list_type: 'bullet' 或 'ordered'
        
        Returns:
            飞书文档块列表
        """
        blocks = []
        block_type = 12 if list_type == 'bullet' else 13  # 12=bullet, 13=ordered
        list_field = "bullet" if list_type == 'bullet' else "ordered"
        
        for item in items:
            elements = self._parse_inline_formatting(item)
            blocks.append({
                "block_type": block_type,
                list_field: {
                    "elements": elements
                }
            })
        
        return blocks
    
    async def update_document_content(
        self,
        document_id: str,
        content: str,
        use_user_token: bool = False
    ) -> bool:
        """更新文档内容

        Args:
            document_id: 文档 ID
            content: 文档内容（Markdown 格式，会自动转换为飞书文档格式）
            use_user_token: 是否使用用户身份 token（默认 False）

        Returns:
            是否更新成功
        """
        try:
            # 第一步：获取文档信息，包括 revision_id 和现有块
            doc_endpoint = f"/docx/v1/documents/{document_id}"
            doc_result = await self._request("GET", doc_endpoint, use_user_token=use_user_token)
            document_data = doc_result.get("data", {}).get("document", {})
            revision_id = document_data.get("revision_id", -1)

            # 第二步：获取根块的所有子块
            blocks_endpoint = f"/docx/v1/documents/{document_id}/blocks"
            blocks_result = await self._request("GET", blocks_endpoint, params={
                "document_revision_id": -1,  # -1 表示最新版本
                "page_size": 500
            }, use_user_token=use_user_token)
            
            # 找到根块（block_id == document_id）
            root_block = None
            items = blocks_result.get("data", {}).get("items", [])
            for item in items:
                if item.get("block_id") == document_id:
                    root_block = item
                    break
            
            # 第三步：如果有现有子块，先删除它们
            if root_block:
                children = root_block.get("children", [])
                if children:
                    # 获取子块数量
                    child_count = len(children)
                    if child_count > 0:
                        # 批量删除所有子块
                        delete_endpoint = f"/docx/v1/documents/{document_id}/blocks/{document_id}/children/batch_delete"
                        delete_data = {
                            "start_index": 0,
                            "end_index": child_count
                        }
                        try:
                            await self._request("DELETE", delete_endpoint,
                                              params={"document_revision_id": revision_id},
                                              data=delete_data,
                                              use_user_token=use_user_token)
                            print(f"✅ 已删除 {child_count} 个现有块")
                        except Exception as e:
                            print(f"⚠️  删除现有块时出错（可能文档为空）: {e}")
                            # 继续执行，可能文档本来就是空的
        
        except Exception as e:
            print(f"⚠️  获取文档信息时出错，将直接添加内容: {e}")
            # 如果获取失败，继续执行，直接添加内容
        
        # 第四步：将 Markdown 内容转换为飞书文档块格式并添加
        endpoint = f"/docx/v1/documents/{document_id}/blocks/{document_id}/children"

        # 将 Markdown 内容转换为飞书文档块格式
        children = self._markdown_to_feishu_blocks(content)

        # 如果没有内容，至少创建一个空文本块
        if not children:
            children.append({
                "block_type": 2,  # 2 表示文本块（段落）
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": content or ""
                            }
                        }
                    ]
                }
            })

        # 分批添加块，避免单次请求过大
        # 飞书API建议每次最多添加30-50个块
        BATCH_SIZE = 30
        total_blocks = len(children)

        try:
            for batch_start in range(0, total_blocks, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_blocks)
                batch_children = children[batch_start:batch_end]

                # 获取最新的 revision_id（每批次都需要获取最新的）
                doc_result = await self._request("GET", f"/docx/v1/documents/{document_id}", use_user_token=use_user_token)
                latest_revision = doc_result.get("data", {}).get("document", {}).get("revision_id", -1)

                data = {
                    "children": batch_children
                }

                await self._request("POST", endpoint,
                                  params={"document_revision_id": latest_revision},
                                  data=data,
                                  use_user_token=use_user_token)
                print(f"✅ 已添加第 {batch_start + 1}-{batch_end} 个块（共 {total_blocks} 个）")

                # 如果还有更多批次，稍微延迟一下，避免触发频率限制
                if batch_end < total_blocks:
                    import asyncio
                    await asyncio.sleep(0.5)  # 延迟500ms

            print(f"✅ 文档内容添加完成，共 {total_blocks} 个块")
            return True
        except Exception as e:
            # 如果更新失败，可能是格式问题
            print(f"⚠️  文档内容更新失败: {e}")
            print("   提示：请检查 Markdown 格式是否正确，或查看飞书 API 错误信息")
            import traceback
            traceback.print_exc()
            return False
    
    async def append_document_content(
        self,
        document_id: str,
        content: str,
        use_user_token: bool = False
    ) -> bool:
        """追加内容到文档末尾（不清空已有内容）"""
        endpoint = f"/docx/v1/documents/{document_id}/blocks/{document_id}/children"

        children = self._markdown_to_feishu_blocks(content)
        if not children:
            children.append({
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {"content": content or ""}
                        }
                    ]
                }
            })

        try:
            doc_result = await self._request("GET", f"/docx/v1/documents/{document_id}", use_user_token=use_user_token)
            latest_revision = doc_result.get("data", {}).get("document", {}).get("revision_id", -1)
            data = {"children": children}
            await self._request(
                "POST",
                endpoint,
                params={"document_revision_id": latest_revision},
                data=data,
                use_user_token=use_user_token
            )
            return True
        except Exception as e:
            print(f"⚠️  追加文档内容失败: {e}")
            return False

    async def get_document_blocks(
        self,
        document_id: str
    ) -> Dict[str, Any]:
        """获取文档的所有块内容
        
        Args:
            document_id: 文档 ID
        
        Returns:
            文档块信息
        """
        endpoint = f"/docx/v1/documents/{document_id}/blocks"
        try:
            result = await self._request("GET", endpoint, params={
                "document_revision_id": -1,
                "page_size": 500
            })
            return result.get("data", {})
        except Exception as e:
            print(f"⚠️  获取文档块失败: {e}")
            return {}
    
    async def get_document(
        self,
        file_token: str
    ) -> Dict[str, Any]:
        """获取文档信息
        
        优先使用 docx API 获取文档信息（因为创建文档返回的是 document_id）
        
        Args:
            file_token: 文档 token 或 document_id
        
        Returns:
            文档信息
        """
        # 优先使用 docx API（因为创建文档返回的是 document_id）
        # 注意：docx API 创建的文档，应该使用 docx API 来获取信息，而不是 drive API
        endpoint = f"/docx/v1/documents/{file_token}"
        print(f"🔍 尝试使用 docx API 获取文档: {endpoint}")
        try:
            result = await self._request("GET", endpoint)
            document_data = result.get("data", {}).get("document", {})
            if document_data:
                print(f"✅ docx API 成功获取文档: {document_data.get('title', 'N/A')}")
                return {
                    "file": {
                        "token": file_token,
                        "name": document_data.get("title", "N/A")
                    }
                }
            else:
                print(f"⚠️  docx API 返回空数据")
                raise FeishuAPIError(
                    message="无法获取文档信息：docx API 返回空数据",
                    status_code=500,
                    error_code="EMPTY_RESPONSE",
                    suggestion="请检查：1. document_id 是否正确 2. 文档是否真的创建成功"
                )
        except FeishuAPIError as e:
            error_msg = str(e) if hasattr(e, '__str__') else f"错误代码: {e.error_code}"
            print(f"❌ docx API 失败: {error_msg} (status: {e.status_code}, error_code: {e.error_code})")
            # 如果 docx API 失败，直接抛出错误（不尝试 drive API，因为 docx API 创建的文档无法通过 drive API 访问）
            if e.status_code == 404:
                raise FeishuAPIError(
                    message=f"文档不存在（404）：使用 docx API 无法访问文档 {file_token}。{error_msg}",
                    status_code=404,
                    error_code=e.error_code,
                    suggestion="请检查：1. document_id 是否正确 2. 文档是否真的创建成功 3. 文档可能创建在了应用无法访问的位置 4. 可能需要等待几秒钟后重试 5. 检查创建文档时的完整API响应"
                )
            else:
                raise
    
    async def get_root_folder_meta(self, use_user_token: bool = False) -> Dict[str, Any]:
        """获取根目录元信息（我的空间）
        
        注意：可能需要用户身份权限才能获取用户的"我的空间"
        
        Args:
            use_user_token: 是否使用用户身份 token（默认 False，使用应用身份 token）
        
        Returns:
            根目录元信息，包含 folder_token
        """
        endpoint = "/drive/explorer/v2/root_folder/meta"
        result = await self._request("GET", endpoint, use_user_token=use_user_token)
        return result.get("data", {})
    
    async def find_folder_by_name(
        self,
        folder_name: str,
        parent_folder_token: Optional[str] = None,
        max_depth: int = 5,
        use_user_token: bool = False
    ) -> Optional[str]:
        """根据文件夹名称查找 folder_token
        
        Args:
            folder_name: 文件夹名称
            parent_folder_token: 父文件夹 token（可选，不指定则从根目录开始查找）
            max_depth: 最大搜索深度，默认5
            use_user_token: 是否使用用户身份 token（默认 False，使用应用身份 token）
        
        Returns:
            文件夹的 token，如果未找到则返回 None
        """
        if max_depth <= 0:
            return None
        
        # 如果没有指定父文件夹，获取根目录
        if not parent_folder_token:
            try:
                root_info = await self.get_root_folder_meta(use_user_token=use_user_token)
                parent_folder_token = root_info.get("token")
            except Exception as e:
                print(f"⚠️  无法获取根目录: {e}")
                return None
        
        # 获取当前文件夹下的所有文件和文件夹
        try:
            result = await self.list_documents(
                folder_token=parent_folder_token, 
                page_size=100,
                use_user_token=use_user_token
            )
            files = result.get("files", [])
            
            # 查找匹配的文件夹
            for file in files:
                if file.get("type") == "folder" and file.get("name") == folder_name:
                    return file.get("token")
            
            # 如果当前目录没找到，递归搜索子文件夹
            for file in files:
                if file.get("type") == "folder":
                    found = await self.find_folder_by_name(
                        folder_name=folder_name,
                        parent_folder_token=file.get("token"),
                        max_depth=max_depth - 1,
                        use_user_token=use_user_token
                    )
                    if found:
                        return found
        except Exception as e:
            print(f"⚠️  搜索文件夹时出错: {e}")
        
        return None
    
    async def list_documents(
        self,
        folder_token: Optional[str] = None,
        page_size: int = 50,
        use_user_token: bool = False
    ) -> Dict[str, Any]:
        """列出文档列表
        
        注意：使用应用身份（tenant_access_token）时，默认读取的是应用创建的文档。
        要读取用户自己的文档，需要：
        1. 指定用户文档库的 folder_token
        2. 或使用用户身份（user_access_token），设置 use_user_token=True
        
        Args:
            folder_token: 文件夹 token（可选，不指定则列出根目录的文档）
            page_size: 每页数量，默认50
            use_user_token: 是否使用用户身份 token（默认 False，使用应用身份 token）
        
        Returns:
            文档列表信息
        """
        endpoint = "/drive/v1/files"
        params = {
            "page_size": page_size
        }
        
        if folder_token:
            params["folder_token"] = folder_token
        elif not use_user_token:
            # 如果不指定 folder_token 且使用应用身份，尝试获取根目录
            # 注意：应用身份可能只能访问应用创建的文档
            print("⚠️  未指定 folder_token，将读取应用创建的文档（不是用户文档库）")
        
        result = await self._request("GET", endpoint, params=params, use_user_token=use_user_token)
        return result.get("data", {})
    
    async def list_wiki_spaces(self) -> List[Dict]:
        """列出知识库（Wiki）空间列表
        
        Returns:
            知识库空间列表
        """
        endpoint = "/wiki/v2/spaces"
        result = await self._request("GET", endpoint)
        return result.get("data", {}).get("items", [])
    
    async def list_wiki_nodes(
        self,
        space_id: str,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """列出知识库中的节点（文档）列表
        
        Args:
            space_id: 知识库空间 ID（可以是字符串或整数）
            page_size: 每页数量，默认50
        
        Returns:
            节点列表信息
        """
        # 注意：space_id 可能需要是整数，尝试转换
        try:
            # 先尝试作为整数
            space_id_int = int(space_id)
            endpoint = f"/wiki/v2/spaces/{space_id_int}/nodes"
        except ValueError:
            # 如果不是整数，尝试作为字符串
            endpoint = f"/wiki/v2/spaces/{space_id}/nodes"
        
        params = {
            "page_size": page_size
        }
        result = await self._request("GET", endpoint, params=params)
        return result.get("data", {})
    
    async def delete_document(
        self,
        file_token: str
    ) -> bool:
        """删除文档
        
        Args:
            file_token: 文档 token
        
        Returns:
            是否删除成功
        """
        endpoint = f"/drive/v1/files/{file_token}"
        await self._request("DELETE", endpoint)
        return True


def convert_memory_to_feishu_fields(
    memory: Dict[str, Any],
    field_name_to_id: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """将记忆数据转换为飞书多维表格字段格式
    
    Args:
        memory: 记忆数据
        field_name_to_id: 字段名称到字段ID的映射（可选，如果提供则使用字段ID）
    """
    fields = {}
    use_field_id = field_name_to_id is not None
    
    # 文本字段
    if "title" in memory:
        key = field_name_to_id.get("标题", "标题") if use_field_id else "标题"
        fields[key] = memory["title"]
    if "content" in memory:
        key = field_name_to_id.get("内容", "内容") if use_field_id else "内容"
        fields[key] = memory["content"]
    if "id" in memory:
        key = field_name_to_id.get("记忆ID", "记忆ID") if use_field_id else "记忆ID"
        fields[key] = memory["id"]
    if "project" in memory and memory["project"]:
        key = field_name_to_id.get("项目", "项目") if use_field_id else "项目"
        fields[key] = memory["project"]
    
    # 单选字段
    if "category" in memory:
        fields["分类"] = memory["category"]
    if "source" in memory and "type" in memory["source"]:
        fields["来源类型"] = memory["source"]["type"]
    
    # 数字字段
    if "importance" in memory:
        fields["重要性"] = memory["importance"]
    
    # 日期时间字段
    # 飞书日期时间字段需要时间戳（毫秒）
    if "created_at" in memory:
        try:
            dt_str = memory["created_at"].replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            # 转换为毫秒时间戳
            fields["创建时间"] = int(dt.timestamp() * 1000)
        except Exception as e:
            # 如果转换失败，尝试其他格式或跳过
            print(f"警告: 创建时间转换失败: {e}")
            pass
    
    if "updated_at" in memory:
        try:
            dt_str = memory["updated_at"].replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            fields["更新时间"] = int(dt.timestamp() * 1000)
        except Exception as e:
            print(f"警告: 更新时间转换失败: {e}")
            pass
    
    # 多选字段（标签）
    # 飞书多选字段需要数组格式，空数组也要传
    if "tags" in memory:
        if isinstance(memory["tags"], list):
            fields["标签"] = memory["tags"] if memory["tags"] else []
        else:
            fields["标签"] = []
    
    # 复选框字段
    # 飞书复选框字段需要布尔值
    if "archived" in memory:
        fields["是否归档"] = bool(memory["archived"])
    
    return fields

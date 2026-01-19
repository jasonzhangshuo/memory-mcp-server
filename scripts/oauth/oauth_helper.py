#!/usr/bin/env python3
"""飞书 OAuth 授权助手 - 自动获取授权"""

import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient

# 全局变量存储授权码
auth_code = None
auth_state = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuth 回调处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        global auth_code, auth_state

        # 解析 URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # 获取授权码
        auth_code = params.get('code', [None])[0]
        auth_state = params.get('state', [None])[0]

        # 返回响应
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        if auth_code:
            html = """
            <html>
            <head><title>授权成功</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ 授权成功！</h1>
                <p>授权码已获取，正在处理...</p>
                <p>你可以关闭此窗口了。</p>
            </body>
            </html>
            """
        else:
            html = """
            <html>
            <head><title>授权失败</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ 授权失败</h1>
                <p>未能获取授权码，请重试。</p>
            </body>
            </html>
            """

        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


async def exchange_token(code: str):
    """使用授权码换取 user_access_token"""
    client = FeishuClient()

    print()
    print("🔄 正在使用授权码换取 user_access_token...")

    try:
        token_data = await client.exchange_user_access_token(code)

        print("✅ 成功获取 user_access_token！")
        print()
        print("📋 Token 信息:")
        print(f"   Access Token: {token_data.get('access_token', 'N/A')[:20]}...")
        print(f"   Refresh Token: {token_data.get('refresh_token', 'N/A')[:20]}...")
        print(f"   Expires In: {token_data.get('expires_in', 'N/A')} 秒")
        print()

        # 保存 token 到文件
        token_file = project_root / '.user_token.json'
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Token 已保存到: {token_file}")
        print()

        return token_data

    except Exception as e:
        print(f"❌ 换取 token 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_user_documents():
    """测试读取用户文档"""
    client = FeishuClient()

    # 加载保存的 token
    token_file = project_root / '.user_token.json'
    if token_file.exists():
        with open(token_file, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        client.user_access_token = token_data.get('access_token')
        client.refresh_token = token_data.get('refresh_token')

        from datetime import datetime, timedelta
        expires_in = token_data.get('expires_in', 7200)
        client.user_token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

    print("=" * 70)
    print("📚 测试读取用户文档库")
    print("=" * 70)
    print()

    try:
        # 获取根目录信息
        print("📁 获取用户根目录...")
        root_info = await client.get_root_folder_meta(use_user_token=True)
        root_token = root_info.get('token')
        print(f"   根目录 Token: {root_token}")
        print()

        # 列出用户文档
        print("📄 读取用户文档列表...")
        result = await client.list_documents(
            folder_token=root_token,
            page_size=20,
            use_user_token=True
        )

        files = result.get('files', [])
        print(f"✅ 找到 {len(files)} 个文件/文档")
        print()

        if files:
            print("📋 文档列表:")
            print("-" * 70)
            for i, file in enumerate(files, 1):
                file_type = file.get('type', 'N/A')
                name = file.get('name', 'N/A')
                token = file.get('token', 'N/A')
                print(f"{i:2d}. [{file_type}] {name}")
                if file_type == 'docx':
                    print(f"    URL: https://my.feishu.cn/docx/{token}")
                print()
        else:
            print("   暂无文档")

        print("=" * 70)
        print("🎉 成功！现在可以读取你的个人云文档了！")
        print("=" * 70)

    except Exception as e:
        print(f"❌ 读取文档失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 70)
    print("🔐 飞书 OAuth 授权助手")
    print("=" * 70)
    print()

    # 检查配置
    client = FeishuClient()
    redirect_uri = "http://localhost:8000/callback"

    # 生成授权链接
    auth_url = client.get_oauth_authorize_url(
        redirect_uri=redirect_uri,
        state='oauth_helper'
    )

    print("📋 步骤 1: 请先在飞书开放平台配置回调地址")
    print("-" * 70)
    print(f"   回调地址: {redirect_uri}")
    print()
    print("   配置位置:")
    print("   1. 访问: https://open.feishu.cn/")
    print("   2. 进入应用: cli_a9e9a4047fb8dbc4")
    print("   3. 左侧菜单 > 安全设置 > 重定向 URL")
    print("   4. 添加上面的回调地址")
    print()

    input("   配置完成后，按 Enter 继续...")
    print()

    print("=" * 70)
    print("🚀 步骤 2: 启动本地服务器并打开授权页面")
    print("=" * 70)
    print()
    print(f"   本地服务器: {redirect_uri}")
    print(f"   授权链接: {auth_url}")
    print()
    print("   即将自动打开浏览器，请在浏览器中完成授权...")
    print()

    # 启动本地服务器
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)

    # 打开浏览器
    print("🌐 正在打开浏览器...")
    webbrowser.open(auth_url)
    print()
    print("⏳ 等待授权回调...")
    print("   (完成授权后服务器会自动关闭)")
    print()

    # 等待授权回调
    global auth_code
    while auth_code is None:
        server.handle_request()

    server.server_close()
    print("✅ 收到授权回调！")
    print(f"   授权码: {auth_code[:20]}...")
    print()

    # 换取 token
    token_data = asyncio.run(exchange_token(auth_code))

    if token_data:
        # 测试读取用户文档
        print()
        input("按 Enter 继续测试读取用户文档...")
        asyncio.run(test_user_documents())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("❌ 用户取消")
    except Exception as e:
        print()
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

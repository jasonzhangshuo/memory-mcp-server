#!/usr/bin/env python3
"""测试列出飞书文档"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def test_list_documents():
    """测试列出文档"""
    try:
        print("=" * 60)
        print("🧪 测试列出飞书文档")
        print("=" * 60)
        print()

        # 初始化客户端
        print("📋 初始化飞书客户端...")
        client = FeishuClient()
        print(f"   App ID: {client.app_id}")
        print()

        # 测试1: 使用应用身份列出文档（会列出应用创建的文档）
        print("📁 测试1: 使用应用身份列出文档...")
        print("   （会列出应用创建的文档）")
        print()

        result = await client.list_documents(
            page_size=10,
            use_user_token=False
        )

        files = result.get("files", [])
        print(f"✅ 找到 {len(files)} 个文件/文档")
        print()

        if files:
            print("📄 文档列表:")
            for i, file in enumerate(files, 1):
                file_type = file.get("type", "N/A")
                name = file.get("name", "N/A")
                token = file.get("token", "N/A")
                print(f"   {i}. [{file_type}] {name}")
                print(f"      Token: {token}")
                if file_type == "docx":
                    print(f"      URL: https://my.feishu.cn/docx/{token}")
        else:
            print("   暂无文档")
        print()

        # 测试2: 尝试获取根目录信息
        print("📁 测试2: 尝试获取根目录信息...")
        try:
            root_info = await client.get_root_folder_meta(use_user_token=False)
            print(f"   根目录 token: {root_info.get('token', 'N/A')}")
            print()
        except Exception as e:
            print(f"   ⚠️  获取根目录失败: {e}")
            print()

        return result

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 列出文档失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_list_documents())

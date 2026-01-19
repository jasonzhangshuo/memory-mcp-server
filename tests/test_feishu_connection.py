#!/usr/bin/env python3
"""测试飞书 API 连接"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def test_connection():
    """测试飞书 API 连接"""
    print("=" * 60)
    print("🔍 测试飞书 API 连接")
    print("=" * 60)
    print()
    
    try:
        # 初始化客户端
        print("1️⃣ 初始化飞书客户端...")
        client = FeishuClient()
        print(f"   ✅ App ID: {client.app_id}")
        print(f"   ✅ App Token: {client.app_token}")
        print(f"   ✅ Table ID: {client.table_id}")
        print()
        
        # 获取访问令牌
        print("2️⃣ 获取访问令牌...")
        token = await client.get_access_token()
        print(f"   ✅ Token 获取成功: {token[:20]}...")
        print()
        
        # 列出数据表
        print("3️⃣ 列出多维表格中的数据表...")
        tables = await client.list_tables()
        print(f"   ✅ 找到 {len(tables)} 个数据表:")
        for table in tables:
            print(f"      - {table.get('name', 'N/A')} (ID: {table.get('table_id', 'N/A')})")
        print()
        
        # 获取字段列表
        print("4️⃣ 获取数据表字段...")
        fields = await client.get_table_fields()
        print(f"   ✅ 找到 {len(fields)} 个字段:")
        for field in fields:
            field_name = field.get('field_name', 'N/A')
            field_type = field.get('type', 'N/A')
            print(f"      - {field_name} ({field_type})")
        print()
        
        print("=" * 60)
        print("✅ 所有测试通过！API 连接正常")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 测试失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        
        # 如果是 HTTP 错误，显示更多信息
        if "400" in str(e) or "Bad Request" in str(e):
            print("⚠️  400 错误可能的原因:")
            print("   1. API 端点不正确")
            print("   2. 权限未正确申请或未生效")
            print("   3. app_token 不正确")
            print("   4. 需要重新发布应用")
        elif "401" in str(e) or "Unauthorized" in str(e):
            print("⚠️  401 错误可能的原因:")
            print("   1. App ID 或 App Secret 不正确")
            print("   2. Token 已过期")
        elif "403" in str(e) or "Forbidden" in str(e):
            print("⚠️  403 错误可能的原因:")
            print("   1. 权限未申请或未通过")
            print("   2. 应用未发布")
        
        print()
        print("请检查:")
        print("1. .env 文件中的配置是否正确")
        print("2. 飞书应用的权限是否已开通并生效")
        print("3. 应用是否需要重新发布")
        print("4. 网络连接是否正常")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_connection())

#!/usr/bin/env python3
"""检查飞书所有权限状态"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient
import httpx


async def check_bitable_permission(client: FeishuClient) -> tuple[bool, str]:
    """检查多维表格权限"""
    try:
        # 尝试列出数据表（需要 bitable:app 权限）
        tables = await client.list_tables()
        return True, f"✅ 多维表格权限正常（找到 {len(tables)} 个数据表）"
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            return False, "❌ 多维表格权限未开通（403 Forbidden）"
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return False, "❌ Token 认证失败（401 Unauthorized）"
        else:
            return False, f"❌ 多维表格权限检查失败: {error_msg}"


async def check_drive_permission(client: FeishuClient) -> tuple[bool, str]:
    """检查文档权限"""
    try:
        token = await client.get_access_token()
        
        # 尝试调用文档 API（需要 drive:drive 权限）
        # 这里只是测试权限，不实际创建文档
        url = "https://open.feishu.cn/open-apis/drive/v1/files"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 使用 OPTIONS 或 HEAD 请求测试权限（更安全）
        # 或者尝试列出文件（只读操作）
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            # 尝试获取根目录文件列表（需要 drive:drive:readonly 或 drive:drive）
            response = await http_client.get(
                "https://open.feishu.cn/open-apis/drive/v1/files",
                headers=headers,
                params={"folder_token": ""}  # 根目录
            )
            
            if response.status_code == 200:
                return True, "✅ 文档权限正常（可以访问云空间）"
            elif response.status_code == 403:
                return False, "❌ 文档权限未开通（403 Forbidden）"
            elif response.status_code == 401:
                return False, "❌ Token 认证失败（401 Unauthorized）"
            else:
                return False, f"❌ 文档权限检查失败（HTTP {response.status_code}）"
                
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            return False, "❌ 文档权限未开通（403 Forbidden）"
        elif "401" in error_msg or "Unauthorized" in error_msg:
            return False, "❌ Token 认证失败（401 Unauthorized）"
        else:
            return False, f"❌ 文档权限检查失败: {error_msg}"


async def check_write_permission(client: FeishuClient) -> tuple[bool, str]:
    """检查写入权限（多维表格）"""
    try:
        # 尝试创建一个测试记录（然后立即删除）
        # 这里只测试权限，不实际创建
        # 或者尝试获取字段列表，如果能获取说明有读取权限
        fields = await client.get_table_fields()
        
        # 如果能获取字段，说明至少有读取权限
        # 写入权限需要通过实际写入测试，但这里先不测试写入
        return True, f"✅ 多维表格读取权限正常（找到 {len(fields)} 个字段）"
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            return False, "❌ 多维表格写入权限可能未开通"
        else:
            return False, f"❌ 权限检查失败: {error_msg}"


async def main():
    """主函数"""
    print("=" * 60)
    print("🔍 检查飞书权限状态")
    print("=" * 60)
    print()
    
    try:
        # 初始化客户端
        print("📋 初始化飞书客户端...")
        client = FeishuClient()
        print(f"   App ID: {client.app_id}")
        print(f"   App Token: {client.app_token[:20]}...")
        print()
        
        # 获取访问令牌
        print("🔑 获取访问令牌...")
        token = await client.get_access_token()
        print(f"   ✅ Token 获取成功")
        print()
        
        # 检查各项权限
        print("=" * 60)
        print("📊 权限检查结果")
        print("=" * 60)
        print()
        
        results = []
        
        # 1. 检查多维表格权限
        print("1️⃣ 检查多维表格权限（bitable:app）...")
        bitable_ok, bitable_msg = await check_bitable_permission(client)
        print(f"   {bitable_msg}")
        results.append(("多维表格权限", bitable_ok, bitable_msg))
        print()
        
        # 2. 检查文档权限
        print("2️⃣ 检查文档权限（drive:drive）...")
        drive_ok, drive_msg = await check_drive_permission(client)
        print(f"   {drive_msg}")
        results.append(("文档权限", drive_ok, drive_msg))
        print()
        
        # 3. 检查写入权限
        print("3️⃣ 检查多维表格读取权限...")
        write_ok, write_msg = await check_write_permission(client)
        print(f"   {write_msg}")
        results.append(("多维表格读取", write_ok, write_msg))
        print()
        
        # 总结
        print("=" * 60)
        print("📋 权限状态总结")
        print("=" * 60)
        print()
        
        all_ok = True
        for name, ok, msg in results:
            status = "✅ 已开通" if ok else "❌ 未开通"
            print(f"{status} - {name}")
            if not ok:
                all_ok = False
        
        print()
        
        if all_ok:
            print("✅ 所有权限已开通！")
        else:
            print("⚠️  部分权限未开通，请参考以下链接申请：")
            print()
            print("多维表格权限：")
            print("https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=bitable:app&op_from=openapi&token_type=tenant")
            print()
            print("文档权限：")
            print("https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=drive:drive&op_from=openapi&token_type=tenant")
            print()
            print("同时申请所有权限：")
            print("https://open.feishu.cn/app/cli_a9e9a4047fb8dbc4/auth?q=bitable:app,drive:drive&op_from=openapi&token_type=tenant")
        
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 检查失败")
        print("=" * 60)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

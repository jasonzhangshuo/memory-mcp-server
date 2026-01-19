#!/usr/bin/env python3
"""读取小红书飞书表格数据"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def read_xiaohongshu_table():
    """读取小红书表格数据"""
    print("=" * 60)
    print("📖 读取小红书飞书表格")
    print("=" * 60)
    print()
    
    # 从URL提取的信息
    xiaohongshu_app_token = "PDcyb3J5GaPzAtsqVmdcEt5xnEc"
    xiaohongshu_table_id = "tblANFToIqllNzTG"
    
    try:
        # 使用现有的应用配置
        client = FeishuClient()
        
        # 临时使用新的表格配置
        original_app_token = client.app_token
        original_table_id = client.table_id
        
        client.app_token = xiaohongshu_app_token
        client.table_id = xiaohongshu_table_id
        
        print(f"📋 表格信息:")
        print(f"   App Token: {xiaohongshu_app_token}")
        print(f"   Table ID: {xiaohongshu_table_id}")
        print()
        
        # 1. 测试访问令牌
        print("1️⃣ 获取访问令牌...")
        token = await client.get_access_token()
        print(f"   ✅ Token 获取成功")
        print()
        
        # 2. 获取字段列表
        print("2️⃣ 获取字段列表...")
        try:
            fields = await client.get_table_fields(table_id=xiaohongshu_table_id)
            print(f"   ✅ 找到 {len(fields)} 个字段:")
            for field in fields:
                field_name = field.get('field_name', 'N/A')
                field_type = field.get('type', 'N/A')
                print(f"      - {field_name} ({field_type})")
            print()
        except Exception as e:
            print(f"   ❌ 获取字段失败: {e}")
            return
        
        # 3. 获取所有记录
        print("3️⃣ 获取所有记录...")
        try:
            all_records = []
            page_token = None
            
            while True:
                result = await client.list_records(
                    table_id=xiaohongshu_table_id, 
                    page_token=page_token, 
                    page_size=100
                )
                records = result.get("items", [])
                all_records.extend(records)
                
                page_token = result.get("page_token")
                if not page_token:
                    break
            
            print(f"   ✅ 找到 {len(all_records)} 条记录")
            print()
            
            # 4. 显示记录详情
            if all_records:
                print("4️⃣ 记录详情（前5条）:")
                for i, record in enumerate(all_records[:5], 1):
                    print(f"\n   【记录 {i}】")
                    fields = record.get("fields", {})
                    record_id = record.get("record_id", "N/A")
                    
                    # 显示所有字段
                    for field_name, field_value in fields.items():
                        if isinstance(field_value, list):
                            if field_value and isinstance(field_value[0], dict):
                                # 附件字段
                                print(f"      {field_name}: [附件] {len(field_value)} 个文件")
                                for item in field_value[:2]:
                                    file_name = item.get('name', 'N/A')
                                    file_token = item.get('token', 'N/A')
                                    file_type = item.get('type', 'N/A')
                                    print(f"        - {file_name} ({file_type}, token: {file_token[:30]}...)")
                            else:
                                print(f"      {field_name}: {field_value}")
                        elif isinstance(field_value, dict):
                            # 复杂对象，格式化显示
                            print(f"      {field_name}:")
                            for k, v in field_value.items():
                                print(f"        {k}: {v}")
                        else:
                            value_str = str(field_value)
                            if len(value_str) > 200:
                                value_str = value_str[:200] + "..."
                            print(f"      {field_name}: {value_str}")
                    
                    print(f"      记录ID: {record_id}")
                
                if len(all_records) > 5:
                    print(f"\n   ... 还有 {len(all_records) - 5} 条记录未显示")
            else:
                print("   ⚠️  表格中没有记录")
                
        except Exception as e:
            print(f"   ❌ 获取记录失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 恢复原始配置
        client.app_token = original_app_token
        client.table_id = original_table_id
        
        print()
        print("=" * 60)
        print("✅ 读取完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print()
        print("💡 可能的原因:")
        print("1. 应用未添加为该表格的协作者")
        print("2. 应用权限未申请或未生效")
        print("3. App ID 或 App Secret 配置错误")
        print("4. 网络连接问题")


if __name__ == "__main__":
    asyncio.run(read_xiaohongshu_table())

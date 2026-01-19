#!/usr/bin/env python3
"""读取小红书博主笔记表格（我的笔记）"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def read_my_notes():
    """读取我的笔记"""
    print("=" * 60)
    print("📝 读取小红书博主笔记（我的笔记）")
    print("=" * 60)
    print()
    
    # 从URL提取的信息
    xiaohongshu_app_token = "PDcyb3J5GaPzAtsqVmdcEt5xnEc"
    my_notes_table_id = "tblVe01tmcfBwPeO"
    
    try:
        # 使用现有的应用配置
        client = FeishuClient()
        
        # 临时使用新的表格配置
        original_app_token = client.app_token
        original_table_id = client.table_id
        
        client.app_token = xiaohongshu_app_token
        client.table_id = my_notes_table_id
        
        print(f"📋 表格信息:")
        print(f"   App Token: {xiaohongshu_app_token}")
        print(f"   Table ID: {my_notes_table_id}")
        print()
        
        # 1. 获取字段列表
        print("1️⃣ 获取字段列表...")
        fields = await client.get_table_fields(table_id=my_notes_table_id)
        print(f"   ✅ 找到 {len(fields)} 个字段:")
        for field in fields:
            field_name = field.get('field_name', 'N/A')
            field_type = field.get('type', 'N/A')
            print(f"      - {field_name} ({field_type})")
        print()
        
        # 2. 获取所有记录
        print("2️⃣ 获取所有记录...")
        all_records = []
        page_token = None
        
        while True:
            result = await client.list_records(
                table_id=my_notes_table_id, 
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
        
        # 3. 显示记录详情
        if all_records:
            print("3️⃣ 我的笔记详情:")
            for i, record in enumerate(all_records, 1):
                print(f"\n   【笔记 {i}】")
                fields = record.get("fields", {})
                record_id = record.get("record_id", "N/A")
                
                # 显示所有字段
                for field_name, field_value in fields.items():
                    if isinstance(field_value, list):
                        if field_value and isinstance(field_value[0], dict):
                            # 附件字段
                            print(f"      {field_name}: [附件] {len(field_value)} 个文件")
                            for item in field_value[:3]:
                                file_name = item.get('name', 'N/A')
                                file_token = item.get('token', 'N/A')
                                file_type = item.get('type', 'N/A')
                                print(f"        - {file_name} ({file_type})")
                        else:
                            print(f"      {field_name}: {field_value}")
                    elif isinstance(field_value, dict):
                        # 复杂对象，格式化显示
                        if 'link' in field_value:
                            print(f"      {field_name}: {field_value.get('link', 'N/A')}")
                        else:
                            print(f"      {field_name}:")
                            for k, v in list(field_value.items())[:5]:  # 只显示前5个键值对
                                print(f"        {k}: {v}")
                    else:
                        value_str = str(field_value)
                        if len(value_str) > 300:
                            value_str = value_str[:300] + "..."
                        print(f"      {field_name}: {value_str}")
                
                print(f"      记录ID: {record_id}")
        else:
            print("   ⚠️  表格中没有记录")
        
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


if __name__ == "__main__":
    asyncio.run(read_my_notes())

#!/usr/bin/env python3
"""清理飞书多维表格中的空记录"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def clean_empty_records():
    """清理空记录"""
    print("=" * 60)
    print("🧹 清理飞书多维表格中的空记录")
    print("=" * 60)
    print()
    
    try:
        client = FeishuClient()
        
        # 获取所有记录
        print("📖 获取所有记录...")
        all_records = []
        page_token = None
        
        while True:
            result = await client.list_records(page_token=page_token, page_size=100)
            records = result.get("items", [])
            all_records.extend(records)
            
            page_token = result.get("page_token")
            if not page_token:
                break
        
        print(f"   ✅ 找到 {len(all_records)} 条记录")
        print()
        
        # 找出空记录
        empty_records = []
        for record in all_records:
            fields = record.get("fields", {})
            title = fields.get("标题", "")
            memory_id = fields.get("记忆ID", "")
            content = fields.get("内容", "")
            
            # 如果标题、记忆ID和内容都为空，认为是空记录
            if not title and not memory_id and not content:
                empty_records.append(record)
        
        if not empty_records:
            print("✅ 没有发现空记录")
            return
        
        print(f"⚠️  发现 {len(empty_records)} 条空记录")
        print()
        
        # 显示空记录
        print("空记录列表:")
        for i, record in enumerate(empty_records, 1):
            record_id = record.get("record_id", "N/A")
            print(f"   {i}. 记录ID: {record_id}")
        print()
        
        # 确认删除
        print("=" * 60)
        print("⚠️  警告：将删除这些空记录")
        print("=" * 60)
        print()
        confirm = input("确认删除？(yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ 已取消")
            return
        
        # 删除空记录
        print()
        print("🗑️  开始删除...")
        deleted_count = 0
        failed_count = 0
        
        for record in empty_records:
            record_id = record.get("record_id")
            try:
                await client.delete_record(record_id)
                deleted_count += 1
                print(f"   ✅ 已删除: {record_id}")
                # 避免请求过快
                await asyncio.sleep(0.2)
            except Exception as e:
                failed_count += 1
                print(f"   ❌ 删除失败: {record_id} - {e}")
        
        print()
        print("=" * 60)
        print("📊 清理完成")
        print("=" * 60)
        print(f"✅ 成功删除: {deleted_count} 条")
        if failed_count > 0:
            print(f"❌ 删除失败: {failed_count} 条")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(clean_empty_records())

#!/usr/bin/env python3
"""删除飞书多维表格中的测试记忆"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sync.feishu_client import FeishuClient


async def delete_test_memories():
    """删除测试记忆"""
    print("=" * 60)
    print("🗑️  删除飞书多维表格中的测试记忆")
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
        
        # 识别测试记忆
        test_records = []
        test_keywords = ["测试", "test", "验证"]
        
        for record in all_records:
            fields = record.get("fields", {})
            title = fields.get("标题", "")
            memory_id = fields.get("记忆ID", "")
            
            # 检查标题是否包含测试关键词
            if title and any(keyword in title.lower() for keyword in test_keywords):
                test_records.append((record, title, memory_id))
        
        if not test_records:
            print("✅ 没有发现测试记忆")
            return
        
        print(f"⚠️  发现 {len(test_records)} 条测试记忆:")
        print()
        for i, (record, title, memory_id) in enumerate(test_records, 1):
            record_id = record.get("record_id", "N/A")
            category = record.get("fields", {}).get("分类", "N/A")
            print(f"   {i}. {title}")
            print(f"      分类: {category}")
            print(f"      记录ID: {record_id}")
            print()
        
        # 确认删除
        print("=" * 60)
        print("⚠️  警告：将删除以上测试记忆")
        print("=" * 60)
        print()
        
        # 检查命令行参数
        import sys
        if "--yes" in sys.argv or "-y" in sys.argv:
            confirm = "yes"
            print("✅ 使用 --yes 参数，自动确认删除")
        else:
            try:
                confirm = input(f"确认删除 {len(test_records)} 条测试记忆？(yes/no): ").strip().lower()
            except EOFError:
                print("❌ 非交互式环境，请使用 --yes 参数自动确认")
                print("   运行: python delete_test_memories.py --yes")
                return
        
        if confirm != "yes":
            print("❌ 已取消")
            return
        
        # 删除测试记录
        print()
        print("🗑️  开始删除...")
        deleted_count = 0
        failed_count = 0
        
        for record, title, memory_id in test_records:
            record_id = record.get("record_id")
            try:
                await client.delete_record(record_id)
                deleted_count += 1
                print(f"   ✅ 已删除: {title}")
                # 避免请求过快
                await asyncio.sleep(0.2)
            except Exception as e:
                failed_count += 1
                print(f"   ❌ 删除失败: {title} - {e}")
        
        print()
        print("=" * 60)
        print("📊 删除完成")
        print("=" * 60)
        print(f"✅ 成功删除: {deleted_count} 条")
        if failed_count > 0:
            print(f"❌ 删除失败: {failed_count} 条")
        print(f"📝 剩余记录: {len(all_records) - deleted_count} 条")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(delete_test_memories())

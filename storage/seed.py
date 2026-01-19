"""Seed data initialization for personal memory system."""

import asyncio
import uuid
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import init_db, add_memory

# Seed data from PRD Appendix A
SEED_DATA = [
    {
        "category": "identity",
        "title": "基本身份信息",
        "content": "张硕，44岁，2026年7月满45岁。曾任创业者和互联网公司总监。学佛8年。",
        "importance": 5
    },
    {
        "category": "goal",
        "title": "核心目标：50岁退休",
        "content": "为50岁退休做好身体与精神的双重准备。不是'再赢一次'，而是'不再走错'。",
        "importance": 5
    },
    {
        "category": "pattern",
        "title": "行为模式：研究替代到达",
        "content": "爱研究不爱到达。研究→优化→迭代→下一个研究的循环给掌控感和快感，但永远在起点附近打转。",
        "importance": 5
    },
    {
        "category": "commitment",
        "title": "三个锚点",
        "content": "晨间定课（起床后碰手机前）、身体运动（灵活安排）、睡前回顾（写下今天到达了什么）。锚点是身份不是任务，可以缩短但不能取消。",
        "importance": 5
    },
    {
        "category": "principle",
        "title": "止损规则",
        "content": "智能体/工具迭代每周最多2小时；久坐45-60分钟必须起身；眼睛干涩/前列腺不适=当天停止屏幕工作；没有明确目的禁止vibe coding。",
        "importance": 4
    }
]


async def seed_database():
    """Initialize database and load seed data."""
    print("Initializing database...")
    await init_db()
    
    print("Loading seed data...")
    for item in SEED_DATA:
        memory_id = str(uuid.uuid4())
        await add_memory(
            memory_id=memory_id,
            category=item["category"],
            title=item["title"],
            content=item["content"],
            importance=item["importance"],
            source_type="manual"
        )
        print(f"  ✓ Added: {item['title']}")
    
    print("Seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())

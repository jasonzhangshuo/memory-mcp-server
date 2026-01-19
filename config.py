"""配置文件：区分生产环境和测试环境"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 环境变量：TEST_MODE
# 设置为 "true" 时使用测试数据库
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# 数据库路径
if TEST_MODE:
    DB_PATH = os.path.join(PROJECT_ROOT, "test_memory.db")
    ENTRIES_DIR = os.path.join(PROJECT_ROOT, "test_entries")
    print(f"⚠️  测试模式: 使用测试数据库 {DB_PATH}")
else:
    DB_PATH = os.path.join(PROJECT_ROOT, "memory.db")
    ENTRIES_DIR = os.path.join(PROJECT_ROOT, "entries")

# 数据库配置
DB_CONFIG = {
    "path": DB_PATH,
    "entries_dir": ENTRIES_DIR,
    "test_mode": TEST_MODE
}


def is_test_mode() -> bool:
    """判断是否为测试模式"""
    return TEST_MODE


def get_db_path() -> str:
    """获取数据库路径"""
    return DB_PATH


def get_entries_dir() -> str:
    """获取条目目录路径"""
    return ENTRIES_DIR


def setup_test_mode():
    """切换到测试模式（用于测试脚本）"""
    global TEST_MODE, DB_PATH, ENTRIES_DIR
    TEST_MODE = True
    DB_PATH = os.path.join(PROJECT_ROOT, "test_memory.db")
    ENTRIES_DIR = os.path.join(PROJECT_ROOT, "test_entries")
    print(f"⚠️  已切换到测试模式: {DB_PATH}")


def cleanup_test_data():
    """清理测试数据"""
    if not TEST_MODE:
        raise RuntimeError("只能在测试模式下清理测试数据")
    
    import shutil
    
    # 删除测试数据库
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✅ 已删除测试数据库: {DB_PATH}")
    
    # 删除测试条目目录
    if os.path.exists(ENTRIES_DIR):
        shutil.rmtree(ENTRIES_DIR)
        print(f"✅ 已删除测试条目目录: {ENTRIES_DIR}")

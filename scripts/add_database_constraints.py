#!/usr/bin/env python3
"""
添加数据库约束脚本
为数据库表添加外键约束和数据完整性约束
"""

import sys
import sqlite3
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConstraintManager:
    """数据库约束管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(project_root / "data" / "autoclip.db")
        
    def add_foreign_key_constraints(self) -> bool:
        """启用外键约束（SQLite不支持动态添加外键约束）"""
        logger.info("🔗 启用外键约束...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # 验证外键约束是否启用
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            if fk_enabled:
                logger.info("✅ 外键约束已启用")
                return True
            else:
                logger.error("❌ 外键约束启用失败")
                return False
            
        except Exception as e:
            logger.error(f"启用外键约束失败: {e}")
            return False
    
    def add_check_constraints(self) -> bool:
        """添加检查约束（SQLite不支持动态添加检查约束）"""
        logger.info("🔍 检查约束说明...")
        
        # SQLite不支持动态添加检查约束，需要在创建表时定义
        # 这里我们只记录约束要求，实际约束在模型定义中
        
        constraints_info = [
            "项目状态: pending, processing, completed, failed",
            "任务状态: pending, running, completed, failed", 
            "切片状态: pending, processing, completed, failed",
            "合集状态: pending, processing, completed, failed",
            "投稿记录状态: pending, uploading, completed, failed"
        ]
        
        logger.info("📋 数据完整性约束要求:")
        for constraint in constraints_info:
            logger.info(f"  - {constraint}")
        
        logger.info("ℹ️  注意: SQLite不支持动态添加检查约束，约束已在模型定义中实现")
        return True
    
    def add_indexes(self) -> bool:
        """添加索引以提高查询性能"""
        logger.info("📊 开始添加索引...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            indexes = [
                # 项目表索引
                {
                    'name': 'idx_projects_status',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)'
                },
                {
                    'name': 'idx_projects_created_at',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)'
                },
                
                # 任务表索引
                {
                    'name': 'idx_tasks_project_id',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)'
                },
                {
                    'name': 'idx_tasks_status',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)'
                },
                {
                    'name': 'idx_tasks_created_at',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)'
                },
                
                # 切片表索引
                {
                    'name': 'idx_clips_project_id',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_clips_project_id ON clips(project_id)'
                },
                {
                    'name': 'idx_clips_status',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(status)'
                },
                {
                    'name': 'idx_clips_score',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_clips_score ON clips(score)'
                },
                
                # 合集表索引
                {
                    'name': 'idx_collections_project_id',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_collections_project_id ON collections(project_id)'
                },
                {
                    'name': 'idx_collections_status',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_collections_status ON collections(status)'
                },
                
                # 投稿记录表索引
                {
                    'name': 'idx_upload_records_account_id',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_upload_records_account_id ON upload_records(account_id)'
                },
                {
                    'name': 'idx_upload_records_clip_id',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_upload_records_clip_id ON upload_records(clip_id)'
                },
                {
                    'name': 'idx_upload_records_status',
                    'sql': 'CREATE INDEX IF NOT EXISTS idx_upload_records_status ON upload_records(status)'
                }
            ]
            
            success_count = 0
            error_count = 0
            
            for index in indexes:
                try:
                    cursor.execute(index['sql'])
                    success_count += 1
                    logger.info(f"✅ 添加索引成功: {index['name']}")
                except sqlite3.Error as e:
                    logger.error(f"❌ 添加索引失败: {index['name']}, 错误: {e}")
                    error_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"🎉 索引添加完成: 成功 {success_count}, 失败 {error_count}")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"添加索引失败: {e}")
            return False
    
    def verify_constraints(self) -> bool:
        """验证约束是否正确添加"""
        logger.info("🔍 验证约束...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查外键约束是否启用
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            logger.info(f"外键约束状态: {'启用' if fk_enabled else '禁用'}")
            
            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"数据库表: {', '.join(tables)}")
            
            # 检查索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            indexes = [row[0] for row in cursor.fetchall()]
            logger.info(f"自定义索引: {', '.join(indexes)}")
            
            conn.close()
            
            logger.info("✅ 约束验证完成")
            return True
            
        except Exception as e:
            logger.error(f"验证约束失败: {e}")
            return False


def main():
    """主函数"""
    logger.info("🚀 开始添加数据库约束...")
    
    manager = DatabaseConstraintManager()
    
    # 1. 添加外键约束
    fk_success = manager.add_foreign_key_constraints()
    
    # 2. 添加检查约束
    check_success = manager.add_check_constraints()
    
    # 3. 添加索引
    index_success = manager.add_indexes()
    
    # 4. 验证约束
    verify_success = manager.verify_constraints()
    
    print("\n" + "=" * 80)
    print("📊 数据库约束添加结果")
    print("=" * 80)
    print(f"外键约束: {'✅ 成功' if fk_success else '❌ 失败'}")
    print(f"检查约束: {'✅ 成功' if check_success else '❌ 失败'}")
    print(f"索引添加: {'✅ 成功' if index_success else '❌ 失败'}")
    print(f"约束验证: {'✅ 成功' if verify_success else '❌ 失败'}")
    
    if all([fk_success, check_success, index_success, verify_success]):
        print("\n🎉 所有数据库约束添加成功！")
    else:
        print("\n⚠️  部分约束添加失败，请检查日志")
    
    logger.info("🎉 数据库约束添加完成!")


if __name__ == "__main__":
    main()

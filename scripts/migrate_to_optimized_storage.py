#!/usr/bin/env python3
"""
数据存储优化迁移脚本
将双重存储模式迁移到优化存储模式（数据库存储元数据，文件系统存储实际文件）
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.database import SessionLocal
from backend.services.optimized_storage_service import OptimizedStorageService
from backend.models.project import Project
from backend.models.clip import Clip
from backend.models.collection import Collection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_current_storage():
    """分析当前存储状况"""
    logger.info("🔍 分析当前存储状况...")
    
    data_dir = project_root / "data"
    projects_dir = data_dir / "projects"
    
    if not projects_dir.exists():
        logger.warning("项目目录不存在")
        return {"projects": [], "total_size": 0}
    
    projects_info = []
    total_size = 0
    
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith('.'):
            project_id = project_dir.name
            project_size = sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file())
            
            # 检查是否有重复数据
            has_duplicate_data = False
            if (project_dir / "clips_metadata.json").exists():
                has_duplicate_data = True
            
            projects_info.append({
                "project_id": project_id,
                "size_mb": round(project_size / (1024 * 1024), 2),
                "has_duplicate_data": has_duplicate_data,
                "files_count": len(list(project_dir.rglob('*')))
            })
            
            total_size += project_size
    
    logger.info(f"📊 分析完成: {len(projects_info)} 个项目, 总大小: {round(total_size / (1024 * 1024), 2)} MB")
    
    return {
        "projects": projects_info,
        "total_size": total_size
    }


def migrate_project_to_optimized_storage(db, project_id: str, dry_run: bool = True):
    """迁移单个项目到优化存储模式"""
    logger.info(f"🔄 迁移项目: {project_id} (dry_run={dry_run})")
    
    try:
        # 获取项目信息
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.warning(f"项目 {project_id} 在数据库中不存在")
            return {"success": False, "error": "项目不存在"}
        
        # 检查项目目录
        data_dir = project_root / "data"
        old_project_dir = data_dir / "projects" / project_id
        
        if not old_project_dir.exists():
            logger.warning(f"项目目录不存在: {old_project_dir}")
            return {"success": False, "error": "项目目录不存在"}
        
        if dry_run:
            logger.info(f"🔍 模拟迁移项目 {project_id}")
            return {"success": True, "dry_run": True, "message": "模拟迁移成功"}
        
        # 创建优化存储服务
        storage_service = OptimizedStorageService(db, project_id)
        
        # 执行迁移
        migration_result = storage_service.migrate_from_old_storage(old_project_dir)
        
        if migration_result["success"]:
            logger.info(f"✅ 项目 {project_id} 迁移成功")
            
            # 清理旧的双重存储文件
            cleanup_old_duplicate_files(old_project_dir)
            
            return {
                "success": True,
                "migrated_files": migration_result["migrated_files"],
                "migrated_metadata": migration_result["migrated_metadata"]
            }
        else:
            logger.error(f"❌ 项目 {project_id} 迁移失败: {migration_result['error']}")
            return migration_result
            
    except Exception as e:
        logger.error(f"❌ 迁移项目 {project_id} 时发生错误: {e}")
        return {"success": False, "error": str(e)}


def cleanup_old_duplicate_files(project_dir: Path):
    """清理旧的双重存储文件"""
    try:
        logger.info(f"🧹 清理项目 {project_dir.name} 的重复文件...")
        
        # 删除重复的元数据文件
        duplicate_files = [
            "clips_metadata.json",
            "collections_metadata.json",
            "step1_outline.json",
            "step2_timeline.json",
            "step3_scoring.json",
            "step4_titles.json",
            "step5_collections.json"
        ]
        
        cleaned_count = 0
        for file_name in duplicate_files:
            file_path = project_dir / file_name
            if file_path.exists():
                # 备份文件
                backup_path = project_dir / f"{file_name}.backup"
                file_path.rename(backup_path)
                cleaned_count += 1
                logger.info(f"📦 备份重复文件: {file_name}")
        
        logger.info(f"✅ 清理完成，备份了 {cleaned_count} 个重复文件")
        
    except Exception as e:
        logger.error(f"❌ 清理重复文件失败: {e}")


def main():
    """主函数"""
    logger.info("🚀 开始数据存储优化迁移...")
    
    # 分析当前存储状况
    storage_info = analyze_current_storage()
    
    if not storage_info["projects"]:
        logger.info("📭 没有找到需要迁移的项目")
        return
    
    # 显示分析结果
    print("\n📊 当前存储状况分析:")
    print("=" * 60)
    for project in storage_info["projects"]:
        status = "⚠️  有重复数据" if project["has_duplicate_data"] else "✅ 正常"
        print(f"项目 {project['project_id'][:8]}... | {project['size_mb']:>8.2f} MB | {project['files_count']:>4} 文件 | {status}")
    
    print(f"\n总大小: {round(storage_info['total_size'] / (1024 * 1024), 2)} MB")
    
    # 询问是否继续
    print("\n" + "=" * 60)
    print("🔧 迁移选项:")
    print("1. 模拟迁移 (dry run) - 查看迁移效果但不实际执行")
    print("2. 执行迁移 - 实际迁移数据并清理重复文件")
    print("3. 退出")
    
    while True:
        choice = input("\n请选择操作 (1/2/3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("❌ 无效选择，请输入 1、2 或 3")
    
    if choice == '3':
        logger.info("👋 用户取消迁移")
        return
    
    dry_run = (choice == '1')
    
    if dry_run:
        logger.info("🔍 开始模拟迁移...")
    else:
        logger.info("🚀 开始实际迁移...")
        # 创建备份
        backup_dir = project_root / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)
        logger.info(f"📦 创建备份目录: {backup_dir}")
    
    # 执行迁移
    db = SessionLocal()
    try:
        success_count = 0
        failed_count = 0
        
        for project_info in storage_info["projects"]:
            project_id = project_info["project_id"]
            
            result = migrate_project_to_optimized_storage(db, project_id, dry_run)
            
            if result["success"]:
                success_count += 1
                if dry_run:
                    logger.info(f"✅ 模拟迁移成功: {project_id}")
                else:
                    logger.info(f"✅ 迁移成功: {project_id}")
            else:
                failed_count += 1
                logger.error(f"❌ 迁移失败: {project_id} - {result.get('error', '未知错误')}")
        
        # 显示迁移结果
        print("\n" + "=" * 60)
        print("📊 迁移结果:")
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {failed_count}")
        print(f"📊 总计: {success_count + failed_count}")
        
        if not dry_run and success_count > 0:
            print(f"\n💾 备份位置: {backup_dir}")
            print("🔧 建议:")
            print("1. 测试系统功能是否正常")
            print("2. 确认无误后可以删除备份文件")
            print("3. 运行数据一致性检查")
        
    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {e}")
    finally:
        db.close()
    
    logger.info("🎉 迁移完成!")


if __name__ == "__main__":
    main()

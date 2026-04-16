#!/usr/bin/env python3
"""
数据一致性检查和清理脚本
检查并修复数据库与文件系统之间的不一致问题
"""

import sys
import os
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
from backend.core.database import SessionLocal
from backend.models.project import Project
from backend.models.task import Task, TaskStatus
from backend.models.clip import Clip
from backend.models.collection import Collection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataConsistencyChecker:
    """数据一致性检查器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(project_root / "data" / "autoclip.db")
        self.data_dir = project_root / "data"
        self.projects_dir = self.data_dir / "projects"
        
    def check_consistency(self) -> Dict[str, Any]:
        """检查数据一致性"""
        logger.info("🔍 开始数据一致性检查...")
        
        issues = []
        warnings = []
        
        # 1. 检查项目数据一致性
        project_issues = self._check_project_consistency()
        issues.extend(project_issues)
        
        # 2. 检查任务数据一致性
        task_issues = self._check_task_consistency()
        issues.extend(task_issues)
        
        # 3. 检查文件系统一致性
        file_issues = self._check_filesystem_consistency()
        issues.extend(file_issues)
        
        # 4. 检查孤立数据
        orphaned_data = self._check_orphaned_data()
        warnings.extend(orphaned_data)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "total_warnings": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "status": "healthy" if len(issues) == 0 else "unhealthy"
        }
    
    def _check_project_consistency(self) -> List[Dict[str, Any]]:
        """检查项目数据一致性"""
        issues = []
        
        try:
            # 获取数据库中的项目
            db = SessionLocal()
            try:
                db_projects = db.query(Project).all()
                db_project_ids = {p.id for p in db_projects}
                
                # 获取文件系统中的项目目录
                fs_project_ids = set()
                if self.projects_dir.exists():
                    for project_dir in self.projects_dir.iterdir():
                        if project_dir.is_dir() and not project_dir.name.startswith('.'):
                            fs_project_ids.add(project_dir.name)
                
                # 检查孤立文件
                orphaned_files = fs_project_ids - db_project_ids
                if orphaned_files:
                    issues.append({
                        "type": "orphaned_files",
                        "severity": "warning",
                        "message": f"发现 {len(orphaned_files)} 个孤立项目文件",
                        "details": list(orphaned_files)
                    })
                
                # 检查缺失文件
                missing_files = db_project_ids - fs_project_ids
                if missing_files:
                    issues.append({
                        "type": "missing_files",
                        "severity": "error",
                        "message": f"发现 {len(missing_files)} 个项目的文件缺失",
                        "details": list(missing_files)
                    })
                
                # 检查异常项目目录
                if (self.projects_dir / "None").exists():
                    issues.append({
                        "type": "invalid_directory",
                        "severity": "warning",
                        "message": "发现无效的项目目录 'None'",
                        "details": ["None"]
                    })
                
            finally:
                db.close()
                
        except Exception as e:
            issues.append({
                "type": "check_error",
                "severity": "error",
                "message": f"检查项目一致性时发生错误: {str(e)}",
                "details": []
            })
        
        return issues
    
    def _check_task_consistency(self) -> List[Dict[str, Any]]:
        """检查任务数据一致性"""
        issues = []
        
        try:
            db = SessionLocal()
            try:
                # 检查长时间运行的异常任务
                from datetime import timedelta
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                long_running_tasks = db.query(Task).filter(
                    Task.status == TaskStatus.RUNNING,
                    Task.created_at < cutoff_time
                ).all()
                
                if long_running_tasks:
                    issues.append({
                        "type": "long_running_tasks",
                        "severity": "warning",
                        "message": f"发现 {len(long_running_tasks)} 个长时间运行的任务",
                        "details": [{"id": t.id, "name": t.name, "created_at": t.created_at.isoformat()} for t in long_running_tasks]
                    })
                
                # 检查孤立任务
                all_tasks = db.query(Task).all()
                all_project_ids = {p.id for p in db.query(Project).all()}
                
                orphaned_tasks = []
                for task in all_tasks:
                    if task.project_id not in all_project_ids:
                        orphaned_tasks.append(task)
                
                if orphaned_tasks:
                    issues.append({
                        "type": "orphaned_tasks",
                        "severity": "error",
                        "message": f"发现 {len(orphaned_tasks)} 个孤立任务",
                        "details": [{"id": t.id, "name": t.name, "project_id": t.project_id} for t in orphaned_tasks]
                    })
                
            finally:
                db.close()
                
        except Exception as e:
            issues.append({
                "type": "check_error",
                "severity": "error",
                "message": f"检查任务一致性时发生错误: {str(e)}",
                "details": []
            })
        
        return issues
    
    def _check_filesystem_consistency(self) -> List[Dict[str, Any]]:
        """检查文件系统一致性"""
        issues = []
        
        try:
            # 检查项目目录结构
            if self.projects_dir.exists():
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir() and not project_dir.name.startswith('.'):
                        # 检查必要的目录结构
                        required_dirs = ["raw", "processing", "output"]
                        missing_dirs = []
                        
                        for req_dir in required_dirs:
                            if not (project_dir / req_dir).exists():
                                missing_dirs.append(req_dir)
                        
                        if missing_dirs:
                            issues.append({
                                "type": "missing_directories",
                                "severity": "warning",
                                "message": f"项目 {project_dir.name} 缺少目录: {', '.join(missing_dirs)}",
                                "details": {"project_id": project_dir.name, "missing_dirs": missing_dirs}
                            })
                        
                        # 检查重复的元数据文件
                        metadata_files = [
                            "clips_metadata.json",
                            "collections_metadata.json",
                            "step1_outline.json",
                            "step2_timeline.json",
                            "step3_scoring.json",
                            "step4_titles.json",
                            "step5_collections.json"
                        ]
                        
                        duplicate_files = []
                        for metadata_file in metadata_files:
                            if (project_dir / metadata_file).exists():
                                duplicate_files.append(metadata_file)
                        
                        if duplicate_files:
                            issues.append({
                                "type": "duplicate_metadata",
                                "severity": "info",
                                "message": f"项目 {project_dir.name} 存在重复元数据文件",
                                "details": {"project_id": project_dir.name, "duplicate_files": duplicate_files}
                            })
                
        except Exception as e:
            issues.append({
                "type": "check_error",
                "severity": "error",
                "message": f"检查文件系统一致性时发生错误: {str(e)}",
                "details": []
            })
        
        return issues
    
    def _check_orphaned_data(self) -> List[Dict[str, Any]]:
        """检查孤立数据"""
        warnings = []
        
        try:
            db = SessionLocal()
            try:
                # 检查孤立的切片数据
                all_clips = db.query(Clip).all()
                all_project_ids = {p.id for p in db.query(Project).all()}
                
                orphaned_clips = [clip for clip in all_clips if clip.project_id not in all_project_ids]
                if orphaned_clips:
                    warnings.append({
                        "type": "orphaned_clips",
                        "message": f"发现 {len(orphaned_clips)} 个孤立切片",
                        "count": len(orphaned_clips)
                    })
                
                # 检查孤立的合集数据
                all_collections = db.query(Collection).all()
                orphaned_collections = [col for col in all_collections if col.project_id not in all_project_ids]
                if orphaned_collections:
                    warnings.append({
                        "type": "orphaned_collections",
                        "message": f"发现 {len(orphaned_collections)} 个孤立合集",
                        "count": len(orphaned_collections)
                    })
                
            finally:
                db.close()
                
        except Exception as e:
            warnings.append({
                "type": "check_error",
                "message": f"检查孤立数据时发生错误: {str(e)}"
            })
        
        return warnings
    
    def fix_issues(self, issues: List[Dict[str, Any]], dry_run: bool = True) -> Dict[str, Any]:
        """修复发现的问题"""
        logger.info(f"🔧 开始修复问题 (dry_run={dry_run})")
        
        fixed_count = 0
        failed_count = 0
        fix_results = []
        
        for issue in issues:
            try:
                if issue["type"] == "orphaned_files":
                    result = self._fix_orphaned_files(issue["details"], dry_run)
                    fix_results.append(result)
                    if result["success"]:
                        fixed_count += 1
                    else:
                        failed_count += 1
                
                elif issue["type"] == "long_running_tasks":
                    result = self._fix_long_running_tasks(issue["details"], dry_run)
                    fix_results.append(result)
                    if result["success"]:
                        fixed_count += 1
                    else:
                        failed_count += 1
                
                elif issue["type"] == "invalid_directory":
                    result = self._fix_invalid_directory(issue["details"], dry_run)
                    fix_results.append(result)
                    if result["success"]:
                        fixed_count += 1
                    else:
                        failed_count += 1
                
                else:
                    logger.warning(f"未知问题类型: {issue['type']}")
                    
            except Exception as e:
                logger.error(f"修复问题失败: {issue['type']}, 错误: {e}")
                failed_count += 1
        
        return {
            "fixed_count": fixed_count,
            "failed_count": failed_count,
            "fix_results": fix_results,
            "dry_run": dry_run
        }
    
    def _fix_orphaned_files(self, orphaned_files: List[str], dry_run: bool) -> Dict[str, Any]:
        """修复孤立文件"""
        try:
            if dry_run:
                logger.info(f"🔍 模拟清理孤立文件: {orphaned_files}")
                return {"success": True, "action": "dry_run", "files": orphaned_files}
            
            cleaned_count = 0
            for project_id in orphaned_files:
                project_dir = self.projects_dir / project_id
                if project_dir.exists():
                    shutil.rmtree(project_dir)
                    cleaned_count += 1
                    logger.info(f"✅ 清理孤立项目目录: {project_id}")
            
            return {"success": True, "action": "cleanup", "cleaned_count": cleaned_count}
            
        except Exception as e:
            logger.error(f"清理孤立文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _fix_long_running_tasks(self, long_running_tasks: List[Dict], dry_run: bool) -> Dict[str, Any]:
        """修复长时间运行的任务"""
        try:
            if dry_run:
                logger.info(f"🔍 模拟修复长时间运行任务: {len(long_running_tasks)} 个")
                return {"success": True, "action": "dry_run", "tasks": long_running_tasks}
            
            db = SessionLocal()
            try:
                fixed_count = 0
                for task_info in long_running_tasks:
                    task_id = task_info["id"]
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = "任务超时，已自动标记为失败"
                        task.updated_at = datetime.utcnow()
                        fixed_count += 1
                        logger.info(f"✅ 修复长时间运行任务: {task_id}")
                
                db.commit()
                return {"success": True, "action": "fix", "fixed_count": fixed_count}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"修复长时间运行任务失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _fix_invalid_directory(self, invalid_dirs: List[str], dry_run: bool) -> Dict[str, Any]:
        """修复无效目录"""
        try:
            if dry_run:
                logger.info(f"🔍 模拟清理无效目录: {invalid_dirs}")
                return {"success": True, "action": "dry_run", "dirs": invalid_dirs}
            
            cleaned_count = 0
            for dir_name in invalid_dirs:
                invalid_dir = self.projects_dir / dir_name
                if invalid_dir.exists():
                    shutil.rmtree(invalid_dir)
                    cleaned_count += 1
                    logger.info(f"✅ 清理无效目录: {dir_name}")
            
            return {"success": True, "action": "cleanup", "cleaned_count": cleaned_count}
            
        except Exception as e:
            logger.error(f"清理无效目录失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数"""
    logger.info("🚀 开始数据一致性检查和修复...")
    
    checker = DataConsistencyChecker()
    
    # 1. 检查数据一致性
    result = checker.check_consistency()
    
    print("\n" + "=" * 80)
    print("📊 数据一致性检查结果")
    print("=" * 80)
    print(f"检查时间: {result['timestamp']}")
    print(f"总问题数: {result['total_issues']}")
    print(f"总警告数: {result['total_warnings']}")
    print(f"状态: {result['status']}")
    
    if result['issues']:
        print("\n🚨 发现的问题:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"{i}. [{issue['severity'].upper()}] {issue['message']}")
            if issue.get('details'):
                print(f"   详情: {issue['details']}")
    
    if result['warnings']:
        print("\n⚠️  警告:")
        for i, warning in enumerate(result['warnings'], 1):
            print(f"{i}. {warning['message']}")
    
    # 2. 如果有问题，询问是否修复
    if result['total_issues'] > 0:
        print("\n" + "=" * 60)
        print("🔧 修复选项:")
        print("1. 模拟修复 (dry run) - 查看修复效果但不实际执行")
        print("2. 执行修复 - 实际修复发现的问题")
        print("3. 退出")
        
        while True:
            choice = input("\n请选择操作 (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                break
            print("❌ 无效选择，请输入 1、2 或 3")
        
        if choice == '3':
            logger.info("👋 用户取消修复")
            return
        
        dry_run = (choice == '1')
        
        # 执行修复
        fix_result = checker.fix_issues(result['issues'], dry_run)
        
        print("\n" + "=" * 60)
        if dry_run:
            print("🔍 模拟修复结果:")
        else:
            print("✅ 修复完成:")
        
        print(f"修复成功: {fix_result['fixed_count']}")
        print(f"修复失败: {fix_result['failed_count']}")
        
        if fix_result['fix_results']:
            print("\n📋 修复详情:")
            for i, fix_result_item in enumerate(fix_result['fix_results'], 1):
                status = "✅" if fix_result_item['success'] else "❌"
                print(f"{i}. {status} {fix_result_item.get('action', 'unknown')}")
                if not fix_result_item['success']:
                    print(f"   错误: {fix_result_item.get('error', 'unknown')}")
    
    else:
        print("\n🎉 数据一致性检查通过，无需修复！")
    
    logger.info("🎉 数据一致性检查和修复完成!")


if __name__ == "__main__":
    main()

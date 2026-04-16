"""
Celery应用配置
任务队列配置和初始化
"""

import os
from celery import Celery
from celery.schedules import crontab

from pathlib import Path


def _to_bool(value: object, default: bool = False) -> bool:
    """Convert common env-style values to bool."""
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _read_local_env() -> dict[str, str]:
    """Read simple KEY=VALUE pairs from the repo .env file."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")

    return values

# 设置默认配置模块
# os.environ.setdefault('CELERY_CONFIG_MODULE', 'backend.core.celery_app')

# 创建Celery应用
celery_app = Celery('autoclip')

LOCAL_ENV = _read_local_env()

DEBUG_MODE = _to_bool(os.getenv('DEBUG'), default=_to_bool(LOCAL_ENV.get('DEBUG'), True))
DEFAULT_REDIS_URL = os.getenv('REDIS_URL') or LOCAL_ENV.get('REDIS_URL') or 'redis://localhost:6379/0'
LOCAL_EAGER_MODE = _to_bool(os.getenv('CELERY_ALWAYS_EAGER'), default=DEBUG_MODE)

# 配置Celery
class CeleryConfig:
    """Celery配置类"""
    
    # 任务序列化格式
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'Asia/Shanghai'
    enable_utc = True
    
    # Redis配置
    broker_url = 'memory://' if LOCAL_EAGER_MODE else DEFAULT_REDIS_URL
    result_backend = 'cache+memory://' if LOCAL_EAGER_MODE else DEFAULT_REDIS_URL
    
    # 任务配置
    task_always_eager = LOCAL_EAGER_MODE
    task_eager_propagates = True
    task_store_eager_result = LOCAL_EAGER_MODE
    
    # 工作进程配置
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = True
    
    # 任务路由
    task_routes = {
        'backend.tasks.processing.*': {'queue': 'processing'},
        'backend.tasks.video.*': {'queue': 'video'},
        'backend.tasks.notification.*': {'queue': 'notification'},
        'backend.tasks.upload.*': {'queue': 'upload'},  # 添加upload任务路由
        'backend.tasks.import_processing.*': {'queue': 'processing'},  # 导入任务路由
    }
    
    # 定时任务配置
    beat_schedule = {
        'cleanup-expired-tasks': {
            'task': 'backend.tasks.maintenance.cleanup_expired_tasks',
            'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
        },
        'health-check': {
            'task': 'backend.tasks.maintenance.health_check',
            'schedule': crontab(minute='*/5'),  # 每5分钟
        },
    }
    
    # 结果配置
    result_expires = 3600  # 1小时
    task_ignore_result = False
    
    # 日志配置
    worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
    worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'

# 应用配置
celery_app.config_from_object(CeleryConfig)

# 自动发现任务
celery_app.autodiscover_tasks([
    'backend.tasks.processing',
    'backend.tasks.video', 
    'backend.tasks.notification',
    'backend.tasks.maintenance',
    'backend.tasks.import_processing'  # 添加导入处理任务
])

if __name__ == '__main__':
    celery_app.start()

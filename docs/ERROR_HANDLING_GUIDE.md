# 统一错误处理指南

## 📋 概述

本项目已实现统一的错误处理机制，提供一致的错误响应格式和自动错误处理功能。

## 🏗️ 错误处理架构

### 错误分类

```python
class ErrorCategory(Enum):
    CONFIGURATION = "CONFIGURATION"  # 配置错误
    NETWORK = "NETWORK"              # 网络错误
    API = "API"                      # API错误
    FILE_IO = "FILE_IO"              # 文件IO错误
    PROCESSING = "PROCESSING"        # 处理错误
    VALIDATION = "VALIDATION"        # 验证错误
    SYSTEM = "SYSTEM"                # 系统错误
```

### 错误级别

```python
class ErrorLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
```

## 🚀 使用方法

### 1. 抛出自定义异常

```python
from backend.utils.error_handler import AutoClipsException, ErrorCategory

# 抛出配置错误
raise AutoClipsException(
    message="API密钥未配置",
    category=ErrorCategory.CONFIGURATION,
    details={"config_key": "DASHSCOPE_API_KEY"}
)

# 抛出文件错误
raise AutoClipsException(
    message="文件不存在",
    category=ErrorCategory.FILE_IO,
    details={"file_path": "/path/to/file.mp4"}
)
```

### 2. 使用错误处理装饰器

```python
from backend.core.error_middleware import handle_errors
from backend.utils.error_handler import ErrorCategory

@handle_errors(ErrorCategory.PROCESSING)
async def process_video(video_path: str):
    # 函数内的任何异常都会被自动转换为AutoClipsException
    if not os.path.exists(video_path):
        raise FileNotFoundError("视频文件不存在")
    
    # 处理逻辑...
    return result
```

### 3. 使用错误上下文管理器

```python
from backend.core.error_middleware import error_context
from backend.utils.error_handler import ErrorCategory

def upload_file(file_path: str):
    with error_context(ErrorCategory.FILE_IO, {"file_path": file_path}):
        # 在这个上下文中抛出的任何异常都会被转换为AutoClipsException
        with open(file_path, 'r') as f:
            content = f.read()
        return content
```

### 4. 在API路由中使用

```python
from fastapi import APIRouter, HTTPException
from backend.utils.error_handler import AutoClipsException, ErrorCategory

router = APIRouter()

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    try:
        # 业务逻辑
        project = await get_project_from_db(project_id)
        if not project:
            raise AutoClipsException(
                message=f"项目不存在: {project_id}",
                category=ErrorCategory.VALIDATION,
                details={"project_id": project_id}
            )
        return project
    except AutoClipsException:
        # 重新抛出，让全局异常处理器处理
        raise
    except Exception as e:
        # 其他异常会被转换为AutoClipsException
        raise AutoClipsException(
            message="获取项目失败",
            category=ErrorCategory.SYSTEM,
            original_exception=e
        )
```

## 📊 错误响应格式

所有错误响应都遵循统一格式：

```json
{
  "error": {
    "code": "AUTOCLIPS_VALIDATION",
    "message": "项目不存在: abc123",
    "details": {
      "project_id": "abc123"
    },
    "request_id": "req_123456",
    "timestamp": 1640995200.0
  }
}
```

### 字段说明

- `code`: 错误代码，格式为 `AUTOCLIPS_{CATEGORY}` 或 `HTTP_{STATUS_CODE}`
- `message`: 错误消息，用户友好的描述
- `details`: 错误详情，包含调试信息
- `request_id`: 请求ID，用于追踪
- `timestamp`: 错误发生时间戳

## 🔧 HTTP状态码映射

| 错误分类 | HTTP状态码 | 说明 |
|---------|-----------|------|
| CONFIGURATION | 500 | 配置错误 |
| NETWORK | 503 | 网络错误 |
| API | 502 | API错误 |
| FILE_IO | 500 | 文件IO错误 |
| PROCESSING | 500 | 处理错误 |
| VALIDATION | 400 | 验证错误 |
| SYSTEM | 500 | 系统错误 |

## 📝 最佳实践

### 1. 错误消息编写

```python
# ✅ 好的错误消息
raise AutoClipsException(
    message="视频文件格式不支持，请使用MP4格式",
    category=ErrorCategory.VALIDATION,
    details={"supported_formats": ["mp4", "avi", "mov"]}
)

# ❌ 不好的错误消息
raise AutoClipsException(
    message="Error: Invalid file",
    category=ErrorCategory.VALIDATION
)
```

### 2. 错误详情包含

```python
# ✅ 包含有用的调试信息
raise AutoClipsException(
    message="处理视频失败",
    category=ErrorCategory.PROCESSING,
    details={
        "project_id": project_id,
        "step": "video_cutting",
        "error_code": "FFMPEG_ERROR",
        "file_size": file_size
    }
)
```

### 3. 错误分类选择

```python
# ✅ 根据错误性质选择正确的分类
if not api_key:
    raise AutoClipsException(
        message="API密钥未配置",
        category=ErrorCategory.CONFIGURATION  # 配置问题
    )

if response.status_code == 429:
    raise AutoClipsException(
        message="API调用频率超限",
        category=ErrorCategory.API  # API问题
    )

if not os.path.exists(file_path):
    raise AutoClipsException(
        message="文件不存在",
        category=ErrorCategory.FILE_IO  # 文件问题
    )
```

### 4. 异常链保持

```python
# ✅ 保持原始异常信息
try:
    result = some_risky_operation()
except Exception as e:
    raise AutoClipsException(
        message="操作失败",
        category=ErrorCategory.SYSTEM,
        original_exception=e  # 保持原始异常
    )
```

## 🧪 测试错误处理

### 1. 测试自定义异常

```python
import pytest
from backend.utils.error_handler import AutoClipsException, ErrorCategory

def test_custom_exception():
    with pytest.raises(AutoClipsException) as exc_info:
        raise AutoClipsException(
            message="测试错误",
            category=ErrorCategory.VALIDATION
        )
    
    assert exc_info.value.category == ErrorCategory.VALIDATION
    assert exc_info.value.message == "测试错误"
```

### 2. 测试API错误响应

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_error_response():
    response = client.get("/api/v1/projects/nonexistent")
    
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "AUTOCLIPS_VALIDATION"
```

## 🔍 错误监控和日志

### 1. 错误日志格式

所有错误都会自动记录到日志，格式如下：

```
2024-01-01 12:00:00 - ERROR - 未处理的异常: AutoClipsException: 项目不存在: abc123
request_id: req_123456
path: /api/v1/projects/abc123
method: GET
traceback: [完整的堆栈跟踪]
```

### 2. 错误统计

可以通过日志分析工具统计错误：

```bash
# 统计错误类型
grep "AUTOCLIPS_" backend.log | cut -d' ' -f4 | sort | uniq -c

# 统计错误频率
grep "ERROR" backend.log | wc -l
```

## 🚨 常见错误处理场景

### 1. 文件操作错误

```python
@handle_errors(ErrorCategory.FILE_IO)
async def save_file(file_path: str, content: bytes):
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
    except PermissionError:
        raise AutoClipsException(
            message="没有文件写入权限",
            category=ErrorCategory.FILE_IO,
            details={"file_path": file_path}
        )
    except OSError as e:
        raise AutoClipsException(
            message="文件系统错误",
            category=ErrorCategory.FILE_IO,
            details={"file_path": file_path, "os_error": str(e)}
        )
```

### 2. API调用错误

```python
@handle_errors(ErrorCategory.API)
async def call_external_api(url: str, data: dict):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 429:
                    raise AutoClipsException(
                        message="API调用频率超限",
                        category=ErrorCategory.API,
                        details={"url": url, "status": 429}
                    )
                return await response.json()
    except aiohttp.ClientError as e:
        raise AutoClipsException(
            message="网络请求失败",
            category=ErrorCategory.NETWORK,
            details={"url": url, "error": str(e)}
        )
```

### 3. 数据处理错误

```python
@handle_errors(ErrorCategory.PROCESSING)
async def process_video_data(video_path: str):
    try:
        # 处理逻辑
        result = await video_processor.process(video_path)
        return result
    except VideoProcessingError as e:
        raise AutoClipsException(
            message="视频处理失败",
            category=ErrorCategory.PROCESSING,
            details={
                "video_path": video_path,
                "error_code": e.code,
                "step": e.step
            },
            original_exception=e
        )
```

## 📚 相关文档

- [API文档](./API_DOCUMENTATION.md)
- [配置管理指南](./CONFIGURATION_GUIDE.md)
- [日志管理指南](./LOGGING_GUIDE.md)

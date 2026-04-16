"""Safe Celery task submission helpers."""

import logging
from typing import Any, Dict


logger = logging.getLogger(__name__)


def submit_video_pipeline_task(
    project_id: str,
    input_video_path: str,
    input_srt_path: str,
) -> Dict[str, Any]:
    """Submit the full video processing task."""
    try:
        from ..tasks.processing import process_video_pipeline

        logger.info("Submitting video pipeline task for project %s", project_id)
        celery_task = process_video_pipeline.delay(
            project_id=project_id,
            input_video_path=input_video_path,
            input_srt_path=input_srt_path,
        )
        return {
            "success": True,
            "task_id": celery_task.id,
            "status": getattr(celery_task, "state", "PENDING"),
            "message": "Video pipeline task submitted",
        }
    except Exception as exc:
        logger.exception(
            "Failed to submit video pipeline task for project %s", project_id
        )
        return {
            "success": False,
            "error": str(exc),
            "message": "Task submission failed",
        }


def submit_single_step_task(
    project_id: str,
    step: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Submit a single processing step task."""
    try:
        from ..tasks.processing import process_single_step

        logger.info(
            "Submitting single-step task for project %s, step %s",
            project_id,
            step,
        )
        celery_task = process_single_step.delay(
            project_id=project_id,
            step=step,
            config=config,
        )
        return {
            "success": True,
            "task_id": celery_task.id,
            "step": step,
            "status": getattr(celery_task, "state", "PENDING"),
            "message": f"Step {step} task submitted",
        }
    except Exception as exc:
        logger.exception(
            "Failed to submit single-step task for project %s, step %s",
            project_id,
            step,
        )
        return {
            "success": False,
            "error": str(exc),
            "message": "Task submission failed",
        }

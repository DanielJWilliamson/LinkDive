"""
Background Processing API endpoints for Link Dive AI
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel

from app.services.background_processing_service import (
    background_processing_service,
    BackgroundTask,
    TaskType,
    TaskStatus
)

router = APIRouter(prefix="/api/background", tags=["background-processing"])

class TaskRequest(BaseModel):
    """Request model for creating background tasks"""
    task_type: str
    campaign_id: Optional[int] = None
    parameters: dict = {}

class TaskResponse(BaseModel):
    """Response model for task status"""
    id: str
    task_type: str
    status: str
    campaign_id: Optional[int]
    progress: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_duration_minutes: Optional[int]
    error_message: Optional[str]

@router.post("/tasks", response_model=dict)
async def create_background_task(
    task_request: TaskRequest,
    user_email: str = Query(..., description="User email for authentication")
):
    """Create a new background task"""
    try:
        # Validate task type
        try:
            task_type = TaskType(task_request.task_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid task type: {task_request.task_type}")
        
        # Estimate duration based on task type
        duration_estimates = {
            TaskType.CAMPAIGN_ANALYSIS: 10,
            TaskType.CONTENT_VERIFICATION: 15,
            TaskType.SCHEDULED_MONITORING: 5,
            TaskType.BATCH_UPDATE: 30
        }
        
        # Create task
        task = BackgroundTask(
            id=f"{task_type.value}-{task_request.campaign_id or 'batch'}-{int(__import__('time').time())}",
            task_type=task_type,
            campaign_id=task_request.campaign_id,
            user_email=user_email,
            parameters=task_request.parameters,
            estimated_duration_minutes=duration_estimates.get(task_type, 10)
        )
        
        # Schedule the task
        task_id = await background_processing_service.schedule_task(task)
        
        return {
            "task_id": task_id,
            "message": f"Background task {task_type.value} scheduled successfully",
            "estimated_duration_minutes": task.estimated_duration_minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create background task: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    user_email: str = Query(..., description="User email for authentication")
):
    """Get status of a specific background task"""
    task_status = background_processing_service.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify user has access to this task
    task = background_processing_service.tasks.get(task_id)
    if task and task.user_email != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return TaskResponse(**task_status)

@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    user_email: str = Query(..., description="User email for authentication")
):
    """Get result of a completed background task"""
    # Verify user has access to this task
    task = background_processing_service.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_email != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Task not completed. Current status: {task.status.value}")
    
    result = background_processing_service.get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task result not found")
    
    return result

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    user_email: str = Query(..., description="User email for authentication"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tasks to return")
):
    """List background tasks for a user"""
    try:
        # Convert status string to enum if provided
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Get filtered tasks
        tasks = background_processing_service.list_tasks(
            user_email=user_email,
            status=status_filter
        )
        
        # Apply limit
        tasks = tasks[:limit]
        
        return [TaskResponse(**task) for task in tasks]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    user_email: str = Query(..., description="User email for authentication")
):
    """Cancel a pending or running background task"""
    # Verify user has access to this task
    task = background_processing_service.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.user_email != user_email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await background_processing_service.cancel_task(task_id)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Task cannot be cancelled (may be completed or already cancelled)"
        )
    
    return {"message": "Task cancelled successfully"}

@router.post("/campaigns/{campaign_id}/analyze")
async def start_campaign_analysis(
    campaign_id: int,
    user_email: str = Query(..., description="User email for authentication"),
    analysis_depth: str = Query("standard", description="Analysis depth: quick, standard, or deep"),
    include_content_verification: bool = Query(False, description="Include content verification")
):
    """Start comprehensive campaign analysis as a background task"""
    try:
        # Create campaign analysis task
        task = BackgroundTask(
            id=f"analysis-{campaign_id}-{int(__import__('time').time())}",
            task_type=TaskType.CAMPAIGN_ANALYSIS,
            campaign_id=campaign_id,
            user_email=user_email,
            parameters={
                "analysis_depth": analysis_depth,
                "include_content_verification": include_content_verification
            },
            estimated_duration_minutes=15 if include_content_verification else 10
        )
        
        # Schedule the task
        task_id = await background_processing_service.schedule_task(task)
        
        return {
            "task_id": task_id,
            "message": f"Campaign analysis started for campaign {campaign_id}",
            "estimated_duration_minutes": task.estimated_duration_minutes,
            "analysis_depth": analysis_depth,
            "includes_content_verification": include_content_verification
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start campaign analysis: {str(e)}")

@router.post("/campaigns/{campaign_id}/verify-content")
async def start_content_verification(
    campaign_id: int,
    user_email: str = Query(..., description="User email for authentication"),
    urls: List[str] = []
):
    """Start content verification for specific URLs as a background task"""
    if not urls:
        raise HTTPException(status_code=400, detail="At least one URL must be provided")
    
    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs allowed per request")
    
    try:
        # Create content verification task
        task = BackgroundTask(
            id=f"verify-{campaign_id}-{int(__import__('time').time())}",
            task_type=TaskType.CONTENT_VERIFICATION,
            campaign_id=campaign_id,
            user_email=user_email,
            parameters={"urls": urls},
            estimated_duration_minutes=len(urls) // 3 + 1  # Rough estimate
        )
        
        # Schedule the task
        task_id = await background_processing_service.schedule_task(task)
        
        return {
            "task_id": task_id,
            "message": f"Content verification started for {len(urls)} URLs",
            "estimated_duration_minutes": task.estimated_duration_minutes,
            "urls_count": len(urls)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start content verification: {str(e)}")

@router.post("/batch-update")
async def start_batch_update(
    user_email: str = Query(..., description="User email for authentication"),
    campaign_ids: List[int] = []
):
    """Start batch update for multiple campaigns"""
    if not campaign_ids:
        raise HTTPException(status_code=400, detail="At least one campaign ID must be provided")
    
    if len(campaign_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 campaigns allowed per batch")
    
    try:
        # Create batch update task
        task = BackgroundTask(
            id=f"batch-{int(__import__('time').time())}",
            task_type=TaskType.BATCH_UPDATE,
            user_email=user_email,
            parameters={"campaign_ids": campaign_ids},
            estimated_duration_minutes=len(campaign_ids) * 2  # Rough estimate
        )
        
        # Schedule the task
        task_id = await background_processing_service.schedule_task(task)
        
        return {
            "task_id": task_id,
            "message": f"Batch update started for {len(campaign_ids)} campaigns",
            "estimated_duration_minutes": task.estimated_duration_minutes,
            "campaign_count": len(campaign_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch update: {str(e)}")

@router.get("/health")
async def background_service_health():
    """Check health status of background processing service"""
    try:
        worker_status = "running" if background_processing_service.worker_running else "stopped"
        
        # Get task statistics
        all_tasks = list(background_processing_service.tasks.values())
        total_tasks = len(all_tasks)
        
        task_stats = {
            "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in all_tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
            "cancelled": len([t for t in all_tasks if t.status == TaskStatus.CANCELLED])
        }
        
        return {
            "worker_status": worker_status,
            "total_tasks": total_tasks,
            "task_statistics": task_stats,
            "active_tasks": len(background_processing_service.active_tasks),
            "queue_size": background_processing_service.task_queue.qsize()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Startup handled by main application lifespan; legacy on_event removed.

"""Background Processing Service for Link Dive AI."""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum

from app.models.campaign import campaign_storage
from app.core.metrics import metrics
import zoneinfo
from app.services.campaign_analysis_service import campaign_analysis_service
from app.services.content_analysis_service import content_analysis_service
from app.services.external.dataforseo_client import dataforseo_client
from app.core.database import get_db
from app.database.repository import CampaignRepository
from app.utils.datetime_utils import utc_now, iso_utc_now

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    CAMPAIGN_ANALYSIS = "campaign_analysis"
    CONTENT_VERIFICATION = "content_verification"
    SCHEDULED_MONITORING = "scheduled_monitoring"
    BATCH_UPDATE = "batch_update"

@dataclass
class BackgroundTask:
    """Represents a background processing task"""
    id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    campaign_id: Optional[int] = None
    user_email: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    estimated_duration_minutes: Optional[int] = None

class BackgroundProcessingService:
    """Service for managing background tasks and automated processing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks = {}  # type: Dict[str, BackgroundTask]
        self.task_queue = asyncio.Queue()
        self.worker_running = False
        self.max_concurrent_tasks = 3
        self.active_tasks = {}  # type: Dict[str, asyncio.Task]
        self.last_scheduler_tick: Optional[datetime] = None
        self.window_tz = zoneinfo.ZoneInfo("Europe/London")
        
    async def start_worker(self):
        """Start the background task worker"""
        if self.worker_running:
            self.logger.warning("Background worker already running")
            return
            
        self.worker_running = True
        self.logger.info("Starting background processing worker")
        
        # Start worker coroutines
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_concurrent_tasks)
        ]
        
        # Start monitoring coroutine
        monitor_task = asyncio.create_task(self._monitor_scheduled_tasks())
        
        try:
            await asyncio.gather(*workers, monitor_task)
        except Exception as e:
            self.logger.error(f"Worker error: {str(e)}")
        finally:
            self.worker_running = False
    
    async def stop_worker(self):
        """Stop the background task worker"""
        self.worker_running = False
        self.logger.info("Stopping background processing worker")
        
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
    
    async def _worker(self, worker_name: str):
        """Background worker coroutine"""
        self.logger.info(f"Started worker: {worker_name}")
        
        while self.worker_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process the task
                await self._process_task(task, worker_name)
                
            except asyncio.TimeoutError:
                # No tasks available, continue
                continue
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {str(e)}")
                await asyncio.sleep(1)
        
        self.logger.info(f"Worker {worker_name} stopped")
    
    async def _process_task(self, task: BackgroundTask, worker_name: str):
        """Process a single background task"""
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        
        self.logger.info(f"Worker {worker_name} processing task {task.id} ({task.task_type.value})")
        
        try:
            # Route to appropriate handler
            if task.task_type == TaskType.CAMPAIGN_ANALYSIS:
                metrics.inc("tasks_started")
                result = await self._handle_campaign_analysis(task)
            elif task.task_type == TaskType.CONTENT_VERIFICATION:
                metrics.inc("tasks_started")
                result = await self._handle_content_verification(task)
            elif task.task_type == TaskType.SCHEDULED_MONITORING:
                metrics.inc("tasks_started")
                result = await self._handle_scheduled_monitoring(task)
            elif task.task_type == TaskType.BATCH_UPDATE:
                metrics.inc("tasks_started")
                result = await self._handle_batch_update(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            metrics.inc("tasks_completed")
            task.progress = 100.0
            
        except Exception as e:
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            metrics.inc("tasks_failed")
        
        finally:
            task.completed_at = utc_now()
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    async def _handle_campaign_analysis(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle campaign analysis task"""
        campaign_id = task.campaign_id
        user_email = task.user_email
        
        if not campaign_id or not user_email:
            raise ValueError("Campaign ID and user email required for campaign analysis")
        
        # Get campaign data
        campaign = campaign_storage.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Update progress
        task.progress = 10.0
        
        # Perform comprehensive analysis
        analysis_depth = task.parameters.get("analysis_depth", "standard")
        analysis_results = await campaign_analysis_service.analyze_campaign_comprehensive(
            campaign=campaign,
            analysis_depth=analysis_depth
        )
        
        task.progress = 70.0
        
        # If content verification is enabled, enhance with content analysis
        if task.parameters.get("include_content_verification", False):
            await self._enhance_with_content_verification(analysis_results, campaign, task)
        
        task.progress = 90.0
        
        # Store results in campaign storage (extend model if needed)
        # For now, just return the results
        return {
            "campaign_id": campaign_id,
            "analysis_results": analysis_results,
            "processed_at": iso_utc_now()
        }
    
    async def _handle_content_verification(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle content verification task"""
        urls = task.parameters.get("urls", [])
        campaign_id = task.campaign_id
        user_email = task.user_email
        
        if not urls or not campaign_id or not user_email:
            raise ValueError("URLs, campaign ID, and user email required for content verification")
        
        # Get campaign data
        campaign = campaign_storage.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        task.progress = 10.0
        
        # Perform content verification
        async with content_analysis_service:
            verification_results = await content_analysis_service.verify_campaign_coverage(
                backlink_urls=urls,
                verification_keywords=campaign.get("verification_keywords", []),
                campaign_details=campaign
            )
        
        task.progress = 90.0
        
        return {
            "campaign_id": campaign_id,
            "verification_results": verification_results,
            "processed_at": iso_utc_now()
        }
    
    async def _handle_scheduled_monitoring(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle scheduled monitoring task"""
        campaign_id = task.campaign_id
        user_email = task.user_email
        
        if not campaign_id or not user_email:
            raise ValueError("Campaign ID and user email required for scheduled monitoring")
        
        # Get campaign data
        campaign = campaign_storage.get_campaign_by_id(campaign_id, user_email)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        task.progress = 20.0
        
        # Perform incremental analysis (lighter than full analysis)
        analysis_results = await campaign_analysis_service.analyze_campaign_comprehensive(
            campaign=campaign,
            analysis_depth="quick"  # Faster for scheduled monitoring
        )
        
        task.progress = 80.0
        
        # Check for significant changes (placeholder logic)
        significant_changes = self._detect_significant_changes(analysis_results, campaign)
        
        task.progress = 90.0
        
        return {
            "campaign_id": campaign_id,
            "monitoring_results": analysis_results,
            "significant_changes": significant_changes,
            "processed_at": iso_utc_now()
        }
    
    async def _handle_batch_update(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle batch update task"""
        campaign_ids = task.parameters.get("campaign_ids", [])
        user_email = task.user_email
        
        if not campaign_ids or not user_email:
            raise ValueError("Campaign IDs and user email required for batch update")
        
        results = []
        total_campaigns = len(campaign_ids)
        
        for i, campaign_id in enumerate(campaign_ids):
            try:
                # Update progress
                task.progress = (i / total_campaigns) * 90
                
                campaign = campaign_storage.get_campaign_by_id(campaign_id, user_email)
                if not campaign:
                    results.append({
                        "campaign_id": campaign_id,
                        "status": "not_found",
                        "error": f"Campaign {campaign_id} not found"
                    })
                    continue
                
                # Perform quick analysis
                analysis_results = await campaign_analysis_service.analyze_campaign_comprehensive(
                    campaign=campaign,
                    analysis_depth="quick"
                )
                
                results.append({
                    "campaign_id": campaign_id,
                    "status": "completed",
                    "results": analysis_results
                })
                
            except Exception as e:
                self.logger.error(f"Batch update failed for campaign {campaign_id}: {str(e)}")
                results.append({
                    "campaign_id": campaign_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        task.progress = 90.0
        
        return {
            "batch_results": results,
            "processed_at": iso_utc_now(),
            "successful_updates": len([r for r in results if r["status"] == "completed"])
        }
    
    async def _enhance_with_content_verification(
        self, 
        analysis_results: Dict[str, Any], 
        campaign: Dict[str, Any], 
        task: BackgroundTask
    ):
        """Enhance analysis results with content verification"""
        try:
            # Extract URLs from analysis results
            all_urls = []
            for result in analysis_results.get("verified_coverage", []):
                all_urls.append(result["url"])
            for result in analysis_results.get("potential_coverage", []):
                all_urls.append(result["url"])
            
            if not all_urls:
                return
            
            # Limit URLs to prevent overwhelming the service
            urls_to_verify = all_urls[:20]  # Top 20 URLs
            
            # Perform content verification
            async with content_analysis_service:
                verification_results = await content_analysis_service.verify_campaign_coverage(
                    backlink_urls=urls_to_verify,
                    verification_keywords=campaign.get("verification_keywords", []),
                    campaign_details=campaign
                )
            
            # Update analysis results with content verification
            analysis_results["content_verification"] = verification_results
            
            task.progress = 85.0
            
        except Exception as e:
            self.logger.error(f"Content verification enhancement failed: {str(e)}")
            # Don't fail the entire task, just log the error
    
    def _detect_significant_changes(self, current_results: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect significant changes in campaign coverage
        In production, this would compare with previous results
        """
        # Placeholder implementation
        return {
            "new_verified_coverage": 0,
            "new_potential_coverage": 0,
            "lost_coverage": 0,
            "domain_rating_changes": [],
            "alert_triggered": False
        }
    
    async def _monitor_scheduled_tasks(self):
        """Monitor for campaigns that need scheduled analysis."""
        self.logger.info("Started scheduled task monitor")
        while self.worker_running:
            try:
                await asyncio.sleep(900)  # 15 minutes
                self.last_scheduler_tick = utc_now()
                metrics.mark("scheduler_last_tick")
                if not self._within_monitor_window():
                    metrics.inc("scheduler_window_skips")
                    continue
                campaigns_to_monitor = self._get_campaigns_for_monitoring()
                for campaign_data in campaigns_to_monitor:
                    task = BackgroundTask(
                        id=f"monitor-{campaign_data['id']}-{int(utc_now().timestamp())}",
                        task_type=TaskType.SCHEDULED_MONITORING,
                        campaign_id=campaign_data["id"],
                        user_email=campaign_data["user_email"],
                        estimated_duration_minutes=5
                    )
                    await self.schedule_task(task)
                    serp_keywords = campaign_data.get('serp_keywords', [])
                    if serp_keywords:
                        keyword = serp_keywords[0]
                        try:
                            serp_results = await dataforseo_client.fetch_serp(keyword, top_n=10)
                            db = next(get_db())
                            repo = CampaignRepository(db)
                            repo.ingest_serp_results(campaign_data['id'], campaign_data['user_email'], keyword, [
                                {'url': r.url, 'position': r.position, 'page_title': r.page_title}
                                for r in serp_results
                            ])
                            metrics.inc('serp_ingestions')
                        except Exception as se:
                            self.logger.error(f"SERP ingestion failed for campaign {campaign_data['id']}: {se}")
                self._auto_pause_expired_campaigns()
            except Exception as e:
                self.logger.error(f"Scheduled task monitor error: {str(e)}")
    
    def _get_campaigns_for_monitoring(self) -> List[Dict[str, Any]]:
        """Return active campaigns from in-memory storage (placeholder)."""
        if hasattr(campaign_storage, 'campaigns'):
            return [c for c in campaign_storage.campaigns if c.get('monitoring_status') == 'Live']
        return []

    def _within_monitor_window(self) -> bool:
        """Return True if current time is within 07:00–19:00 Europe/London Mon–Fri."""
        now = datetime.now(self.window_tz)
        if now.weekday() >= 5:  # Sat/Sun
            return False
        if now.hour < 7 or now.hour >= 19:
            return False
        return True

    def _auto_pause_expired_campaigns(self):
        """Auto-pause campaigns older than 365 days (placeholder using storage)."""
        try:
            campaigns = campaign_storage.list_campaigns() if hasattr(campaign_storage, 'list_campaigns') else []
            cutoff = utc_now() - timedelta(days=365)
            for c in campaigns:
                launch = c.get('launch_date')
                if not launch:
                    continue
                try:
                    if isinstance(launch, str):
                        launch_dt = datetime.fromisoformat(launch)
                    else:
                        launch_dt = launch
                except Exception:
                    continue
                if launch_dt < cutoff and c.get('monitoring_status') == 'Live':
                    c['monitoring_status'] = 'Paused'
                    metrics.inc('campaigns_auto_paused')
        except Exception as e:
            self.logger.error(f"Auto pause scan failed: {e}")
    
    async def schedule_task(self, task: BackgroundTask) -> str:
        """
        Schedule a background task for processing
        
        Returns:
            Task ID for tracking
        """
        # Store task
        self.tasks[task.id] = task
        
        # Add to queue
        await self.task_queue.put(task)
        
        self.logger.info(f"Scheduled task {task.id} ({task.task_type.value})")
        return task.id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a background task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "campaign_id": task.campaign_id,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "estimated_duration_minutes": task.estimated_duration_minutes,
            "error_message": task.error_message
        }
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a completed background task"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            return None
        
        return task.result
    
    def list_tasks(self, user_email: Optional[str] = None, status: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """List background tasks with optional filtering"""
        filtered_tasks = []
        
        for task in self.tasks.values():
            # Filter by user email if provided
            if user_email and task.user_email != user_email:
                continue
            
            # Filter by status if provided
            if status and task.status != status:
                continue
            
            filtered_tasks.append(self.get_task_status(task.id))
        
        # Sort by created_at descending
        filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return filtered_tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False  # Cannot cancel completed tasks
        
        # Cancel if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = utc_now()
        
        return True

# Global service instance
background_processing_service = BackgroundProcessingService()

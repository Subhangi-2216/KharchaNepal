"""
Celery configuration for Kharcha Nepal automated expense tracking.
"""
import os
from celery import Celery
from config import settings

# Create Celery instance
celery_app = Celery(
    "kharcha_nepal",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.email_processing.tasks",  # Email processing tasks
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "src.email_processing.tasks.process_email": {"queue": "email_processing"},
        "src.email_processing.tasks.sync_gmail_messages": {"queue": "email_sync"},
        "src.email_processing.tasks.extract_transaction_data": {"queue": "ocr_processing"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Periodic task settings
    beat_schedule={
        'cleanup-stuck-syncs': {
            'task': 'src.email_processing.tasks.cleanup_stuck_syncs',
            'schedule': 900.0,  # Run every 15 minutes
        },
        'collect-daily-statistics': {
            'task': 'src.email_processing.tasks.collect_daily_statistics',
            'schedule': 86400.0,  # Run once per day (24 hours)
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

if __name__ == "__main__":
    celery_app.start()

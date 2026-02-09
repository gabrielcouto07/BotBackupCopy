"""
Celery configuration for bot workers
"""
import os

# Broker and backend
broker_url = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
result_backend = os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Reliability
task_acks_late = True  # ACK after completing task
task_reject_on_worker_lost = True  # Requeue if worker crashes
worker_prefetch_multiplier = 1  # 1 task at a time (fair distribution)

# Retry
task_autoretry_for = (Exception,)
task_retry_backoff = True  # Exponential backoff
task_retry_backoff_max = 600  # Max 10 min
task_retry_jitter = True  # Randomization

# Timeouts
task_soft_time_limit = 3600  # 1 hour (soft)
task_time_limit = 3900  # 1h 5min (hard kill)

# Worker settings
worker_max_tasks_per_child = 50  # Recycle worker after 50 tasks
worker_send_task_events = True
task_send_sent_event = True

# Logging
worker_hijack_root_logger = False

# Result expiration
result_expires = 3600  # 1 hour

# Task routes (will be overridden dynamically by tenant)
task_default_queue = 'default'
task_queues = None  # Will be created dynamically

# Beat schedule for maintenance tasks
beat_schedule = {
    'cleanup-expired-locks': {
        'task': 'app.worker.tasks.cleanup_expired_locks',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-old-logs': {
        'task': 'app.worker.tasks.cleanup_old_logs',
        'schedule': 86400.0,  # Daily
    },
}

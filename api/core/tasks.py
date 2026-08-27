from logging import getLogger

from celery import shared_task

logger = getLogger(__name__)


@shared_task(ignore_result=True)
def celery_beat_heartbeat():
    """Lightweight operational proof that Celery Beat is dispatching tasks."""
    logger.info("event=celery_beat_heartbeat")

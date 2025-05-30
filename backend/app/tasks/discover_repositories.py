import logging

from app.celery_app import celery_app

# Set up logging
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run(self):
    task_id = self.request.id
    logger.info(f"Task {task_id} started: Discovering repositories")

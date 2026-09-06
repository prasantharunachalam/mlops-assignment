import asyncio
import logging
import random
from app.database import SessionLocal
from app.repositories import DeploymentRepository
from app.models import DeploymentStatus
from app.utils.logging import set_correlation_id

logger = logging.getLogger(__name__)


class DeploymentWorker:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True
        logger.info("Deployment worker started")
        while self.running:
            await self.process_deployments()
            await asyncio.sleep(2)

    def stop(self):
        self.running = False
        logger.info("Deployment worker stopped")

    async def process_deployments(self):
        db = SessionLocal()
        try:
            repo = DeploymentRepository(db)
            deployments = repo.get_requested_deployments(limit=5)

            for deployment in deployments:
                # Set correlation ID for distributed tracing
                if deployment.correlation_id:
                    set_correlation_id(deployment.correlation_id)

                logger.info(f"Processing deployment {deployment.id}")

                # Simulated deployment steps
                repo.update_status(deployment.id, DeploymentStatus.VALIDATING)
                await asyncio.sleep(0.5)

                repo.update_status(deployment.id, DeploymentStatus.DEPLOYING)
                await asyncio.sleep(1)

                # Simulate success/failure (95% success rate - realistic for production)
                if random.random() < 0.95:
                    repo.update_status(deployment.id, DeploymentStatus.SUCCEEDED)
                    logger.info(f"Deployment {deployment.id} succeeded")
                else:
                    repo.update_status(
                        deployment.id,
                        DeploymentStatus.FAILED,
                        failure_reason="Simulated deployment failure (network timeout/resource unavailable)"
                    )
                    logger.warning(f"Deployment {deployment.id} failed")

        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            db.close()

import asyncio
import logging
from app.worker.deployment_worker import DeploymentWorker
from app.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def main():
    worker = DeploymentWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

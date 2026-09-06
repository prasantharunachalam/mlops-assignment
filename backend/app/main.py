from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
from app.utils.logging import setup_logging, set_correlation_id
from app.api.v1 import models, deployments, monitoring, health

setup_logging()

app = FastAPI(
    title="MLOps Platform API",
    version="1.0.0",
    description="Model registry and deployment management platform",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Include routers
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(deployments.router, prefix="/api/v1", tags=["deployments"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
def root():
    return {"message": "MLOps Platform API", "version": "1.0.0"}

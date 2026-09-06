"""
Pytest configuration and fixtures for backend tests.

Provides database setup, FastAPI test client, and common fixtures
for testing the MLOps platform backend.
"""
import os
import uuid
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import Model, ModelVersion, Deployment

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Helper function to generate IDs
def generate_model_id() -> str:
    return f"model-{uuid.uuid4()}"

def generate_version_id() -> str:
    return f"ver-{uuid.uuid4()}"

def generate_deployment_id() -> str:
    return f"dep-{uuid.uuid4()}"

@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_model(db_session) -> Model:
    """Create a sample model for testing."""
    import uuid
    model = Model(
        id=f"model-{uuid.uuid4()}",
        name="test-fraud-detector",
        owner="test-user",
        description="Test fraud detection model"
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def sample_version(db_session, sample_model) -> ModelVersion:
    """Create a sample model version for testing."""
    import uuid
    version = ModelVersion(
        id=f"ver-{uuid.uuid4()}",
        model_id=sample_model.id,
        version_number="1.0.0",
        framework="scikit-learn",
        algorithm="RandomForest",
        artifact_uri="s3://models/fraud-detector/v1.0.0",
        training_data_ref="s3://data/fraud-training-20240101",
        lifecycle_stage="DRAFT",
        tags={"experiment_id": "exp-123", "accuracy": "0.95"}
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return version


@pytest.fixture
def approved_version(db_session, sample_model) -> ModelVersion:
    """Create an approved model version ready for deployment."""
    import uuid
    version = ModelVersion(
        id=f"ver-{uuid.uuid4()}",
        model_id=sample_model.id,
        version_number="2.0.0",
        framework="tensorflow",
        algorithm="NeuralNetwork",
        artifact_uri="s3://models/fraud-detector/v2.0.0",
        training_data_ref="s3://data/fraud-training-20240201",
        lifecycle_stage="APPROVED",
        tags={"experiment_id": "exp-456", "accuracy": "0.97"}
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return version


@pytest.fixture
def sample_deployment(db_session, approved_version) -> Deployment:
    """Create a sample deployment for testing."""
    import uuid
    deployment = Deployment(
        id=f"dep-{uuid.uuid4()}",
        model_version_id=approved_version.id,
        environment="STAGING",
        status="SUCCEEDED",
        idempotency_key="test-idempotency-key-123"
    )
    db_session.add(deployment)
    db_session.commit()
    db_session.refresh(deployment)
    return deployment

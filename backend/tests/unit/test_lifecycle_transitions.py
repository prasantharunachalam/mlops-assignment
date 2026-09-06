"""
Unit tests for model version lifecycle state transitions.

Tests the state machine defined in RegistryService.LIFECYCLE_TRANSITIONS
to ensure only valid transitions are allowed and invalid transitions are rejected.
"""
import pytest
from app.models import LifecycleStage
from app.services import RegistryService
from app.repositories import ModelRepository


class TestLifecycleTransitions:
    """Test lifecycle stage transitions in the model registry."""

    @pytest.fixture
    def registry_service(self, db_session):
        """Create a RegistryService instance for testing."""
        repo = ModelRepository(db_session)
        return RegistryService(repo)

    # Valid forward transitions
    def test_draft_to_validated_transition_succeeds(
        self, registry_service, sample_version, db_session
    ):
        """Test valid transition from DRAFT to VALIDATED."""
        assert sample_version.lifecycle_stage == LifecycleStage.DRAFT
        row_version = sample_version.row_version

        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.VALIDATED
        assert updated.row_version == row_version + 1

    def test_validated_to_approved_transition_succeeds(
        self, registry_service, sample_version, db_session
    ):
        """Test valid transition from VALIDATED to APPROVED."""
        # First promote to VALIDATED
        sample_version.lifecycle_stage = LifecycleStage.VALIDATED
        db_session.commit()
        db_session.refresh(sample_version)

        row_version = sample_version.row_version
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.APPROVED, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.APPROVED
        assert updated.row_version == row_version + 1

    def test_approved_to_staging_transition_succeeds(
        self, registry_service, approved_version
    ):
        """Test valid transition from APPROVED to STAGING."""
        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.STAGING, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.STAGING
        assert updated.row_version == row_version + 1

    def test_staging_to_production_transition_succeeds(
        self, registry_service, approved_version, db_session
    ):
        """Test valid transition from STAGING to PRODUCTION."""
        # First promote to STAGING
        approved_version.lifecycle_stage = LifecycleStage.STAGING
        db_session.commit()
        db_session.refresh(approved_version)

        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.PRODUCTION, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.PRODUCTION
        assert updated.row_version == row_version + 1

    def test_production_to_archived_transition_succeeds(
        self, registry_service, approved_version, db_session
    ):
        """Test valid transition from PRODUCTION to ARCHIVED."""
        # Promote to PRODUCTION first
        approved_version.lifecycle_stage = LifecycleStage.PRODUCTION
        db_session.commit()
        db_session.refresh(approved_version)

        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.ARCHIVED, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.ARCHIVED
        assert updated.row_version == row_version + 1

    # Valid backward transitions (rollback scenarios)
    def test_validated_to_draft_rollback_succeeds(
        self, registry_service, sample_version, db_session
    ):
        """Test valid rollback from VALIDATED to DRAFT."""
        sample_version.lifecycle_stage = LifecycleStage.VALIDATED
        db_session.commit()
        db_session.refresh(sample_version)

        row_version = sample_version.row_version
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.DRAFT, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.DRAFT

    def test_approved_to_validated_rollback_succeeds(
        self, registry_service, approved_version
    ):
        """Test valid rollback from APPROVED to VALIDATED."""
        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.VALIDATED, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.VALIDATED

    def test_staging_to_approved_rollback_succeeds(
        self, registry_service, approved_version, db_session
    ):
        """Test valid rollback from STAGING to APPROVED."""
        approved_version.lifecycle_stage = LifecycleStage.STAGING
        db_session.commit()
        db_session.refresh(approved_version)

        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.APPROVED, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.APPROVED

    def test_production_to_staging_rollback_succeeds(
        self, registry_service, approved_version, db_session
    ):
        """Test valid rollback from PRODUCTION to STAGING."""
        approved_version.lifecycle_stage = LifecycleStage.PRODUCTION
        db_session.commit()
        db_session.refresh(approved_version)

        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.STAGING, row_version
        )

        assert error is None
        assert updated is not None
        assert updated.lifecycle_stage == LifecycleStage.STAGING

    # Invalid transitions (skip stages)
    def test_draft_to_approved_skip_fails(self, registry_service, sample_version):
        """Test invalid transition that skips VALIDATED stage."""
        row_version = sample_version.row_version
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.APPROVED, row_version
        )

        assert updated is None
        assert error is not None
        assert "Invalid transition" in error
        assert "DRAFT" in error
        assert "APPROVED" in error

    def test_draft_to_production_skip_fails(self, registry_service, sample_version):
        """Test invalid transition from DRAFT directly to PRODUCTION."""
        row_version = sample_version.row_version
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.PRODUCTION, row_version
        )

        assert updated is None
        assert error is not None
        assert "Invalid transition" in error

    def test_validated_to_staging_skip_fails(
        self, registry_service, sample_version, db_session
    ):
        """Test invalid transition that skips APPROVED stage."""
        sample_version.lifecycle_stage = LifecycleStage.VALIDATED
        db_session.commit()
        db_session.refresh(sample_version)

        row_version = sample_version.row_version
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.STAGING, row_version
        )

        assert updated is None
        assert error is not None
        assert "Invalid transition" in error

    def test_approved_to_production_skip_fails(
        self, registry_service, approved_version
    ):
        """Test invalid transition that skips STAGING stage."""
        row_version = approved_version.row_version
        updated, error = registry_service.promote_lifecycle(
            approved_version.id, LifecycleStage.PRODUCTION, row_version
        )

        assert updated is None
        assert error is not None
        assert "Invalid transition" in error

    # Terminal state
    def test_archived_has_no_valid_transitions(
        self, registry_service, approved_version, db_session
    ):
        """Test that ARCHIVED is a terminal state with no valid transitions."""
        approved_version.lifecycle_stage = LifecycleStage.ARCHIVED
        db_session.commit()
        db_session.refresh(approved_version)

        row_version = approved_version.row_version

        # Try to transition to any other stage - all should fail
        for target_stage in LifecycleStage:
            if target_stage == LifecycleStage.ARCHIVED:
                continue

            updated, error = registry_service.promote_lifecycle(
                approved_version.id, target_stage, row_version
            )

            assert updated is None
            assert error is not None
            assert "Invalid transition" in error

    # Edge cases
    def test_promote_nonexistent_version_returns_not_found(self, registry_service):
        """Test promoting a version that doesn't exist."""
        updated, error = registry_service.promote_lifecycle(
            "nonexistent-version-id", LifecycleStage.VALIDATED, 1
        )

        assert updated is None
        assert error == "Version not found"

    def test_same_stage_transition_fails(self, registry_service, sample_version):
        """Test that transitioning to the same stage is not allowed."""
        row_version = sample_version.row_version
        current_stage = sample_version.lifecycle_stage

        updated, error = registry_service.promote_lifecycle(
            sample_version.id, current_stage, row_version
        )

        assert updated is None
        assert error is not None
        assert "Invalid transition" in error

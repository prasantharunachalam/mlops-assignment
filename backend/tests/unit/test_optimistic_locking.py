"""
Unit tests for optimistic locking using row_version.

Tests that concurrent updates are properly detected and prevented
using the row_version field as a version counter.
"""
import pytest
from sqlalchemy.orm import Session
from app.models import LifecycleStage
from app.services import RegistryService
from app.repositories import ModelRepository


class TestOptimisticLocking:
    """Test optimistic locking mechanism using row_version."""

    @pytest.fixture
    def registry_service(self, db_session):
        """Create a RegistryService instance for testing."""
        repo = ModelRepository(db_session)
        return RegistryService(repo)

    def test_successful_update_increments_row_version(
        self, registry_service, sample_version
    ):
        """Test that successful updates increment row_version."""
        initial_row_version = sample_version.row_version
        assert initial_row_version == 1  # Default starting value

        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, initial_row_version
        )

        assert error is None
        assert updated is not None
        assert updated.row_version == initial_row_version + 1

    def test_stale_row_version_causes_conflict(
        self, registry_service, sample_version, db_session
    ):
        """Test that using a stale row_version causes a conflict."""
        initial_row_version = sample_version.row_version

        # First update succeeds
        updated1, error1 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, initial_row_version
        )
        assert error1 is None
        assert updated1.row_version == initial_row_version + 1

        # Second update with stale row_version fails
        updated2, error2 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.APPROVED, initial_row_version
        )

        assert updated2 is None
        assert error2 is not None
        assert "Conflict" in error2
        assert "row_version mismatch" in error2

    def test_sequential_updates_with_correct_row_versions_succeed(
        self, registry_service, sample_version
    ):
        """Test that sequential updates work when using correct row_versions."""
        rv1 = sample_version.row_version

        # Update 1: DRAFT -> VALIDATED
        updated1, error1 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, rv1
        )
        assert error1 is None
        rv2 = updated1.row_version

        # Update 2: VALIDATED -> APPROVED
        updated2, error2 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.APPROVED, rv2
        )
        assert error2 is None
        rv3 = updated2.row_version

        # Update 3: APPROVED -> STAGING
        updated3, error3 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.STAGING, rv3
        )
        assert error3 is None
        rv4 = updated3.row_version

        # Verify row_version incremented each time
        assert rv2 == rv1 + 1
        assert rv3 == rv2 + 1
        assert rv4 == rv3 + 1

    def test_concurrent_update_simulation(
        self, registry_service, sample_version, db_session
    ):
        """
        Simulate concurrent updates by two clients.
        Both read the same version, but only one update should succeed.
        """
        # Both clients read the current state
        client1_row_version = sample_version.row_version
        client2_row_version = sample_version.row_version

        # Client 1 updates first (succeeds)
        updated1, error1 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, client1_row_version
        )
        assert error1 is None
        assert updated1.row_version == client1_row_version + 1

        # Client 2 tries to update with stale row_version (fails)
        updated2, error2 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, client2_row_version
        )
        assert updated2 is None
        assert "Conflict" in error2

    def test_client_can_retry_after_conflict(
        self, registry_service, sample_version, db_session
    ):
        """Test that a client can retry after receiving a conflict error."""
        initial_rv = sample_version.row_version

        # First update succeeds
        updated1, _ = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, initial_rv
        )

        # Second client gets conflict with stale version
        _, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, initial_rv
        )
        assert "Conflict" in error

        # Client refreshes and retries with new row_version (succeeds with rollback)
        new_rv = updated1.row_version
        updated2, error2 = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.DRAFT, new_rv
        )
        assert error2 is None
        assert updated2 is not None

    def test_multiple_concurrent_conflicts(
        self, registry_service, sample_version, db_session
    ):
        """Test handling of multiple concurrent update attempts."""
        initial_rv = sample_version.row_version

        # First update succeeds
        updated, _ = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, initial_rv
        )

        # Multiple clients with stale versions all fail
        for _ in range(5):
            result, error = registry_service.promote_lifecycle(
                sample_version.id, LifecycleStage.APPROVED, initial_rv
            )
            assert result is None
            assert "Conflict" in error

        # Verify the version is still in VALIDATED state
        final_version = registry_service.get_version(sample_version.id)
        assert final_version.lifecycle_stage == LifecycleStage.VALIDATED

    def test_row_version_mismatch_with_negative_value(
        self, registry_service, sample_version
    ):
        """Test that negative row_versions cause conflicts."""
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, -1
        )

        assert updated is None
        assert "Conflict" in error

    def test_row_version_mismatch_with_future_value(
        self, registry_service, sample_version
    ):
        """Test that future row_versions cause conflicts."""
        current_rv = sample_version.row_version
        future_rv = current_rv + 100

        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, future_rv
        )

        assert updated is None
        assert "Conflict" in error

    def test_row_version_persists_across_reads(
        self, registry_service, sample_version, db_session
    ):
        """Test that row_version is correctly persisted and retrieved."""
        # Promote lifecycle
        rv1 = sample_version.row_version
        updated, _ = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, rv1
        )
        rv2 = updated.row_version

        # Re-fetch from database
        db_session.expire_all()  # Clear session cache
        refetched = registry_service.get_version(sample_version.id)

        assert refetched.row_version == rv2
        assert refetched.lifecycle_stage == LifecycleStage.VALIDATED

    def test_optimistic_locking_on_rollback_transition(
        self, registry_service, sample_version, db_session
    ):
        """Test that optimistic locking works for rollback transitions too."""
        # Promote to VALIDATED
        sample_version.lifecycle_stage = LifecycleStage.VALIDATED
        db_session.commit()
        db_session.refresh(sample_version)

        initial_rv = sample_version.row_version

        # Client 1 rolls back to DRAFT
        updated1, _ = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.DRAFT, initial_rv
        )

        # Client 2 tries to roll back with stale version (conflict)
        updated2, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.DRAFT, initial_rv
        )

        assert updated2 is None
        assert "Conflict" in error

    def test_zero_row_version_causes_conflict(self, registry_service, sample_version):
        """Test that row_version of 0 causes a conflict (versions start at 1)."""
        updated, error = registry_service.promote_lifecycle(
            sample_version.id, LifecycleStage.VALIDATED, 0
        )

        assert updated is None
        assert "Conflict" in error

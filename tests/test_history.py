"""
Tests for history tracking module
"""
import json
import tempfile
from pathlib import Path
import pytest
from audit.checks.history import HistoryTracker, check_history


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def tracker(temp_db):
    """Create tracker instance with temp database"""
    return HistoryTracker(db_path=temp_db)


@pytest.fixture
def sample_audit():
    """Sample audit data"""
    return {
        "url": "https://example.com",
        "score": 85,
        "checks": {
            "meta": {"issues": ["Missing description"]},
            "links": {"issues": []}
        }
    }


def test_init_db(tracker):
    """Test database initialization"""
    assert Path(tracker.db_path).exists()


def test_save_audit(tracker, sample_audit):
    """Test saving audit to history"""
    audit_id = tracker.save_audit("https://example.com", sample_audit)
    assert audit_id > 0


def test_get_history(tracker, sample_audit):
    """Test retrieving audit history"""
    tracker.save_audit("https://example.com", sample_audit)
    tracker.save_audit("https://example.com", sample_audit)
    
    history = tracker.get_history("https://example.com", limit=5)
    assert len(history) == 2
    assert history[0]["score"] == 85


def test_compare_with_previous(tracker, sample_audit):
    """Test comparison with previous audit"""
    # First audit
    tracker.save_audit("https://example.com", sample_audit)
    
    # Second audit with improved score
    improved_audit = sample_audit.copy()
    improved_audit["score"] = 90
    improved_audit["checks"]["meta"]["issues"] = []
    
    comparison = tracker.compare_with_previous("https://example.com", improved_audit)
    
    assert comparison is not None
    assert comparison["score_change"] == 5
    assert comparison["issues_change"] == -1


def test_get_trend(tracker, sample_audit):
    """Test trend analysis"""
    # Add multiple audits
    for score in [80, 82, 85, 88, 90]:
        audit = sample_audit.copy()
        audit["score"] = score
        tracker.save_audit("https://example.com", audit)
    
    trend = tracker.get_trend("https://example.com", days=30)
    
    assert trend["audits_count"] == 5
    assert trend["score_trend"]["first"] == 80
    assert trend["score_trend"]["last"] == 90
    assert trend["score_trend"]["change"] == 10


def test_check_history(tracker, sample_audit):
    """Test history check module"""
    result = check_history("https://example.com", sample_audit, tracker=tracker)
    
    assert result["status"] == "pass"
    assert "audit_id" in result
    assert "trend" in result


def test_empty_history(tracker):
    """Test behavior with no history"""
    history = tracker.get_history("https://nonexistent.com")
    assert len(history) == 0
    
    trend = tracker.get_trend("https://nonexistent.com")
    assert "error" in trend

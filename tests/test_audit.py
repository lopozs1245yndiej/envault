"""Tests for envault/audit.py"""

import json
import pytest
from pathlib import Path

from envault.audit import (
    get_audit_log_path,
    log_event,
    read_events,
    clear_log,
    AUDIT_LOG_FILENAME,
)


@pytest.fixture
def audit_dir(tmp_path):
    return tmp_path / ".envault"


def test_get_audit_log_path_returns_expected(audit_dir):
    path = get_audit_log_path(base_dir=audit_dir)
    assert path == audit_dir / AUDIT_LOG_FILENAME


def test_log_event_creates_file(audit_dir):
    log_event("lock", ".env", success=True, base_dir=audit_dir)
    assert get_audit_log_path(audit_dir).exists()


def test_log_event_writes_valid_json(audit_dir):
    log_event("unlock", ".env.production", success=True, base_dir=audit_dir)
    log_path = get_audit_log_path(audit_dir)
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["action"] == "unlock"
    assert entry["target"] == ".env.production"
    assert entry["success"] is True
    assert "timestamp" in entry


def test_log_event_includes_note_when_provided(audit_dir):
    log_event("push", ".env", success=False, base_dir=audit_dir, note="sync dir missing")
    events = read_events(base_dir=audit_dir)
    assert events[0]["note"] == "sync dir missing"


def test_log_event_no_note_key_when_empty(audit_dir):
    log_event("pull", ".env", success=True, base_dir=audit_dir)
    events = read_events(base_dir=audit_dir)
    assert "note" not in events[0]


def test_read_events_returns_empty_list_when_no_log(audit_dir):
    events = read_events(base_dir=audit_dir)
    assert events == []


def test_read_events_returns_all_entries(audit_dir):
    log_event("lock", ".env", success=True, base_dir=audit_dir)
    log_event("push", ".env", success=True, base_dir=audit_dir)
    log_event("unlock", ".env", success=False, base_dir=audit_dir)
    events = read_events(base_dir=audit_dir)
    assert len(events) == 3
    assert events[2]["action"] == "unlock"


def test_clear_log_removes_file(audit_dir):
    log_event("lock", ".env", success=True, base_dir=audit_dir)
    clear_log(base_dir=audit_dir)
    assert not get_audit_log_path(audit_dir).exists()


def test_clear_log_no_error_when_missing(audit_dir):
    # should not raise
    clear_log(base_dir=audit_dir)

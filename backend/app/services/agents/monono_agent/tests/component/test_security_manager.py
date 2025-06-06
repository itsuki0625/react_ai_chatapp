import pytest
import json
import logging
from app.services.agents.monono_agent.components.security_manager import SecurityManager

class TestSecurityManager:

    @pytest.fixture(autouse=True)
    def setup_logger(self, caplog):
        # キャプチャするロガーを設定
        caplog.set_level(logging.INFO, logger="security_audit")
        return caplog

    def test_sanitize_string_and_patterns(self):
        patterns = [r"[\w\.-]+@[\w\.-]+", r"\b\d{2,4}-\d{2,4}-\d{4}\b"]
        mgr = SecurityManager(pii_patterns=patterns)
        text = "Email: user.name@example.com, Tel: 03-1234-5678"
        masked = mgr.sanitize_data(text)
        assert "user.name@example.com" not in masked
        assert "03-1234-5678" not in masked
        assert masked.count("[REDACTED]") >= 2

    def test_sanitize_nested_structures(self):
        patterns = [r"secret"]
        mgr = SecurityManager(pii_patterns=patterns)
        data = {
            "key1": "this is secret info",
            "key2": ["no secret", "very secret"]
        }
        result = mgr.sanitize_data(data)
        assert result["key1"] == "this is [REDACTED] info"
        assert result["key2"][0] == "no [REDACTED]"
        assert result["key2"][1] == "very [REDACTED]"

    def test_check_permissions_default_allow(self):
        mgr = SecurityManager()
        # ACLが空の場合は全許可
        assert mgr.check_permissions("any_user", "delete", "resource") is True

    def test_check_permissions_with_acl(self):
        acl = {"alice": ["read", "write"], "bob": ["read"]}
        mgr = SecurityManager(access_control_list=acl)
        assert mgr.check_permissions("alice", "write", "res1") is True
        assert mgr.check_permissions("alice", "delete", "res1") is False
        # ユーザー未登録は許可
        assert mgr.check_permissions("charlie", "delete", "res2") is True

    def test_log_audit_event_records_info(self, setup_logger):
        mgr = SecurityManager()
        event = {"user": "alice", "action": "login", "status": "success"}
        mgr.log_audit_event(event)
        # caplogにINFOレコードがあること
        records = [r for r in setup_logger.records if r.levelno == logging.INFO]
        assert any("alice" in r.message and "login" in r.message for r in records) 
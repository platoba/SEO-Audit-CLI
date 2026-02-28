"""Tests for audit.telegram_bot - Telegram message formatting and sending."""

import pytest
from unittest.mock import patch, MagicMock
from audit.core import AuditResult
from audit.telegram_bot import (
    format_telegram_report,
    format_batch_telegram_report,
    send_to_telegram,
    send_audit_to_telegram,
)


@pytest.fixture
def sample_result():
    r = AuditResult(url="https://example.com", domain="example.com")
    r.load_time = 1.5
    r.details = {"page_size_kb": 250, "core_web_vitals": {
        "LCP": {"status": "good", "estimate": "1.5s"},
        "CLS": {"status": "needs_improvement", "risk_elements": 2},
    }}
    r.add_issue("error", "meta", "Missing title", 10)
    r.add_issue("warning", "links", "No lazy loading", 2)
    r.add_pass("security", "HTTPS OK")
    # score = 100 - 10 - 2 = 88
    return r


@pytest.fixture
def sample_batch():
    results = []
    for i in range(12):
        r = AuditResult(url=f"https://example{i}.com", domain=f"example{i}.com")
        r.score = 60 + i * 3
        r.add_issue("error", "meta", "err", 5)
        results.append(r)
    return results


class TestFormatTelegramReport:
    def test_contains_url(self, sample_result):
        text = format_telegram_report(sample_result)
        assert "example.com" in text

    def test_contains_score(self, sample_result):
        text = format_telegram_report(sample_result)
        assert "88" in text

    def test_contains_errors(self, sample_result):
        text = format_telegram_report(sample_result)
        assert "Missing title" in text

    def test_contains_warnings(self, sample_result):
        text = format_telegram_report(sample_result)
        assert "No lazy loading" in text

    def test_contains_cwv(self, sample_result):
        text = format_telegram_report(sample_result)
        assert "LCP" in text
        assert "CLS" in text

    def test_emoji_red_for_low_score(self):
        r = AuditResult(url="https://bad.com", domain="bad.com")
        r.score = 40
        text = format_telegram_report(r)
        assert "🔴" in text

    def test_emoji_green_for_high_score(self):
        r = AuditResult(url="https://good.com", domain="good.com")
        r.score = 90
        text = format_telegram_report(r)
        assert "🟢" in text

    def test_truncates_many_errors(self):
        r = AuditResult(url="https://x.com", domain="x.com")
        for i in range(10):
            r.add_issue("error", "meta", f"Error {i}", 1)
        text = format_telegram_report(r)
        assert "more" in text.lower()


class TestFormatBatchTelegramReport:
    def test_batch_contains_count(self, sample_batch):
        text = format_batch_telegram_report(sample_batch)
        assert "12" in text

    def test_batch_truncates_at_10(self, sample_batch):
        text = format_batch_telegram_report(sample_batch)
        assert "more" in text.lower()

    def test_batch_avg_score(self, sample_batch):
        text = format_batch_telegram_report(sample_batch)
        assert "Avg Score" in text


class TestSendToTelegram:
    @patch("audit.telegram_bot.requests.post")
    def test_send_success(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"ok": True}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        result = send_to_telegram("Test message", bot_token="123:ABC", chat_id="456")
        assert result["ok"] is True
        mock_post.assert_called_once()

    def test_send_missing_token(self):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            send_to_telegram("Test", bot_token="", chat_id="")

    @patch("audit.telegram_bot.requests.post")
    def test_send_uses_env(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"ok": True}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        import os
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["TELEGRAM_CHAT_ID"] = "test-chat"
        try:
            send_to_telegram("Hello")
            mock_post.assert_called_once()
        finally:
            del os.environ["TELEGRAM_BOT_TOKEN"]
            del os.environ["TELEGRAM_CHAT_ID"]


class TestSendAuditToTelegram:
    @patch("audit.telegram_bot.send_to_telegram")
    def test_single_result(self, mock_send, sample_result):
        mock_send.return_value = {"ok": True}
        send_audit_to_telegram(sample_result, bot_token="t", chat_id="c")
        mock_send.assert_called_once()
        text = mock_send.call_args[0][0]
        assert "example.com" in text

    @patch("audit.telegram_bot.send_to_telegram")
    def test_batch_results(self, mock_send, sample_batch):
        mock_send.return_value = {"ok": True}
        send_audit_to_telegram(sample_batch, bot_token="t", chat_id="c")
        mock_send.assert_called_once()
        text = mock_send.call_args[0][0]
        assert "Batch" in text

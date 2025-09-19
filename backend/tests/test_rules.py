import pytest
from app.rules.email import check_email_reputation
from app.rules.bot import check_bot_activity
from app.rules.timezone import check_timezone_mismatch
from app.rules.device import check_device


def test_email_temporary():
    result = check_email_reputation("test@yopmail.com")
    assert result.fraud_flag == "temporary_email"
    assert result.score_delta > 0


def test_email_normal():
    result = check_email_reputation("test@gmail.com")
    assert result.fraud_flag is None
    assert result.score_delta == 0


def test_bot_activity_fast_typing():
    result = check_bot_activity(5000, 10, 1000, 30)  # typing < 40ms
    assert result.fraud_flag == "autofill_or_bot"
    assert result.score_delta > 0


def test_bot_activity_no_mouse():
    result = check_bot_activity(2000, 0, 500, 100)  # no mouse moves
    assert result.fraud_flag == "bot_like_activity"
    assert result.score_delta > 0


def test_timezone_mismatch():
    result = check_timezone_mismatch("US", "Europe/London")
    assert result.fraud_flag == "timezone_mismatch"
    assert result.score_delta > 0


def test_timezone_match():
    result = check_timezone_mismatch("US", "America/New_York")
    assert result.fraud_flag is None
    assert result.score_delta == 0


def test_device_suspicious():
    result = check_device({"platform": "Linux"}, "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/91.0")
    assert result.fraud_flag == "suspicious_device"
    assert result.score_delta > 0


def test_device_normal():
    result = check_device({"platform": "MacIntel"}, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
    assert result.fraud_flag is None
    assert result.score_delta == 0

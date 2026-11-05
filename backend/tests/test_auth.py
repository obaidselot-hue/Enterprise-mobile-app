import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import ValidationError

from database import SessionLocal
import models
import schemas
from routers import auth
from security import hash_otp, decode_token

def test_request_otp_invalid_phone_format():
    """Ensure malformed or non-E.164 phone numbers raise validation errors."""
    with pytest.raises(ValidationError):
        schemas.PhoneRequest(phone_number="12345")
    
    with pytest.raises(ValidationError):
        schemas.PhoneRequest(phone_number="04155552671")

def test_request_otp_valid_phone():
    """Ensure valid international phone numbers trigger code generation."""
    test_phone = "+14155553333"
    db = SessionLocal()
    # Clean previous
    db.query(models.OTPVerification).filter(models.OTPVerification.phone_number == test_phone).delete()
    db.commit()

    payload = schemas.PhoneRequest(phone_number=test_phone)
    result = auth.request_otp(payload, db)

    assert result["success"] is True
    assert result["cooldown_seconds"] == 60
    assert result["expires_in_seconds"] == 300

    # Verify record in DB
    rec = db.query(models.OTPVerification).filter(models.OTPVerification.phone_number == test_phone).first()
    assert rec is not None
    assert rec.status == "pending"
    db.close()

def test_request_otp_cooldown_rejection():
    """Ensure requesting another OTP within 60 seconds raises HTTP 429."""
    test_phone = "+14155554444"
    db = SessionLocal()
    db.query(models.OTPVerification).filter(models.OTPVerification.phone_number == test_phone).delete()
    db.commit()

    payload = schemas.PhoneRequest(phone_number=test_phone)
    auth.request_otp(payload, db)

    # Immediate second request
    with pytest.raises(HTTPException) as exc_info:
        auth.request_otp(payload, db)
    
    assert exc_info.value.status_code == 429
    assert "Cooldown active" in exc_info.value.detail
    db.close()

def test_verify_otp_lifecycle_and_jwt():
    """Test full verification flow: valid code -> returns JWT access and refresh tokens."""
    test_phone = "+14155555555"
    db = SessionLocal()
    db.query(models.OTPVerification).filter(models.OTPVerification.phone_number == test_phone).delete()
    db.commit()

    raw_otp = "852963"
    rec = models.OTPVerification(
        phone_number=test_phone,
        otp_hash=hash_otp(raw_otp),
        attempts_count=0,
        max_attempts=3,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()

    # Mock request object
    class DummyRequest:
        client = type("Client", (), {"host": "127.0.0.1"})()

    verify_payload = schemas.OTPVerifyRequest(phone_number=test_phone, otp_code=raw_otp)
    token_resp = auth.verify_otp(verify_payload, DummyRequest(), db)

    assert token_resp.access_token is not None
    assert token_resp.refresh_token is not None
    assert token_resp.token_type == "bearer"
    assert token_resp.user.phone_number == test_phone

    # Verify token decoding
    decoded = decode_token(token_resp.access_token, expected_type="access")
    assert decoded["phone"] == test_phone
    db.close()

def test_verify_otp_invalid_code_decrements_attempts():
    """Test that wrong code decrements remaining attempts and eventually locks out."""
    test_phone = "+14155556666"
    db = SessionLocal()
    db.query(models.OTPVerification).filter(models.OTPVerification.phone_number == test_phone).delete()
    db.commit()

    rec = models.OTPVerification(
        phone_number=test_phone,
        otp_hash=hash_otp("112233"),
        attempts_count=0,
        max_attempts=3,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()

    class DummyRequest:
        client = type("Client", (), {"host": "127.0.0.1"})()

    bad_payload = schemas.OTPVerifyRequest(phone_number=test_phone, otp_code="000000")

    # Attempt 1
    with pytest.raises(HTTPException) as exc1:
        auth.verify_otp(bad_payload, DummyRequest(), db)
    assert "2 attempt(s) remaining" in exc1.value.detail

    # Attempt 2
    with pytest.raises(HTTPException) as exc2:
        auth.verify_otp(bad_payload, DummyRequest(), db)
    assert "1 attempt(s) remaining" in exc2.value.detail

    # Attempt 3 (Lockout)
    with pytest.raises(HTTPException) as exc3:
        auth.verify_otp(bad_payload, DummyRequest(), db)
    assert "0 attempt(s) remaining" in exc3.value.detail

    # Attempt 4 (Rejected due to max attempts exceeded)
    with pytest.raises(HTTPException) as exc4:
        auth.verify_otp(bad_payload, DummyRequest(), db)
    assert "Maximum verification attempts exceeded" in exc4.value.detail

    db.close()

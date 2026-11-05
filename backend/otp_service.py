import secrets
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config import settings
import models
from security import hash_otp

logger = logging.getLogger("uvicorn.error")

class OTPService:
    @staticmethod
    def generate_secure_otp() -> str:
        """Generates a cryptographically strong 6-digit numeric OTP (100000 - 999999)."""
        return f"{secrets.randbelow(900000) + 100000}"

    @classmethod
    def request_otp(cls, db: Session, phone_number: str) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Check Resend Cooldown (e.g., 60 seconds)
        recent_request = db.query(models.OTPVerification).filter(
            models.OTPVerification.phone_number == phone_number,
            models.OTPVerification.created_at >= now - timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
        ).first()

        if recent_request:
            elapsed = (now - recent_request.created_at).total_seconds()
            remaining_wait = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Cooldown active. Please wait {max(1, remaining_wait)} seconds before requesting a new code."
            )

        # 2. Velocity Limit: Max requests per hour
        hourly_count = db.query(models.OTPVerification).filter(
            models.OTPVerification.phone_number == phone_number,
            models.OTPVerification.created_at >= now - timedelta(hours=1)
        ).count()

        if hourly_count >= settings.OTP_MAX_REQUESTS_PER_HOUR:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Exceeded hourly limit of {settings.OTP_MAX_REQUESTS_PER_HOUR} OTP requests. Please try again later."
            )

        # 3. Invalidate any existing pending OTPs
        db.query(models.OTPVerification).filter(
            models.OTPVerification.phone_number == phone_number,
            models.OTPVerification.status == "pending"
        ).update({"status": "expired"})

        # 4. Generate & Hash new OTP
        raw_otp = cls.generate_secure_otp()
        hashed = hash_otp(raw_otp)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        otp_record = models.OTPVerification(
            phone_number=phone_number,
            otp_hash=hashed,
            attempts_count=0,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            status="pending",
            expires_at=expires_at,
            created_at=now
        )
        db.add(otp_record)
        db.commit()

        # 5. Dispatch via SMS Provider
        cls._dispatch_sms(phone_number, raw_otp)

        return {
            "success": True,
            "message": "OTP has been generated and dispatched.",
            "cooldown_seconds": settings.OTP_RESEND_COOLDOWN_SECONDS,
            "expires_in_seconds": settings.OTP_EXPIRE_MINUTES * 60
        }

    @classmethod
    def verify_otp(cls, db: Session, phone_number: str, raw_otp: str) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Retrieve the most recent OTP record for this phone number
        record = db.query(models.OTPVerification).filter(
            models.OTPVerification.phone_number == phone_number
        ).order_by(models.OTPVerification.created_at.desc()).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending verification request found. Please request a new OTP."
            )

        if record.status == "failed" or record.attempts_count >= record.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Code has been invalidated."
            )

        if record.status == "expired":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new verification code."
            )

        if record.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending verification request found. Please request a new OTP."
            )

        # Check Expiration
        if now > record.expires_at:
            record.status = "expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new verification code."
            )

        # Hash and compare
        incoming_hash = hash_otp(raw_otp)
        if incoming_hash != record.otp_hash:
            record.attempts_count += 1
            if record.attempts_count >= record.max_attempts:
                record.status = "failed"
            db.commit()
            remaining = record.max_attempts - record.attempts_count
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {max(0, remaining)} attempt(s) remaining."
            )

        # Successfully Verified
        record.status = "verified"
        db.commit()
        return True

    @staticmethod
    def _dispatch_sms(phone_number: str, otp: str):
        """Dispatches SMS through Twilio if configured, or prints clearly to console in dev mode."""
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_PHONE:
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"Your security verification code is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
                    from_=settings.TWILIO_FROM_PHONE,
                    to=phone_number
                )
                logger.info(f"SMS successfully dispatched to {phone_number} via Twilio.")
            except Exception as e:
                logger.error(f"Failed to deliver SMS via Twilio: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="SMS gateway provider encountered an error delivering the code."
                )
        else:
            print("\n" + "=" * 60)
            print("  📱 [DEVELOPMENT SMS GATEWAY DISPATCH]")
            print(f"  Destination : {phone_number}")
            print(f"  OTP Code    : {otp}")
            print(f"  Validity    : {settings.OTP_EXPIRE_MINUTES} Minutes")
            print("=" * 60 + "\n")

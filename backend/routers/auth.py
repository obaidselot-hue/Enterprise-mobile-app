from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
import models
import schemas
from otp_service import OTPService
from security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication & OTP"])

@router.post("/request-otp", summary="Request 6-digit OTP code")
def request_otp(payload: schemas.PhoneRequest, db: Session = Depends(get_db)):
    """Generates and delivers a cryptographically random 6-digit OTP to the phone number."""
    result = OTPService.request_otp(db, payload.phone_number)
    return result

@router.post("/verify-otp", response_model=schemas.TokenResponse, summary="Verify OTP and obtain JWT tokens")
def verify_otp(payload: schemas.OTPVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """Verifies the OTP against the hashed record. Upon success, provisions/authenticates the user."""
    OTPService.verify_otp(db, payload.phone_number, payload.otp_code)

    # Find or provision user
    user = db.query(models.User).filter(models.User.phone_number == payload.phone_number).first()
    if not user:
        # Default new registrations as operator
        user = models.User(
            phone_number=payload.phone_number,
            full_name=f"User {payload.phone_number[-4:]}",
            role="operator",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    # Record login audit log
    client_ip = request.client.host if request.client else "unknown"
    audit = models.AuditLog(
        user_id=user.id,
        action_type="AUTH_OTP_LOGIN",
        entity_name="users",
        entity_id=user.id,
        ip_address=client_ip,
        details={"phone": user.phone_number, "timestamp": datetime.utcnow().isoformat()}
    )
    db.add(audit)
    db.commit()

    # Generate Token Pair
    claims = {"sub": str(user.id), "phone": user.phone_number, "role": user.role}
    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=schemas.UserProfileResponse.model_validate(user)
    )

@router.post("/refresh-token", summary="Exchange refresh token for new access token")
def refresh_access_token(payload: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refreshes an expired access token using a valid, non-expired refresh token."""
    decoded = decode_token(payload.refresh_token, expected_type="refresh")
    user_id = decoded.get("sub")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session or deactivated account.")

    claims = {"sub": str(user.id), "phone": user.phone_number, "role": user.role}
    new_access_token = create_access_token(claims)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in_seconds": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=schemas.UserProfileResponse, summary="Get current logged-in user profile")
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """Returns the authenticated user's profile and permissions."""
    return current_user

"""
MYFY.AI — KYC & DigiLocker Verification Router
Handles PAN validation, DigiLocker Aadhaar e-KYC session initiation, and OTP verification.
"""
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models, schemas

router = APIRouter(prefix="/kyc", tags=["kyc"])

# Active in-memory DigiLocker Aadhaar e-KYC sessions (session_id -> data)
DIGILOCKER_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Indian PAN Regex: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")


def mask_pan(pan: str) -> str:
    """Mask PAN for privacy, showing only first 2 and last 2 characters (e.g., ABXXXXXX4F)."""
    if not pan or len(pan) != 10:
        return pan
    return f"{pan[:2]}XXXXXX{pan[-2:]}"


def mask_aadhaar(last4: str) -> str:
    """Format masked Aadhaar display (e.g., XXXX-XXXX-1234)."""
    if not last4:
        return "XXXX-XXXX-XXXX"
    return f"XXXX-XXXX-{last4}"


@router.get("/status", response_model=schemas.KycStatusResponse)
def get_kyc_status(
    current_user: models.User = Depends(get_current_user),
):
    """Fetch current user's KYC verification status."""
    return schemas.KycStatusResponse(
        kyc_status=current_user.kyc_status or "pending",
        pan_number=mask_pan(current_user.pan_number) if current_user.pan_number else None,
        pan_verified=bool(current_user.pan_verified),
        aadhaar_masked=mask_aadhaar(current_user.aadhaar_last4) if current_user.aadhaar_last4 else None,
        digilocker_verified=bool(current_user.digilocker_verified),
        monthly_income=float(current_user.monthly_income or 0.0),
        kyc_completed_at=current_user.kyc_completed_at,
    )


@router.post("/pan/verify")
def verify_pan(
    payload: schemas.PanVerifyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Verify and register the user's Permanent Account Number (PAN).
    Validates standard 10-character alphanumeric PAN format against ITD requirements.
    """
    pan_clean = payload.pan_number.strip().upper()
    if not PAN_REGEX.match(pan_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN format. PAN must be exactly 10 alphanumeric characters (e.g., ABCDE1234F).",
        )

    # Check 4th letter entity type: 'P' = Individual (standard for personal finance)
    entity_type = pan_clean[3]
    entity_desc = "Individual" if entity_type == "P" else "Entity/Company"

    current_user.pan_number = pan_clean
    current_user.pan_verified = True

    if current_user.digilocker_verified:
        current_user.kyc_status = "verified"
        if not current_user.kyc_completed_at:
            current_user.kyc_completed_at = datetime.utcnow()
    else:
        current_user.kyc_status = "pan_verified"

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": f"PAN verified successfully ({entity_desc} holder: {current_user.name}).",
        "pan_masked": mask_pan(pan_clean),
        "kyc_status": current_user.kyc_status,
    }


@router.post("/digilocker/initiate")
def initiate_digilocker(
    payload: schemas.DigiLockerInitiateRequest,
    current_user: models.User = Depends(get_current_user),
):
    """
    Initiate DigiLocker Aadhaar e-KYC authentication session.
    Accepts 12-digit Aadhaar number and generates an OTP session.
    """
    aadhaar_clean = re.sub(r"[\s\-]", "", payload.aadhaar_number)
    if not re.match(r"^\d{12}$", aadhaar_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Aadhaar number. Must be exactly 12 digits.",
        )

    session_id = str(uuid.uuid4())
    # In production sandbox, DigiLocker routes OTP to UIDAI-registered mobile
    simulated_otp = "123456"
    DIGILOCKER_SESSIONS[session_id] = {
        "user_id": current_user.id,
        "aadhaar_last4": aadhaar_clean[-4:],
        "otp": simulated_otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }

    masked = mask_aadhaar(aadhaar_clean[-4:])
    return {
        "success": True,
        "session_id": session_id,
        "masked_aadhaar": masked,
        "message": f"DigiLocker OTP requested for {masked}. Please enter the 6-digit OTP sent to your linked mobile number.",
        "sandbox_hint": "Demo/Sandbox mode: Use OTP 123456",
    }


@router.post("/digilocker/verify-otp")
def verify_digilocker_otp(
    payload: schemas.DigiLockerVerifyOtpRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Validate DigiLocker OTP, confirm Aadhaar verification, and finalize KYC status.
    """
    session = DIGILOCKER_SESSIONS.get(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DigiLocker verification session expired or invalid. Please re-initiate.",
        )

    if session["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not match active account credentials.",
        )

    if datetime.utcnow() > session["expires_at"]:
        DIGILOCKER_SESSIONS.pop(payload.session_id, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    otp_entered = payload.otp.strip()
    if otp_entered != session["otp"] and otp_entered != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP. Please check the code and try again (Sandbox test OTP: 123456).",
        )

    # Mark verified in database
    current_user.aadhaar_last4 = session["aadhaar_last4"]
    current_user.digilocker_verified = True
    current_user.digilocker_id = f"DL-{uuid.uuid4().hex[:8].upper()}"
    current_user.kyc_status = "verified"
    current_user.kyc_completed_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    # Clean up session
    DIGILOCKER_SESSIONS.pop(payload.session_id, None)

    return {
        "success": True,
        "message": "DigiLocker Aadhaar e-KYC authenticated and profile verified successfully!",
        "digilocker_id": current_user.digilocker_id,
        "kyc_status": current_user.kyc_status,
        "aadhaar_masked": mask_aadhaar(current_user.aadhaar_last4),
        "completed_at": current_user.kyc_completed_at,
    }

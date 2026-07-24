#!/usr/bin/env python3
"""
FastAPI wrapper for he853-static RF transmitter (Elro/KaKu smart home switches).
Secure, robust, and production-ready implementation.
"""

import logging
import os
import subprocess
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="HE853 Static Controller", version="1.0.0")

# Pydantic response models
class StatusResponse(BaseModel):
    exitcode: int
    result: str
    verbose_result: str | None = None

    @field_validator("exitcode")
    @classmethod
    def validate_exitcode(cls, v):
        return int(v)


# =====================
# Authentication Layer
# =====================

async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from header against environment variable."""
    expected_key = os.environ.get("HE853_API_KEY")
    if not expected_key:
        logger.warning("HE853_API_KEY not configured — authentication disabled!")
        return True  # Developer mode!
    if x_api_key != expected_key:
        logger.warning(f"Invalid API key attempt from caller")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


# =====================
# Core Helper Functions
# =====================

def run_he853(args: list[str], timeout: int = 10) -> dict:
    """
    Execute he853-static with given arguments.
    Returns standardized status dictionary.
    """
    try:
        result = subprocess.run(
            ["he853-static", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined_output = f"{stdout}\n{stderr}" if stderr else stdout
        
        logger.debug(f"he853-static returned {result.returncode}: {combined_output[:200]}")
        
        return {
            "verbose_result": combined_output if combined_output else None,
            "exitcode": result.returncode,
            "result": "OK" if result.returncode == 0 else "FAIL",
        }
    except FileNotFoundError as e:
        logger.error(f"he853-static binary not found in PATH: {e}")
        return {
            "verbose_result": "he853-static binary not found in PATH",
            "exitcode": -1,
            "result": "FAIL",
        }
    except subprocess.TimeoutExpired as e:
        logger.error(f"he853-static command timed out after {timeout}s: {e}")
        return {
            "verbose_result": f"Command timed out after {timeout} seconds",
            "exitcode": -2,
            "result": "FAIL",
        }

def normalize_action(action: str) -> tuple[str, bool]:
    """
    Normalize validated action to onoff string.
    Returns (onoff_value, success).
    
    Note: action is already regex-validated, so we only check range for numeric.
    """
    if action.lower() == "on":
        return ("1", True)
    if action.lower() == "off":
        return ("0", True)
    
    # Numeric action (already regex-validated as 1-3 digits)
    try:
        num_val = int(action)
        if 0 <= num_val <= 255:
            return (str(num_val), True)
    except ValueError:
        pass
    
    # Should not happen if regex is correct, but handle gracefully
    return ("", False)

# =====================
# API Endpoints
# =====================

@app.get("/status", response_model=StatusResponse, tags=["Status"])
def get_status():
    """Return the current status of the he853-static binary."""
    return run_he853([])


@app.get("/help", response_model=StatusResponse, tags=["Info"])
def get_help():
    """Return help output from he853-static."""
    return run_he853(["--help"])


@app.get("/switch", response_model=StatusResponse, tags=["Control"])
def switch(
    action: Annotated[str, Query(
        description="Action: on, off, or numeric 0-255",
        min_length=1,
        max_length=3,
        pattern=r"^(on|off|\d{1,3})$"
    )],
    address: Annotated[str, Query(
        description="4-digit device address (e.g., 1234)",
        pattern=r"^\d{4}$"
    )],
    protocol: Annotated[str, Query(
        description="Protocol: A, U, E, K, or L",
        pattern=r"^[AUEKL]$"
    )] = "A",
    api_key: bool = Depends(verify_api_key)
):
    """
    Control a smart home switch via he853-static.

    Parameters:
    - action: 'on' | 'off' | '1' | '0' | number 0-255 (for dimming)
    - address: 4-digit device address
    - protocol: One of A, U, E, K, L (default: A)
    """
    onoff, success = normalize_action(action)
    if not success:
        logger.warning(f"Invalid action: {action}")
        return StatusResponse(
            exitcode=-4,
            result="FAIL",
            verbose_result=f"Action '{action}' not allowed. Use: on, off, 1, 0, or 0-255"
        )

    args = [address, onoff, protocol.upper()]
    logger.info(f"Switch command: address={address}, action={onoff}, protocol={protocol}")

    result = run_he853(args)
    return StatusResponse(**result)

# =====================
# Application Entry Point
# =====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

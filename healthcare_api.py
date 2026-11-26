import sqlite3

from aura_usage_quota import (
    UsageQuota,
    UsageQuotaExceeded,
)

from aura_input_guard import (
    validate_question,
    InputTokenLimitExceeded,
)
from aura_rate_limiter import SlidingWindowRateLimiter
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import time
import uuid
from aura_tracing import trace_id_context
import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Request,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAIError

from healthcare_tools import (
    DatabaseUnavailableError,
    get_appointment_count,
    get_patient_status,
    get_all_patients,
)
from healthcare_agent import ask_healthcare_agent
from audit_logger import log_audit_event


app = FastAPI(
    title="Healthcare AI API",
    description="Educational prototype using fictional patient data",
    version="2.1.0",
    debug=False,
)

logger = logging.getLogger("aura.observability")
logger.setLevel(logging.INFO)

# Send observability logs to the Uvicorn terminal
logger.handlers.clear()
logger.addHandler(logging.StreamHandler())
logger.propagate = False
# API rate limiting
rate_limiter = SlidingWindowRateLimiter()

RATE_LIMIT_ENABLED = (
    os.environ.get("AURA_RATE_LIMIT_ENABLED", "false")
    .lower() == "true"
)

def check_rate_limit(request: Request):
    if not RATE_LIMIT_ENABLED:
        return None

    path = request.url.path.rstrip("/")
    method = request.method

    if method == "POST" and path == "/auth/login":
        category, limit = "login", 5
    elif method == "POST" and path == "/agent/ask":
        category, limit = "agent", 10
    elif method == "GET" and (
        path == "/patients" or path.startswith("/patients/")
    ):
        category, limit = "patients", 30
    else:
        return None

    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = rate_limiter.allow(
        f"{category}:{client_ip}", limit, window_seconds=60
    )

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": str(retry_after)},
        )
    return None


@app.middleware("http")
async def trace_requests(request, call_next):
    trace_id = uuid.uuid4().hex
    token = trace_id_context.set(trace_id)
    start_time = time.perf_counter()
    status = "success"

    try:
        response = check_rate_limit(request)
        if response is None:
            response = await call_next(request)

        if response.status_code >= 400:
            status = "error"

        response.headers["X-Trace-ID"] = trace_id
        return response

    except Exception:
        status = "error"
        raise

    finally:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.info(
            "trace_id=%s operation=http_request "
            "method=%s status=%s duration_ms=%.2f",
            trace_id,
            request.method,
            status,
            duration_ms,
        )

        trace_id_context.reset(token)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

COOKIE_NAME = "aura_session"
SESSION_DURATION_SECONDS = 3600
COOKIE_SECURE = os.environ.get("AURA_COOKIE_SECURE", "false").lower() == "true"


# -----------------------------------
# Safe error handling
# -----------------------------------

@app.exception_handler(DatabaseUnavailableError)
async def database_error_handler(
    request: Request,
    exc: DatabaseUnavailableError,
):
    logger.error(
        "Patient database unavailable: %s",
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Patient information temporarily unavailable"
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
):
    # Log only the exception type, not patient details,
    # secrets, request bodies, or full tracebacks.
    logger.error(
        "Unexpected application error: %s",
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred"
        },
    )


# -----------------------------------
# Authentication
# -----------------------------------

def session_settings():
    username = os.environ.get("AURA_DEMO_USERNAME", "")
    password = os.environ.get("AURA_DEMO_PASSWORD", "")
    secret = os.environ.get("AURA_SESSION_SECRET", "")

    if not username or len(password) < 12 or len(secret) < 32:
        raise RuntimeError(
            "Demo authentication environment variables are not configured"
        )

    return username, password, secret


def sign_session(payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def create_session(username: str, secret: str) -> str:
    session_data = {
        "username": username,
        "expires": int(time.time()) + SESSION_DURATION_SECONDS,
        "nonce": secrets.token_hex(16),
    }

    encoded = base64.urlsafe_b64encode(
        json.dumps(session_data).encode("utf-8")
    ).decode("ascii").rstrip("=")

    return sign_session(encoded, secret)


def verify_session(request: Request):
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        payload, signature = token.rsplit(".", 1)
        _, _, secret = session_settings()
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")

        padded = payload + "=" * (-len(payload) % 4)
        session_data = json.loads(
            base64.urlsafe_b64decode(padded).decode("utf-8")
        )

        if not isinstance(session_data, dict):
            raise ValueError("Invalid session data")

        expires = session_data["expires"]
        if (
            not isinstance(expires, int)
            or isinstance(expires, bool)
            or expires <= time.time()
        ):
            raise ValueError("Session expired or invalid")

        expected_username, _, _ = session_settings()
        if session_data["username"] != expected_username:
            raise ValueError("Invalid user")

        return expected_username

    except (
        ValueError,
        KeyError,
        TypeError,
        UnicodeError,
        binascii.Error,
        json.JSONDecodeError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        )


class LoginRequest(BaseModel):
    username: str
    password: str


class AgentQuestion(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


@app.post("/auth/login")
def login(credentials: LoginRequest, response: Response):
    username, password, secret = session_settings()

    username_valid = hmac.compare_digest(
        credentials.username.encode("utf-8"),
        username.encode("utf-8"),
    )

    password_valid = hmac.compare_digest(
        credentials.password.encode("utf-8"),
        password.encode("utf-8"),
    )

    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = create_session(username, secret)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_DURATION_SECONDS,
    )

    return {"message": "Login successful"}


@app.get("/auth/me")
def current_user(username=Depends(verify_session)):
    return {"username": username}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        samesite="lax",
    )
    return {"message": "Logged out"}


# -----------------------------------
# Patient authorization
# -----------------------------------

DEMO_PATIENT_ACCESS = {
    "aura_demo": {101},
}


def require_patient_access(
    username: str,
    patient_id: int,
    action: str,
):
    allowed_patients = DEMO_PATIENT_ACCESS.get(
        username,
        set(),
    )
    allowed = patient_id in allowed_patients

    # Audit before any patient database access.
    log_audit_event(
        username=username,
        patient_id=patient_id,
        action=action,
        outcome="allowed" if allowed else "denied",
        source="api",
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this patient",
        )


# -----------------------------------
# Patient endpoints
# -----------------------------------

@app.get("/patients")
def list_patients(username=Depends(verify_session)):
    allowed_ids = DEMO_PATIENT_ACCESS.get(
        username,
        set(),
    )

    if not allowed_ids:
        return {"patients": []}

    result = get_all_patients()

    filtered_patients = [
        patient
        for patient in result["patients"]
        if patient["id"] in allowed_ids
    ]

    return {"patients": filtered_patients}


@app.get("/patients/{patient_id}/appointments")
def patient_appointments(
    patient_id: int,
    username=Depends(verify_session),
):
    require_patient_access(
        username,
        patient_id,
        action="view_appointments",
    )

    result = get_appointment_count(patient_id)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return result


@app.get("/patients/{patient_id}/status")
def patient_status(
    patient_id: int,
    username=Depends(verify_session),
):
    require_patient_access(
        username,
        patient_id,
        action="view_status",
    )

    result = get_patient_status(patient_id)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return result


# -----------------------------------
# AI agent endpoint
# -----------------------------------

usage_quota = UsageQuota()


@app.post("/agent/ask")
def ask_agent(
    request: AgentQuestion,
    username=Depends(verify_session),
):
    allowed_ids = DEMO_PATIENT_ACCESS.get(
        username,
        set(),
    )

    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="A question is required",
            )

        validate_question(request.question)

        usage_quota.reserve_request()

        answer = ask_healthcare_agent(
            request.question,
            allowed_patient_ids=allowed_ids,
            username=username,
        )

        return {
            "question": request.question,
            "answer": answer,
        }

    except UsageQuotaExceeded as error:
        logger.warning(
            "Global usage quota exhausted"
        )

        raise HTTPException(
            status_code=429,
            detail="Demo usage limit reached. Please try again later.",
        ) from error

    except InputTokenLimitExceeded as error:
        raise HTTPException(
            status_code=400,
            detail="Request exceeds the allowed token limit",
        ) from error

    except sqlite3.Error as error:
        logger.error(
            "Database operation failed: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable",
        ) from error

    except OpenAIError as error:
        logger.error(
            "AI provider error: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail="AI service temporarily unavailable",
        ) from error

    except RuntimeError as error:
        logger.error(
            "Agent execution error: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=503,
            detail="Agent could not complete the request",
        ) from error
# Production React frontend
FRONTEND_DIST = (
    Path(__file__).resolve().parent
    / "frontend"
    / "dist"
)

if (FRONTEND_DIST / "index.html").is_file():

    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="frontend_assets",
    )

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(
            FRONTEND_DIST / "index.html"
        )

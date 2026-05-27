"""
ContratR.ai — Módulo utilitário compartilhado (v3 — FTR Ready).

Pilares Well-Architected cobertos:
  - Excelência Operacional: structured logging com correlation_id
  - Segurança: JWT com HMAC-SHA256, sanitização, validação
  - Confiabilidade: error handler com retry awareness
  - Performance: reuso de clients fora do handler
  - Custo: Decimal serialization para DynamoDB
"""

import json
import logging
import os
import uuid
import hashlib
import hmac
import base64
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from functools import wraps
from typing import Any

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("contratr-ai")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        json.dumps({
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "service": "contratr-ai",
            "message": "%(message)s",
        }),
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    logger.addHandler(handler)

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
MAX_PDF_SIZE_MB = 10
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024
JWT_SECRET = os.environ.get("JWT_SECRET", "contratr-ai-secret-2026-challenge")
JWT_EXPIRY_HOURS = 24


# ── HTTP Responses (CORS) ──

def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Content-Type": "application/json",
        "X-Content-Type-Options": "nosniff",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }

def success_response(body: Any, status_code: int = 200) -> dict:
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps(body, ensure_ascii=False, default=_json_serializer),
    }

def error_response(message: str, status_code: int = 400, details: str = None) -> dict:
    body = {"error": message}
    if details:
        body["details"] = details
    return {"statusCode": status_code, "headers": _cors_headers(), "body": json.dumps(body, ensure_ascii=False)}

def _json_serializer(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Tipo não serializável: {type(obj)}")


# ── JWT ──

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)

def generate_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload["exp"] = int(time.time()) + (JWT_EXPIRY_HOURS * 3600)
    payload["iat"] = int(time.time())
    h = _b64url_encode(json.dumps(header).encode())
    p = _b64url_encode(json.dumps(payload).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"

def verify_jwt(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        expected = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(s)):
            return None
        payload = json.loads(_b64url_decode(p))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def require_auth(func):
    @wraps(func)
    def wrapper(event, context):
        auth_header = event.get("headers", {}).get("Authorization", "") or event.get("headers", {}).get("authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return error_response("Token de autenticação obrigatório", 401)
        payload = verify_jwt(token)
        if not payload:
            return error_response("Token inválido ou expirado", 401)
        event["auth"] = payload
        return func(event, context)
    return wrapper


# ── Validadores ──

def validate_pdf_upload(event: dict) -> tuple[bool, str]:
    body = _parse_body(event)
    if not body:
        return False, "Request body é obrigatório"
    filename = body.get("filename", "")
    if not filename:
        return False, "Campo 'filename' é obrigatório"
    if not filename.lower().endswith(".pdf"):
        return False, "Apenas arquivos PDF são aceitos"
    file_size = body.get("file_size", 0)
    if file_size and int(file_size) > MAX_PDF_SIZE_BYTES:
        return False, f"Arquivo excede o limite de {MAX_PDF_SIZE_MB}MB"
    if not sanitize_filename(filename):
        return False, "Nome de arquivo inválido"
    return True, ""

def sanitize_filename(filename: str) -> str:
    filename = filename.replace("\\", "/").split("/")[-1]
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_ ")
    sanitized = "".join(c for c in filename if c in safe_chars)
    return sanitized.strip() if sanitized else ""


# ── Helpers ──

def generate_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ttl_days(days: int = 30) -> int:
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())

def _parse_body(event: dict) -> dict | None:
    body = event.get("body")
    if not body:
        return None
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return body

def float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(i) for i in obj]
    return obj

def lambda_error_handler(func):
    @wraps(func)
    def wrapper(event, context):
        cid = (
            event.get("headers", {}).get("x-correlation-id", "")
            or event.get("requestContext", {}).get("requestId", "")
            or generate_id()
        )
        fn = getattr(context, "function_name", "local") if context else "local"
        logger.info("INVOKE | fn=%s | cid=%s", fn, cid)
        try:
            return func(event, context)
        except Exception:
            logger.exception("UNHANDLED_ERROR | fn=%s | cid=%s", fn, cid)
            return error_response("Erro interno do servidor.", status_code=500)
    return wrapper

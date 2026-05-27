"""
ContratR.ai — Auth Login Lambda

POST /auth/login { "email": "...", "password": "..." }
→ { "token": "jwt...", "expires_in": 86400 }

Autenticação simples com operador master único.
Em produção, migrar para Amazon Cognito.
"""

import os
import json
import hashlib

from utils import (
    lambda_error_handler,
    generate_jwt,
    success_response,
    error_response,
    _parse_body,
    logger,
)

MASTER_EMAIL = os.environ.get("MASTER_EMAIL", "admin@contratr.ai")
MASTER_PASSWORD_HASH = os.environ.get(
    "MASTER_PASSWORD_HASH",
    hashlib.sha256("ContraTR@2026!".encode()).hexdigest(),
)


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return error_response("E-mail e senha são obrigatórios", 400)

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if email != MASTER_EMAIL.lower() or password_hash != MASTER_PASSWORD_HASH:
        logger.warning("Login falhou | email=%s", email)
        return error_response("Credenciais inválidas", 401)

    token = generate_jwt({"sub": email, "role": "master"})
    logger.info("Login bem-sucedido | email=%s", email)

    return success_response({
        "token": token,
        "expires_in": 86400,
        "user": {"email": email, "role": "master"},
    })

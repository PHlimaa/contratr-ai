"""
ContratR.ai — External API Lambda

GET /api/v1/analysis/{analysis_id}    → Retorna JSON completo da análise
POST /api/v1/analyze                  → Inicia análise via API (com API key)

Funcionalidade 5: API pública para integração com outros sistemas.
Retorna JSON padronizado com score, cláusulas, riscos e políticas violadas.
Autenticação via API key no header X-API-Key.
"""

import os
import json
import hashlib

import boto3

from utils import (
    lambda_error_handler,
    generate_id,
    now_iso,
    ttl_days,
    success_response,
    error_response,
    _parse_body,
    sanitize_filename,
    logger,
)

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

TABLE_NAME = os.environ["ANALYSIS_TABLE"]
BUCKET_NAME = os.environ.get("CONTRACTS_BUCKET", "")

# API keys simples (em produção, usar API Gateway API Keys ou Cognito)
VALID_API_KEYS = os.environ.get("API_KEYS", "contratr-demo-key-2026,contratr-test-key").split(",")


def _validate_api_key(event: dict) -> bool:
    headers = event.get("headers", {})
    api_key = headers.get("X-API-Key", "") or headers.get("x-api-key", "")
    return api_key in VALID_API_KEYS


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}

    if not _validate_api_key(event):
        return error_response("API key inválida. Envie no header X-API-Key.", 401)

    if method == "GET" and path_params.get("analysis_id"):
        return _get_analysis(path_params["analysis_id"])
    elif method == "POST" and "/api/v1/analyze" in path:
        return _start_analysis(event)
    else:
        return error_response("Rota não encontrada", 404)


def _get_analysis(analysis_id: str) -> dict:
    table = dynamodb.Table(TABLE_NAME)
    r = table.query(
        KeyConditionExpression="analysis_id = :a",
        ExpressionAttributeValues={":a": analysis_id},
        Limit=1,
    )
    items = r.get("Items", [])
    if not items:
        return error_response("Análise não encontrada", 404)

    item = items[0]
    status = item.get("status", "unknown")

    result = {
        "analysis_id": analysis_id,
        "status": status,
        "filename": item.get("filename"),
        "company_id": item.get("company_id"),
        "company_name": item.get("company_name"),
        "created_at": item.get("created_at"),
        "progress": _get_progress(status),
    }

    if status == "error":
        result["error"] = item.get("error_message", "Erro desconhecido")

    if status == "completed" and item.get("analysis_result"):
        analysis = item["analysis_result"]
        result["score"] = analysis.get("score", 0)
        result["score_label"] = analysis.get("score_label", "")
        result["summary"] = analysis.get("summary", "")
        result["policies_violated"] = analysis.get("policies_violated", 0)
        result["policies_total"] = analysis.get("policies_total", 0)
        result["parties"] = analysis.get("parties", {})
        result["contract_info"] = analysis.get("contract_info", {})
        result["clauses"] = analysis.get("clauses", [])
        result["financial_risks"] = analysis.get("financial_risks", [])

    if item.get("entities"):
        result["entities"] = item["entities"]

    return success_response(result)


def _start_analysis(event: dict) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    filename = body.get("filename", "")
    company_id = body.get("company_id", "")

    if not filename or not filename.lower().endswith(".pdf"):
        return error_response("'filename' obrigatório e deve ser .pdf", 422)
    if not company_id:
        return error_response("'company_id' obrigatório", 422)

    analysis_id = generate_id()
    safe_filename = sanitize_filename(filename)
    s3_key = f"uploads/{analysis_id}/{safe_filename}"

    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
            "ContentType": "application/pdf",
            "ServerSideEncryption": "AES256",
        },
        ExpiresIn=300,
    )

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "analysis_id": analysis_id,
            "created_at": now_iso(),
            "status": "pending_upload",
            "filename": safe_filename,
            "file_size": body.get("file_size", 0),
            "s3_key": s3_key,
            "company_id": company_id,
            "source": "external_api",
            "ttl": ttl_days(30),
        }
    )

    return success_response({
        "analysis_id": analysis_id,
        "upload_url": presigned_url,
        "expires_in": 300,
        "polling_url": f"/api/v1/analysis/{analysis_id}",
        "instructions": {
            "step_1": "PUT o PDF no upload_url com headers Content-Type: application/pdf e x-amz-server-side-encryption: AES256",
            "step_2": f"GET /api/v1/analysis/{analysis_id} para acompanhar progresso",
            "step_3": "Quando status=completed, o JSON terá score, clauses, financial_risks",
        },
    }, 201)


def _get_progress(status: str) -> int:
    return {
        "pending_upload": 0, "extracting_text": 20, "text_extracted": 40,
        "analyzing_entities": 50, "entities_extracted": 60,
        "analyzing_with_ai": 80, "completed": 100, "error": -1,
    }.get(status, 0)

"""
ContratR.ai — Analysis History Lambda

GET /companies/{company_id}/analyses          → Lista histórico de análises da empresa
GET /companies/{company_id}/analyses?status=completed → Filtra por status

Funcionalidade 1: Histórico de contratos analisados por empresa.
Mostra contratos em andamento ("analyzing") e concluídos ("completed").
"""

import os
import json

import boto3
from boto3.dynamodb.conditions import Key, Attr

from utils import (
    lambda_error_handler,
    require_auth,
    success_response,
    error_response,
    logger,
)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["ANALYSIS_TABLE"]


@lambda_error_handler
@require_auth
def lambda_handler(event: dict, context) -> dict:
    path_params = event.get("pathParameters") or {}
    company_id = path_params.get("company_id")
    query_params = event.get("queryStringParameters") or {}
    status_filter = query_params.get("status")
    limit = int(query_params.get("limit", "50"))

    if not company_id:
        return error_response("company_id obrigatório", 400)

    table = dynamodb.Table(TABLE_NAME)

    # Scan com filtro por company_id (em produção, usar GSI)
    scan_kwargs = {
        "FilterExpression": Attr("company_id").eq(company_id),
        "Limit": min(limit, 100),
    }

    if status_filter:
        scan_kwargs["FilterExpression"] = (
            Attr("company_id").eq(company_id) & Attr("status").eq(status_filter)
        )

    response = table.scan(**scan_kwargs)
    items = response.get("Items", [])

    # Ordena por created_at (mais recente primeiro)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Remove texto extraído (pesado) do listing
    analyses = []
    for item in items:
        analyses.append({
            "analysis_id": item.get("analysis_id"),
            "filename": item.get("filename"),
            "status": item.get("status"),
            "risk_score": item.get("risk_score"),
            "company_name": item.get("company_name"),
            "created_at": item.get("created_at"),
            "bedrock_completed_at": item.get("bedrock_completed_at"),
            "error_message": item.get("error_message"),
            "progress": _get_progress(item.get("status", "")),
        })

    logger.info("Histórico | company=%s | total=%d", company_id, len(analyses))

    return success_response({
        "analyses": analyses,
        "total": len(analyses),
        "company_id": company_id,
    })


def _get_progress(status: str) -> int:
    return {
        "pending_upload": 0, "extracting_text": 20, "text_extracted": 40,
        "analyzing_entities": 50, "entities_extracted": 60,
        "analyzing_with_ai": 80, "completed": 100, "error": -1,
    }.get(status, 0)

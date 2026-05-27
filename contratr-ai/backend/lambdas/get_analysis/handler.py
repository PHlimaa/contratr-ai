"""
ContratR.ai — Get Analysis v2

GET /contracts/{analysis_id}
Retorna resultado incluindo políticas violadas e nome da empresa.
"""

import os
import re

import boto3

from utils import lambda_error_handler, success_response, error_response, logger

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["ANALYSIS_TABLE"]

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    analysis_id = event.get("pathParameters", {}).get("analysis_id", "")
    if not analysis_id or not UUID_RE.match(analysis_id):
        return error_response("analysis_id inválido", 400)

    table = dynamodb.Table(TABLE_NAME)
    r = table.query(KeyConditionExpression="analysis_id = :a", ExpressionAttributeValues={":a": analysis_id}, Limit=1)
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
    }

    if status == "error":
        result["error_message"] = item.get("error_message", "Erro desconhecido")
    if item.get("entities"):
        result["entities"] = item["entities"]
    if status == "completed" and item.get("analysis_result"):
        result["analysis"] = item["analysis_result"]
        result["risk_score"] = item.get("risk_score", 0)

    progress_map = {
        "pending_upload": 0, "extracting_text": 20, "text_extracted": 40,
        "analyzing_entities": 50, "entities_extracted": 60,
        "analyzing_with_ai": 80, "completed": 100, "error": -1,
    }
    result["progress"] = progress_map.get(status, 0)

    return success_response(result)

"""
ContratR.ai — Companies CRUD Lambda

GET  /companies              → Lista todas as empresas
POST /companies              → Cria nova empresa
GET  /companies/{id}         → Detalhes de uma empresa
PUT  /companies/{id}         → Atualiza empresa
DELETE /companies/{id}       → Remove empresa

Todas as rotas exigem JWT (via require_auth).
"""

import os
import json

import boto3

from utils import (
    lambda_error_handler,
    require_auth,
    generate_id,
    now_iso,
    ttl_days,
    success_response,
    error_response,
    _parse_body,
    logger,
)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("COMPANIES_TABLE", "contratr-ai-companies-dev")


@lambda_error_handler
@require_auth
def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "GET")
    path_params = event.get("pathParameters") or {}
    company_id = path_params.get("company_id")

    table = dynamodb.Table(TABLE_NAME)

    if method == "GET" and not company_id:
        return _list_companies(table)
    elif method == "GET" and company_id:
        return _get_company(table, company_id)
    elif method == "POST":
        return _create_company(table, event)
    elif method == "PUT" and company_id:
        return _update_company(table, company_id, event)
    elif method == "DELETE" and company_id:
        return _delete_company(table, company_id)
    else:
        return error_response("Método não suportado", 405)


def _list_companies(table) -> dict:
    response = table.scan(
        ProjectionExpression="company_id, #n, cnpj, sector, created_at, policies_count",
        ExpressionAttributeNames={"#n": "name"},
    )
    items = response.get("Items", [])
    return success_response({"companies": items, "total": len(items)})


def _get_company(table, company_id: str) -> dict:
    response = table.get_item(Key={"company_id": company_id})
    item = response.get("Item")
    if not item:
        return error_response("Empresa não encontrada", 404)
    return success_response(item)


def _create_company(table, event: dict) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    name = body.get("name", "").strip()
    if not name:
        return error_response("Nome da empresa é obrigatório", 422)

    company_id = generate_id()
    item = {
        "company_id": company_id,
        "name": name,
        "cnpj": body.get("cnpj", "").strip(),
        "sector": body.get("sector", "").strip(),
        "policies": [],
        "policies_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    table.put_item(Item=item)
    logger.info("Empresa criada | id=%s | name=%s", company_id, name)

    return success_response(item, 201)


def _update_company(table, company_id: str, event: dict) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    update_parts = []
    expr_names = {}
    expr_values = {":updated": now_iso()}
    update_parts.append("updated_at = :updated")

    if "name" in body:
        update_parts.append("#n = :name")
        expr_names["#n"] = "name"
        expr_values[":name"] = body["name"].strip()
    if "cnpj" in body:
        update_parts.append("cnpj = :cnpj")
        expr_values[":cnpj"] = body["cnpj"].strip()
    if "sector" in body:
        update_parts.append("sector = :sector")
        expr_values[":sector"] = body["sector"].strip()

    try:
        response = table.update_item(
            Key={"company_id": company_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=expr_names if expr_names else None,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
            ConditionExpression="attribute_exists(company_id)",
        )
        return success_response(response["Attributes"])
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return error_response("Empresa não encontrada", 404)


def _delete_company(table, company_id: str) -> dict:
    table.delete_item(Key={"company_id": company_id})
    logger.info("Empresa removida | id=%s", company_id)
    return success_response({"message": "Empresa removida", "company_id": company_id})

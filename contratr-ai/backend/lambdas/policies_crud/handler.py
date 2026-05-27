"""
ContratR.ai — Policies CRUD Lambda

POST   /companies/{id}/policies          → Adiciona política
DELETE /companies/{id}/policies/{pid}    → Remove política
PUT    /companies/{id}/policies/{pid}    → Atualiza política

Políticas são armazenadas como lista dentro do item da empresa no DynamoDB.
"""

import os
import json

import boto3

from utils import (
    lambda_error_handler,
    require_auth,
    generate_id,
    now_iso,
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
    method = event.get("httpMethod", "POST")
    path_params = event.get("pathParameters") or {}
    company_id = path_params.get("company_id")
    policy_id = path_params.get("policy_id")

    if not company_id:
        return error_response("company_id obrigatório", 400)

    table = dynamodb.Table(TABLE_NAME)

    if method == "POST":
        return _add_policy(table, company_id, event)
    elif method == "DELETE" and policy_id:
        return _remove_policy(table, company_id, policy_id)
    elif method == "PUT" and policy_id:
        return _update_policy(table, company_id, policy_id, event)
    else:
        return error_response("Método não suportado", 405)


def _add_policy(table, company_id: str, event: dict) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    rule = body.get("rule", "").strip()
    if not rule:
        return error_response("Campo 'rule' é obrigatório", 422)

    policy = {
        "policy_id": generate_id(),
        "rule": rule,
        "severity": body.get("severity", "medium"),
        "category": body.get("category", "Geral"),
        "created_at": now_iso(),
    }

    try:
        table.update_item(
            Key={"company_id": company_id},
            UpdateExpression="SET policies = list_append(if_not_exists(policies, :empty), :new_policy), policies_count = policies_count + :one, updated_at = :updated",
            ExpressionAttributeValues={
                ":new_policy": [policy],
                ":empty": [],
                ":one": 1,
                ":updated": now_iso(),
            },
            ConditionExpression="attribute_exists(company_id)",
        )
        logger.info("Política adicionada | company=%s | policy=%s", company_id, policy["policy_id"])
        return success_response(policy, 201)
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return error_response("Empresa não encontrada", 404)


def _remove_policy(table, company_id: str, policy_id: str) -> dict:
    response = table.get_item(Key={"company_id": company_id})
    item = response.get("Item")
    if not item:
        return error_response("Empresa não encontrada", 404)

    policies = item.get("policies", [])
    new_policies = [p for p in policies if p.get("policy_id") != policy_id]

    if len(new_policies) == len(policies):
        return error_response("Política não encontrada", 404)

    table.update_item(
        Key={"company_id": company_id},
        UpdateExpression="SET policies = :policies, policies_count = :count, updated_at = :updated",
        ExpressionAttributeValues={
            ":policies": new_policies,
            ":count": len(new_policies),
            ":updated": now_iso(),
        },
    )

    logger.info("Política removida | company=%s | policy=%s", company_id, policy_id)
    return success_response({"message": "Política removida", "policy_id": policy_id})


def _update_policy(table, company_id: str, policy_id: str, event: dict) -> dict:
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório", 400)

    response = table.get_item(Key={"company_id": company_id})
    item = response.get("Item")
    if not item:
        return error_response("Empresa não encontrada", 404)

    policies = item.get("policies", [])
    updated = False
    for p in policies:
        if p.get("policy_id") == policy_id:
            if "rule" in body:
                p["rule"] = body["rule"]
            if "severity" in body:
                p["severity"] = body["severity"]
            if "category" in body:
                p["category"] = body["category"]
            p["updated_at"] = now_iso()
            updated = True
            break

    if not updated:
        return error_response("Política não encontrada", 404)

    table.update_item(
        Key={"company_id": company_id},
        UpdateExpression="SET policies = :policies, updated_at = :updated",
        ExpressionAttributeValues={":policies": policies, ":updated": now_iso()},
    )

    return success_response({"message": "Política atualizada", "policy_id": policy_id})

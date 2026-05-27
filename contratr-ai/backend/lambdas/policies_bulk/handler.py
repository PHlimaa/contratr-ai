"""
ContratR.ai — Policies Bulk Import Lambda

POST /companies/{company_id}/policies/bulk
Body: { "text": "coloque aqui todo o documento de políticas da empresa..." }

Funcionalidade 3: Usuário cola texto livre com políticas.
O Bedrock (Nova Lite) lê, separa em políticas individuais,
categoriza e sugere severidade. Retorna para o usuário avaliar.
"""

import os
import json
import time

import boto3
from botocore.config import Config

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

bedrock_config = Config(retries={"max_attempts": 3, "mode": "adaptive"}, read_timeout=120)
bedrock_client = boto3.client("bedrock-runtime", config=bedrock_config)
dynamodb = boto3.resource("dynamodb")

COMPANIES_TABLE = os.environ.get("COMPANIES_TABLE", "contratr-ai-companies-dev")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")

PARSE_PROMPT = """Voce e um especialista em compliance corporativo.
Recebeu um texto contendo politicas internas de uma empresa.
Sua tarefa e separar cada politica individual e categoriza-la.

Para cada politica identificada, retorne:
- rule: o texto da politica (limpo e claro)
- category: categoria (ex: Multas, Renovacao, Reajuste, SLA, Garantia, Pagamento, Confidencialidade, Rescisao, Outro)
- severity: nivel sugerido (critical, high, medium, low)
- reasoning: breve justificativa da severidade sugerida (1 frase)

Retorne APENAS JSON no formato:
{
  "policies": [
    {
      "rule": "texto da politica",
      "category": "categoria",
      "severity": "high",
      "reasoning": "justificativa"
    }
  ]
}

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional."""


@lambda_error_handler
@require_auth
def lambda_handler(event: dict, context) -> dict:
    path_params = event.get("pathParameters") or {}
    company_id = path_params.get("company_id")

    if not company_id:
        return error_response("company_id obrigatório", 400)

    body = _parse_body(event)
    if not body or not body.get("text", "").strip():
        return error_response("Campo 'text' com as políticas é obrigatório", 422)

    text = body["text"].strip()
    auto_save = body.get("auto_save", False)

    logger.info("Bulk policies | company=%s | text_len=%d", company_id, len(text))

    # Verifica se empresa existe
    table = dynamodb.Table(COMPANIES_TABLE)
    company = table.get_item(Key={"company_id": company_id}).get("Item")
    if not company:
        return error_response("Empresa não encontrada", 404)

    # Chama Bedrock para parsear
    try:
        parsed = _parse_policies_with_ai(text)
    except Exception as e:
        logger.error("Bedrock falhou no bulk: %s", str(e))
        return error_response(f"Erro ao processar políticas: {str(e)}", 500)

    if not parsed or not parsed.get("policies"):
        return error_response("Não foi possível identificar políticas no texto", 422)

    policies = parsed["policies"]

    # Adiciona IDs temporários para o frontend
    for p in policies:
        p["temp_id"] = generate_id()
        p["status"] = "pending_review"

    # Se auto_save, salva direto no DynamoDB
    if auto_save:
        existing = company.get("policies", [])
        for p in policies:
            existing.append({
                "policy_id": generate_id(),
                "rule": p["rule"],
                "category": p.get("category", "Geral"),
                "severity": p.get("severity", "medium"),
                "created_at": now_iso(),
                "source": "bulk_import",
            })
        table.update_item(
            Key={"company_id": company_id},
            UpdateExpression="SET policies = :p, policies_count = :c, updated_at = :u",
            ExpressionAttributeValues={
                ":p": existing,
                ":c": len(existing),
                ":u": now_iso(),
            },
        )
        logger.info("Bulk save | company=%s | added=%d", company_id, len(policies))

    return success_response({
        "policies": policies,
        "total_identified": len(policies),
        "auto_saved": auto_save,
        "message": "Políticas identificadas. Revise os níveis de criticidade antes de salvar."
        if not auto_save else f"{len(policies)} políticas salvas automaticamente.",
    }, 200 if not auto_save else 201)


def _parse_policies_with_ai(text: str) -> dict | None:
    user_prompt = f"Texto com politicas da empresa:\n\n{text[:8000]}\n\nIdentifique e categorize cada politica."

    body = {
        "messages": [{"role": "user", "content": [{"text": f"{PARSE_PROMPT}\n\n{user_prompt}"}]}],
        "inferenceConfig": {"max_new_tokens": 4096, "temperature": 0.1},
    }

    response = bedrock_client.invoke_model(
        modelId=MODEL_ID, contentType="application/json",
        accept="application/json", body=json.dumps(body),
    )
    resp_body = json.loads(response["body"].read())
    text_resp = resp_body.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")

    # Parse JSON
    try:
        return json.loads(text_resp)
    except json.JSONDecodeError:
        pass
    import re
    m = re.search(r"\{[\s\S]*\}", text_resp)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None

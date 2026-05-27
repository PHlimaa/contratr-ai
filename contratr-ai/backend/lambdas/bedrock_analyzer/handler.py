"""
ContratR.ai — Bedrock Analyzer v4 (Universal: Nova + Claude)
"""

import os
import json
import time

import boto3
from botocore.config import Config

from utils import lambda_error_handler, now_iso, float_to_decimal, logger

bedrock_config = Config(retries={"max_attempts": 3, "mode": "adaptive"}, read_timeout=120)
bedrock_client = boto3.client("bedrock-runtime", config=bedrock_config)
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["ANALYSIS_TABLE"]
COMPANIES_TABLE = os.environ.get("COMPANIES_TABLE", "contratr-ai-companies-dev")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
MAX_TEXT_TOKENS = 8000

SYSTEM_PROMPT = """Voce e um auditor juridico especialista em contratos brasileiros, \
com profundo conhecimento do Codigo Civil, CDC e legislacao empresarial.

Sua tarefa e analisar o texto de um contrato considerando TANTO a legislacao brasileira \
QUANTO as politicas internas da empresa contratante.

Regras:
1. Identifique TODAS as clausulas que apresentem risco
2. Para cada clausula, verifique se viola alguma POLITICA INTERNA da empresa
3. Classifique: "critical", "high", "medium", "low"
4. Cite artigos de lei E politicas internas violadas
5. Gere score de risco 0-100
6. Linguagem simples

Formato JSON estrito:
{
  "score": 0,
  "score_label": "Baixo Risco",
  "summary": "resumo",
  "policies_violated": 0,
  "policies_total": 0,
  "parties": {"contratante": "", "contratada": ""},
  "contract_info": {"valor": "", "vigencia": "", "renovacao": ""},
  "clauses": [
    {
      "title": "Clausula X.Y",
      "risk_level": "critical",
      "original_text": "trecho",
      "analysis": "analise",
      "policy_violated": "politica ou null",
      "recommendation": "sugestao"
    }
  ],
  "financial_risks": [
    {"label": "", "estimated_value": "", "severity": ""}
  ]
}

IMPORTANTE: Responda APENAS com o JSON."""


@lambda_error_handler
def lambda_handler(event, context):
    analysis_id = event.get("analysis_id")
    if not analysis_id:
        return {"statusCode": 400}

    table = dynamodb.Table(TABLE_NAME)
    item = _get_item(table, analysis_id)
    if not item:
        return {"statusCode": 404}

    text = item.get("extracted_text", "")
    entities = item.get("entities", {})
    company_id = item.get("company_id", "")

    _update_status(table, item, "analyzing_with_ai")

    policies = []
    company_name = "Nao informada"
    if company_id:
        ct = dynamodb.Table(COMPANIES_TABLE)
        company = ct.get_item(Key={"company_id": company_id}).get("Item")
        if company:
            policies = company.get("policies", [])
            company_name = company.get("name", company_name)

    prompt = _build_prompt(text, entities, policies, company_name)

    try:
        ai_response = _invoke_bedrock(prompt)
    except Exception as e:
        _update_status(table, item, "error", f"Bedrock: {str(e)}")
        raise

    result = _parse_response(ai_response)
    if not result:
        _update_status(table, item, "error", "Resposta da IA invalida")
        return {"statusCode": 500}

    table.update_item(
        Key={"analysis_id": analysis_id, "created_at": item["created_at"]},
        UpdateExpression="SET #s = :s, analysis_result = :r, risk_score = :sc, company_name = :cn, bedrock_completed_at = :c",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "completed",
            ":r": float_to_decimal(result),
            ":sc": result.get("score", 0),
            ":cn": company_name,
            ":c": now_iso(),
        },
    )
    return {"statusCode": 200}


def _build_prompt(text, entities, policies, company_name):
    parts = [f"Contrato analisado para: {company_name}\n"]
    if policies:
        parts.append("POLITICAS INTERNAS DA EMPRESA:")
        for i, p in enumerate(policies, 1):
            sev = p.get("severity", "medium").upper()
            cat = p.get("category", "Geral")
            parts.append(f"{i}. [{sev}] [{cat}] {p.get('rule', '')}")
        parts.append("")
    parts.append("Texto do Contrato:")
    parts.append(text[:MAX_TEXT_TOKENS * 4])
    if entities:
        parts.append("\nEntidades Detectadas:")
        for cat, items in entities.items():
            if items:
                texts = [e["text"] if isinstance(e, dict) else str(e) for e in items[:10]]
                parts.append(f"- {cat}: {', '.join(texts)}")
    parts.append("\nAnalise e retorne JSON conforme formato especificado.")
    return "\n".join(parts)


def _invoke_bedrock(prompt):
    is_nova = "nova" in MODEL_ID.lower()
    is_claude = "claude" in MODEL_ID.lower() or "anthropic" in MODEL_ID.lower()

    if is_nova:
        body = {
            "messages": [{"role": "user", "content": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
            "inferenceConfig": {"max_new_tokens": 4096, "temperature": 0.1},
        }
    elif is_claude:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.1,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        body = {
            "inputText": f"{SYSTEM_PROMPT}\n\n{prompt}",
            "textGenerationConfig": {"maxTokenCount": 4096, "temperature": 0.1},
        }

    start = time.time()
    response = bedrock_client.invoke_model(
        modelId=MODEL_ID, contentType="application/json",
        accept="application/json", body=json.dumps(body),
    )
    elapsed = round(time.time() - start, 2)
    resp_body = json.loads(response["body"].read())

    if is_nova:
        text = resp_body.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
    elif is_claude:
        text = "".join(b.get("text", "") for b in resp_body.get("content", []) if b.get("type") == "text")
    else:
        text = resp_body.get("results", [{}])[0].get("outputText", "")

    logger.info("Bedrock | model=%s | elapsed=%.2fs", MODEL_ID, elapsed)
    return text


def _parse_response(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    import re
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    fb, lb = text.find("{"), text.rfind("}")
    if fb != -1 and lb != -1:
        try:
            return json.loads(text[fb:lb + 1])
        except json.JSONDecodeError:
            pass
    return None


def _get_item(table, aid):
    r = table.query(KeyConditionExpression="analysis_id = :a", ExpressionAttributeValues={":a": aid}, Limit=1)
    return r.get("Items", [None])[0]


def _update_status(table, item, status, err=None):
    expr = "SET #s = :s, updated_at = :u"
    vals = {":s": status, ":u": now_iso()}
    if err:
        expr += ", error_message = :e"
        vals[":e"] = err
    table.update_item(
        Key={"analysis_id": item["analysis_id"], "created_at": item["created_at"]},
        UpdateExpression=expr, ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues=vals,
    )

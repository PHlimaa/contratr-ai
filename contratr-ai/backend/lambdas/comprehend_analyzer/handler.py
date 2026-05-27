"""
ContratR.ai — Comprehend Analyzer v2

Extrai entidades do texto via Amazon Comprehend.
Fix: converte float → Decimal para DynamoDB.
"""

import os
import json
from decimal import Decimal

import boto3

from utils import lambda_error_handler, now_iso, float_to_decimal, logger

comprehend_client = boto3.client("comprehend")
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

TABLE_NAME = os.environ["ANALYSIS_TABLE"]
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
MAX_BYTES = 5000


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    analysis_id = event.get("analysis_id")
    if not analysis_id:
        return {"statusCode": 400}

    table = dynamodb.Table(TABLE_NAME)
    item = _get_item(table, analysis_id)
    if not item:
        return {"statusCode": 404}

    text = item.get("extracted_text", "")
    if not text:
        return {"statusCode": 422}

    _update_status(table, item, "analyzing_entities")

    entities = _detect_entities(text)
    key_phrases = _detect_key_phrases(text)
    categorized = _categorize(entities)

    table.update_item(
        Key={"analysis_id": analysis_id, "created_at": item["created_at"]},
        UpdateExpression="SET #s = :s, entities = :e, key_phrases = :k, comprehend_completed_at = :c",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "entities_extracted",
            ":e": float_to_decimal(categorized),
            ":k": key_phrases[:50],
            ":c": now_iso(),
        },
    )

    lambda_client.invoke(
        FunctionName=f"contratr-ai-bedrock-{ENVIRONMENT}",
        InvocationType="Event",
        Payload=json.dumps({"analysis_id": analysis_id}),
    )

    return {"statusCode": 200}


def _detect_entities(text):
    all_ents = []
    for chunk in _chunks(text):
        if not chunk.strip():
            continue
        try:
            r = comprehend_client.detect_entities(Text=chunk, LanguageCode="pt")
            all_ents.extend(r.get("Entities", []))
        except Exception:
            continue
    return all_ents


def _detect_key_phrases(text):
    phrases = []
    for chunk in _chunks(text):
        if not chunk.strip():
            continue
        try:
            r = comprehend_client.detect_key_phrases(Text=chunk, LanguageCode="pt")
            for p in r.get("KeyPhrases", []):
                if p["Score"] > 0.8:
                    phrases.append(p["Text"])
        except Exception:
            continue
    seen = set()
    return [p for p in phrases if not (p.lower().strip() in seen or seen.add(p.lower().strip()))]


def _categorize(entities):
    cats = {"pessoas": [], "organizacoes": [], "datas": [], "valores": [], "outros": []}
    tmap = {"PERSON": "pessoas", "ORGANIZATION": "organizacoes", "DATE": "datas", "QUANTITY": "valores"}
    seen = set()
    for e in entities:
        txt, typ, score = e.get("Text", "").strip(), e.get("Type", "OTHER"), e.get("Score", 0)
        if score < 0.7 or len(txt) < 2:
            continue
        key = f"{typ}:{txt.lower()}"
        if key in seen:
            continue
        seen.add(key)
        cat = tmap.get(typ, "outros")
        cats[cat].append({"text": txt, "type": typ, "confidence": Decimal(str(round(score, 3)))})
    for c in cats:
        cats[c] = sorted(cats[c], key=lambda x: x["confidence"], reverse=True)[:20]
    return cats


def _chunks(text):
    encoded = text.encode("utf-8")
    result, start = [], 0
    while start < len(encoded):
        end = min(start + MAX_BYTES, len(encoded))
        if end < len(encoded):
            nl = encoded.rfind(b"\n", start, end)
            if nl > start:
                end = nl + 1
        result.append(encoded[start:end].decode("utf-8", errors="ignore"))
        start = end
    return result


def _get_item(table, aid):
    r = table.query(KeyConditionExpression="analysis_id = :a", ExpressionAttributeValues={":a": aid}, Limit=1)
    return r.get("Items", [None])[0]


def _update_status(table, item, status):
    table.update_item(
        Key={"analysis_id": item["analysis_id"], "created_at": item["created_at"]},
        UpdateExpression="SET #s = :s, updated_at = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":u": now_iso()},
    )

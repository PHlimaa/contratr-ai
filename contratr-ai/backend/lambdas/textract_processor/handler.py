"""
ContratR.ai — Textract Processor v2

Disparada via evento S3. Extrai texto do PDF via Amazon Textract.
"""

import os
import json
import time
from urllib.parse import unquote_plus

import boto3

from utils import lambda_error_handler, now_iso, logger

s3_client = boto3.client("s3")
textract_client = boto3.client("textract")
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

BUCKET_NAME = os.environ["CONTRACTS_BUCKET"]
TABLE_NAME = os.environ["ANALYSIS_TABLE"]
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = unquote_plus(record["s3"]["object"]["key"])

    path_parts = key.split("/")
    if len(path_parts) < 3:
        return {"statusCode": 400, "body": "Invalid S3 key"}

    analysis_id = path_parts[1]
    logger.info("Textract | analysis=%s | key=%s", analysis_id, key)

    table = dynamodb.Table(TABLE_NAME)
    _update_status(table, analysis_id, "extracting_text")

    try:
        extracted_text = _extract_text(bucket, key)
    except Exception as e:
        logger.error("Textract falhou | %s", str(e))
        _update_status(table, analysis_id, "error", str(e))
        raise

    if not extracted_text.strip():
        _update_status(table, analysis_id, "error", "PDF sem texto legível")
        return {"statusCode": 422}

    max_len = 50_000
    stored_text = extracted_text[:max_len]

    table.update_item(
        Key={"analysis_id": analysis_id, "created_at": _get_created_at(table, analysis_id)},
        UpdateExpression="SET #s = :s, extracted_text = :t, text_length = :l, textract_completed_at = :c",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "text_extracted", ":t": stored_text, ":l": len(extracted_text), ":c": now_iso()},
    )

    lambda_client.invoke(
        FunctionName=f"contratr-ai-comprehend-{ENVIRONMENT}",
        InvocationType="Event",
        Payload=json.dumps({"analysis_id": analysis_id}),
    )

    return {"statusCode": 200}


def _extract_text(bucket, key):
    try:
        r = textract_client.detect_document_text(Document={"S3Object": {"Bucket": bucket, "Name": key}})
        return _parse(r)
    except textract_client.exceptions.UnsupportedDocumentException:
        return _extract_multipage(bucket, key)


def _extract_multipage(bucket, key):
    r = textract_client.start_document_text_detection(DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}})
    job_id = r["JobId"]
    for _ in range(60):
        time.sleep(2)
        result = textract_client.get_document_text_detection(JobId=job_id)
        if result["JobStatus"] == "SUCCEEDED":
            break
        if result["JobStatus"] == "FAILED":
            raise RuntimeError("Textract job falhou")
    else:
        raise TimeoutError("Textract timeout")

    text = _parse(result)
    while "NextToken" in result:
        result = textract_client.get_document_text_detection(JobId=job_id, NextToken=result["NextToken"])
        text += "\n" + _parse(result)
    return text


def _parse(response):
    return "\n".join(b["Text"] for b in response.get("Blocks", []) if b["BlockType"] == "LINE")


def _update_status(table, aid, status, error_msg=None):
    ca = _get_created_at(table, aid)
    if not ca:
        return
    expr = "SET #s = :s, updated_at = :u"
    vals = {":s": status, ":u": now_iso()}
    if error_msg:
        expr += ", error_message = :e"
        vals[":e"] = error_msg
    table.update_item(Key={"analysis_id": aid, "created_at": ca}, UpdateExpression=expr, ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues=vals)


def _get_created_at(table, aid):
    r = table.query(KeyConditionExpression="analysis_id = :a", ExpressionAttributeValues={":a": aid}, Limit=1)
    items = r.get("Items", [])
    return items[0]["created_at"] if items else None

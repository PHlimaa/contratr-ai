"""
ContratR.ai — Upload Processor v2

POST /contracts/upload { "filename": "...", "file_size": ..., "company_id": "..." }
→ { "analysis_id": "...", "upload_url": "...", "expires_in": 300 }

Agora exige company_id para vincular a análise a uma empresa.
"""

import os
import json

import boto3

from utils import (
    lambda_error_handler,
    require_auth,
    validate_pdf_upload,
    sanitize_filename,
    generate_id,
    now_iso,
    ttl_days,
    success_response,
    error_response,
    _parse_body,
    logger,
)

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = os.environ["CONTRACTS_BUCKET"]
TABLE_NAME = os.environ["ANALYSIS_TABLE"]
PRESIGNED_URL_EXPIRY = 300


@lambda_error_handler
@require_auth
def lambda_handler(event: dict, context) -> dict:
    is_valid, error_msg = validate_pdf_upload(event)
    if not is_valid:
        return error_response(error_msg, 422)

    body = json.loads(event["body"])
    raw_filename = body["filename"]
    file_size = body.get("file_size", 0)
    company_id = body.get("company_id", "")

    if not company_id:
        return error_response("Campo 'company_id' é obrigatório", 422)

    analysis_id = generate_id()
    safe_filename = sanitize_filename(raw_filename)
    s3_key = f"uploads/{analysis_id}/{safe_filename}"

    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
            "ContentType": "application/pdf",
            "ServerSideEncryption": "AES256",
            "Metadata": {"analysis-id": analysis_id, "company-id": company_id},
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "analysis_id": analysis_id,
            "created_at": now_iso(),
            "status": "pending_upload",
            "filename": safe_filename,
            "file_size": file_size,
            "s3_key": s3_key,
            "company_id": company_id,
            "ttl": ttl_days(30),
        }
    )

    logger.info("Upload criado | analysis=%s | company=%s", analysis_id, company_id)

    return success_response(
        {"analysis_id": analysis_id, "upload_url": presigned_url, "expires_in": PRESIGNED_URL_EXPIRY},
        status_code=201,
    )

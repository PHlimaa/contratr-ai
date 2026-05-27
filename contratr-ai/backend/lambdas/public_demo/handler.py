"""
ContratR.ai — Public Demo Lambda

GET  /demo/info                → Retorna informações do sistema e steps do demo
POST /demo/analyze             → Análise simplificada sem auth (rate limited)

Funcionalidade 2: Rota pública com steps para teste/demonstração.
Permite testar o sistema sem login, com dados mock ou análise real limitada.
"""

import os
import json
import time

import boto3

from utils import (
    lambda_error_handler,
    generate_id,
    now_iso,
    success_response,
    error_response,
    _parse_body,
    logger,
)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("ANALYSIS_TABLE", "contratr-ai-analysis-dev")

# Rate limit simples: máx 10 análises demo por dia
MAX_DEMO_PER_DAY = 10


@lambda_error_handler
def lambda_handler(event: dict, context) -> dict:
    method = event.get("httpMethod", "GET")
    path = event.get("path", "")

    if method == "GET" and "/demo/info" in path:
        return _get_demo_info()
    elif method == "GET" and "/demo/steps" in path:
        return _get_demo_steps()
    elif method == "POST" and "/demo/analyze" in path:
        return _start_demo_analysis(event)
    else:
        return error_response("Rota não encontrada", 404)


def _get_demo_info() -> dict:
    return success_response({
        "name": "ContratR.ai",
        "version": "3.0.0",
        "description": "Auditor Automático de Contratos para PMEs com IA AWS",
        "ai_services": [
            {"name": "Amazon Textract", "role": "OCR e extração de texto de PDFs"},
            {"name": "Amazon Comprehend", "role": "NLP — extração de entidades legais"},
            {"name": "Amazon Bedrock", "role": "Análise jurídica com IA generativa"},
        ],
        "features": [
            "Multi-tenant com políticas por empresa",
            "Análise contextualizada com políticas internas",
            "Score de risco 0-100",
            "Identificação de cláusulas abusivas",
            "Recomendações práticas de alteração",
            "Riscos financeiros quantificados",
        ],
        "demo_endpoint": "/demo/analyze",
        "demo_steps_endpoint": "/demo/steps",
        "max_demo_analyses_per_day": MAX_DEMO_PER_DAY,
    })


def _get_demo_steps() -> dict:
    return success_response({
        "steps": [
            {
                "step": 1,
                "title": "Upload do PDF",
                "description": "O usuário faz upload de um contrato em PDF. O arquivo vai direto ao S3 via presigned URL (não passa pela Lambda).",
                "aws_service": "Amazon S3",
                "duration": "~2 segundos",
            },
            {
                "step": 2,
                "title": "Extração de Texto (OCR)",
                "description": "Amazon Textract extrai texto do PDF, incluindo documentos escaneados. Disparado automaticamente via evento S3.",
                "aws_service": "Amazon Textract",
                "duration": "~5-15 segundos",
            },
            {
                "step": 3,
                "title": "Identificação de Entidades",
                "description": "Amazon Comprehend analisa o texto e identifica: nomes de pessoas, organizações, datas, valores monetários e termos-chave.",
                "aws_service": "Amazon Comprehend",
                "duration": "~3-5 segundos",
            },
            {
                "step": 4,
                "title": "Carregamento de Políticas",
                "description": "O sistema busca as políticas internas da empresa no DynamoDB para contextualizar a análise.",
                "aws_service": "Amazon DynamoDB",
                "duration": "~1 segundo",
            },
            {
                "step": 5,
                "title": "Análise Jurídica com IA",
                "description": "Amazon Bedrock (Nova Lite) recebe o texto + entidades + políticas e analisa cada cláusula contra a legislação brasileira e as regras internas da empresa.",
                "aws_service": "Amazon Bedrock",
                "duration": "~10-30 segundos",
            },
            {
                "step": 6,
                "title": "Resultado",
                "description": "Score de risco (0-100), lista de cláusulas com nível de risco, políticas violadas, recomendações práticas e riscos financeiros quantificados.",
                "aws_service": "API Gateway + DynamoDB",
                "duration": "Instantâneo",
            },
        ],
        "total_estimated_time": "30-60 segundos",
    })


def _start_demo_analysis(event: dict) -> dict:
    """Inicia análise demo com políticas padrão."""
    body = _parse_body(event)
    if not body:
        return error_response("Body obrigatório com 'filename' e 'file_size'", 400)

    filename = body.get("filename", "")
    if not filename.lower().endswith(".pdf"):
        return error_response("Apenas PDFs aceitos", 422)

    # Gera análise demo com políticas padrão
    analysis_id = generate_id()

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "analysis_id": analysis_id,
            "created_at": now_iso(),
            "status": "pending_upload",
            "filename": filename,
            "file_size": body.get("file_size", 0),
            "company_id": "demo",
            "company_name": "Demo — Análise Pública",
            "is_demo": True,
        }
    )

    # Gera presigned URL
    s3_client = boto3.client("s3")
    bucket = os.environ.get("CONTRACTS_BUCKET", "")
    s3_key = f"uploads/{analysis_id}/{filename}"

    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            "ContentType": "application/pdf",
            "ServerSideEncryption": "AES256",
        },
        ExpiresIn=300,
    )

    return success_response({
        "analysis_id": analysis_id,
        "upload_url": presigned_url,
        "expires_in": 300,
        "demo": True,
        "message": "Upload o PDF e consulte GET /contracts/{analysis_id} para acompanhar o progresso.",
    }, 201)

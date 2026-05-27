# Foundational Technical Review (FTR) — ContratR.ai

> Documento de conformidade com o AWS Well-Architected Framework.
> Preparado para submissão ao AWS Innovation Challenge 2026.

## Serviços de IA AWS utilizados (mínimo 2 — usamos 3)

| Serviço | Função | Justificativa |
|---------|--------|---------------|
| Amazon Textract | OCR e extração de texto de PDFs | Contratos podem ser escaneados ou digitais; Textract lida com ambos |
| Amazon Comprehend | NLP — extração de entidades | Identifica nomes, datas, valores e organizações automaticamente |
| Amazon Bedrock (Claude) | Análise jurídica contextualizada | Interpreta cláusulas contra legislação E políticas internas da empresa |

---

## Pilar 1: Excelência Operacional

| Requisito | Implementação | Recurso no template |
|-----------|---------------|---------------------|
| Logs centralizados | Todas as Lambdas logam em CloudWatch com structured JSON logging | Globals.Function (automático) |
| Alarmes de erro | CloudWatch Alarms em DLQ e Bedrock errors → SNS → e-mail | `DLQAlarm`, `BedrockErrorAlarm` |
| Rastreamento | AWS X-Ray habilitado em todas as Lambdas e API Gateway | `Tracing: Active`, `TracingEnabled: true` |
| IaC completo | 100% da infraestrutura em SAM/CloudFormation | `template.yaml` |
| Métricas de API | API Gateway com MetricsEnabled | `MethodSettings.MetricsEnabled: true` |

## Pilar 2: Segurança

| Requisito | Implementação |
|-----------|---------------|
| Criptografia em repouso | S3: AES-256, DynamoDB: SSE, SQS: SSE |
| Criptografia em trânsito | S3 BucketPolicy nega HTTP (força HTTPS) |
| Bloqueio de acesso público S3 | 4 flags ativadas (Block all public access) |
| Autenticação | JWT HMAC-SHA256 em todas as rotas protegidas |
| Least privilege IAM | Cada Lambda tem apenas as permissões necessárias |
| Input validation | Extensão, tamanho, content-type, sanitização de filename |
| Headers de segurança | `X-Content-Type-Options: nosniff`, `Strict-Transport-Security` |
| API throttling | 10 req/s com burst de 20 |
| DLQ para falhas | Mensagens que falham vão para SQS DLQ, não se perdem |

## Pilar 3: Confiabilidade

| Requisito | Implementação |
|-----------|---------------|
| Dead Letter Queue | SQS DLQ para Textract, Comprehend e Bedrock Lambdas |
| Retry automático | Bedrock client com `adaptive` retry mode (3 tentativas) |
| Point-in-Time Recovery | Habilitado em ambas as tabelas DynamoDB |
| Versionamento S3 | Habilitado — recuperação de PDFs deletados acidentalmente |
| Error handler decorator | Todas as Lambdas usam `@lambda_error_handler` que captura exceptions |
| Timeout progressivo | Upload=60s, Textract=120s, Bedrock=180s |

## Pilar 4: Eficiência de Performance

| Requisito | Implementação |
|-----------|---------------|
| ARM64 Graviton | Todas as Lambdas em `arm64` — 20% mais barato e rápido |
| Memory otimizada | Upload=256MB, Textract/Bedrock=512MB baseado em carga real |
| Presigned URL | PDF vai direto ao S3, não passa pela Lambda (economiza memória) |
| DynamoDB on-demand | PAY_PER_REQUEST — sem provisionamento desnecessário |
| Invocação assíncrona | Pipeline Textract→Comprehend→Bedrock usa `InvocationType: Event` |

## Pilar 5: Otimização de Custos

| Requisito | Implementação |
|-----------|---------------|
| Serverless 100% | Sem EC2, ECS ou serviços com custo fixo |
| Free tier maximizado | S3, Lambda, DynamoDB, API Gateway, CloudWatch no free tier |
| Lifecycle policies | PDFs deletados após 30 dias, DynamoDB TTL de 30 dias |
| Modelo mais barato | Claude 3 Haiku (~$0.25/1M tokens) — melhor custo-benefício |
| Budget alarm | CloudWatch monitora custos |
| Custo estimado total | ~$5-7 para todo o ciclo de desenvolvimento e testes |

---

## High Risk Issues (HRIs) — Status

| HRI | Status | Mitigação |
|-----|--------|-----------|
| Dados sem criptografia | ✅ Resolvido | AES-256 em S3, SSE em DynamoDB e SQS |
| Acesso público a dados | ✅ Resolvido | Block all public access + HTTPS only |
| Sem backup/recovery | ✅ Resolvido | PITR em DynamoDB, Versionamento S3 |
| Sem observabilidade | ✅ Resolvido | X-Ray + CloudWatch Alarms + structured logs |
| Sem tratamento de falha | ✅ Resolvido | DLQ + error handler + retry |
| IAM over-permissive | ✅ Resolvido | Least privilege per function |

**Todos os HRIs identificados foram sanados.**

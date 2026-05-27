# Decisões de Segurança — ContratR.ai v3

## IAM — Least Privilege por Lambda

| Lambda | S3 | DynamoDB Analysis | DynamoDB Companies | Textract | Comprehend | Bedrock | SQS DLQ |
|--------|----|-------------------|--------------------|---------|-----------|---------| --------|
| auth_login | — | — | — | — | — | — | — |
| companies_crud | — | — | CRUD | — | — | — | — |
| policies_crud | — | — | CRUD | — | — | — | — |
| upload_processor | PutObject, GetObject | CRUD | — | — | — | — | — |
| textract_processor | GetObject | CRUD | — | ✅ | — | — | Send |
| comprehend_analyzer | — | CRUD | — | — | ✅ | — | Send |
| bedrock_analyzer | — | CRUD | Read | — | — | ✅ | Send |
| get_analysis | — | Read | — | — | — | — | — |

## Criptografia

- S3: AES-256 server-side, policy nega uploads sem SSE header
- DynamoDB: SSE habilitado (AWS managed key)
- SQS DLQ: SSE habilitado
- Trânsito: S3 policy nega HTTP, API Gateway só HTTPS

## Headers de Segurança

Todas as respostas incluem:
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Autenticação

- JWT HMAC-SHA256 com expiração de 24h
- Decorator `@require_auth` em rotas protegidas
- Secret via variável de ambiente (NoEcho no template)

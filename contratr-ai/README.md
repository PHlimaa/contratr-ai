# ContratR.ai v4 — Auditor de Contratos para PMEs

> **AWS Innovation Challenge 2026** | LegalTech SaaS | FTR Ready

## Funcionalidades

### Core
- Login JWT do operador master
- CRUD de empresas com CNPJ e setor
- Gestão de políticas por empresa
- Análise de contratos via Textract + Comprehend + Bedrock
- Score de risco 0-100 com cláusulas e riscos financeiros

### Novas (v4)
- **Histórico de contratos** — lista análises por empresa com status em tempo real
- **Import bulk de políticas com IA** — cole texto livre, a IA separa e categoriza
- **Rota pública para demo** — endpoints sem auth para apresentação
- **Upload assíncrono** — histórico mostra "analisando" com progresso
- **API externa (JSON)** — API key para integração com outros sistemas

## Serviços de IA AWS (3)

| Serviço | Função |
|---------|--------|
| Amazon Textract | OCR e extração de texto |
| Amazon Comprehend | NLP — entidades legais |
| Amazon Bedrock (Nova Lite) | Análise jurídica + parse de políticas |

## Endpoints (14 rotas)

| Método | Path | Auth |
|--------|------|------|
| POST | /auth/login | Não |
| GET/POST | /companies | JWT |
| GET/PUT/DELETE | /companies/{id} | JWT |
| POST | /companies/{id}/policies | JWT |
| DELETE | /companies/{id}/policies/{pid} | JWT |
| POST | /companies/{id}/policies/bulk | JWT |
| GET | /companies/{id}/analyses | JWT |
| POST | /contracts/upload | JWT |
| GET | /contracts/{analysis_id} | Não |
| GET | /demo/info | Não |
| GET | /demo/steps | Não |
| POST | /demo/analyze | Não |
| POST | /api/v1/analyze | API Key |
| GET | /api/v1/analysis/{id} | API Key |

## API Externa

```bash
curl -X POST https://API_URL/api/v1/analyze \
  -H "X-API-Key: contratr-demo-key-2026" \
  -d '{"filename":"contrato.pdf","company_id":"ID"}'

curl https://API_URL/api/v1/analysis/ID \
  -H "X-API-Key: contratr-demo-key-2026"
```

## Deploy

```bash
cd infrastructure && sam build && sam deploy --guided
```

Login: `admin@contratr.ai` / `ContraTR@2026!`

"""Testes unitários — utils v2 (JWT + Decimal)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'layers', 'common', 'python'))
os.environ.update({"CONTRACTS_BUCKET": "test", "ANALYSIS_TABLE": "test", "COMPANIES_TABLE": "test", "ENVIRONMENT": "test", "BEDROCK_MODEL_ID": "test", "JWT_SECRET": "test-secret"})

from decimal import Decimal
from utils import (validate_pdf_upload, sanitize_filename, generate_id, success_response, error_response,
                   now_iso, generate_jwt, verify_jwt, float_to_decimal)


class TestJWT:
    def test_generate_and_verify(self):
        token = generate_jwt({"sub": "admin@test.com", "role": "master"})
        payload = verify_jwt(token)
        assert payload is not None
        assert payload["sub"] == "admin@test.com"
        assert payload["role"] == "master"

    def test_invalid_token(self):
        assert verify_jwt("invalid.token.here") is None

    def test_tampered_token(self):
        token = generate_jwt({"sub": "admin"})
        parts = token.split(".")
        parts[1] = parts[1][:-2] + "XX"
        assert verify_jwt(".".join(parts)) is None

    def test_empty_token(self):
        assert verify_jwt("") is None


class TestFloatToDecimal:
    def test_float(self):
        assert float_to_decimal(0.95) == Decimal("0.95")

    def test_nested_dict(self):
        result = float_to_decimal({"score": 0.8, "name": "test"})
        assert result["score"] == Decimal("0.8")
        assert result["name"] == "test"

    def test_nested_list(self):
        result = float_to_decimal([0.1, 0.2, "text"])
        assert result[0] == Decimal("0.1")
        assert result[2] == "text"

    def test_deep_nesting(self):
        data = {"entities": [{"confidence": 0.95, "text": "ACME"}]}
        result = float_to_decimal(data)
        assert result["entities"][0]["confidence"] == Decimal("0.95")


class TestValidation:
    def test_valid_upload(self):
        event = {"body": json.dumps({"filename": "c.pdf", "file_size": 500})}
        ok, err = validate_pdf_upload(event)
        assert ok is True

    def test_rejects_non_pdf(self):
        event = {"body": json.dumps({"filename": "c.docx", "file_size": 500})}
        ok, err = validate_pdf_upload(event)
        assert ok is False

    def test_rejects_oversized(self):
        event = {"body": json.dumps({"filename": "c.pdf", "file_size": 20_000_000})}
        ok, err = validate_pdf_upload(event)
        assert ok is False

    def test_sanitize_traversal(self):
        r = sanitize_filename("../../etc/passwd")
        assert "/" not in r

    def test_sanitize_normal(self):
        assert sanitize_filename("contrato-2024.pdf") == "contrato-2024.pdf"


class TestHelpers:
    def test_generate_id(self):
        aid = generate_id()
        assert len(aid) == 36 and aid.count("-") == 4

    def test_now_iso(self):
        ts = now_iso()
        assert "T" in ts

    def test_success_response(self):
        r = success_response({"ok": True})
        assert r["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in r["headers"]

    def test_error_response(self):
        r = error_response("Erro", 422)
        assert r["statusCode"] == 422
        assert json.loads(r["body"])["error"] == "Erro"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

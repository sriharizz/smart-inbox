import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "test-data"

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["indexed_cases"] >= 27

def test_process_eml_endpoint():
    eml_file = TEST_DATA_DIR / "emails" / "email_01.eml"
    assert eml_file.exists()
    with open(eml_file, "rb") as f:
        response = client.post(
            "/api/v1/process-eml",
            files={"file": ("email_01.eml", f.read(), "message/rfc822")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["triage"]["primary_category"] == "Safety Report (ICSR)"
    assert "Sarah Jenkins" in data["reporter"]["name"]
    assert "Cardioril" in data["product"]["product_name"]

def test_process_case_04_multi_label_and_photo_review():
    eml_file = TEST_DATA_DIR / "emails" / "email_04.eml"
    assert eml_file.exists()
    with open(eml_file, "rb") as f:
        response = client.post(
            "/api/v1/process-eml",
            files={"file": ("email_04.eml", f.read(), "message/rfc822")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["triage"]["is_multi_label"] is True
    assert data["quality_complaint"] is not None
    assert data["quality_complaint"]["requires_human_review"] is True

def test_literature_screen_and_split():
    pdf_file = TEST_DATA_DIR / "pdfs" / "literature_articles" / "article_03_multicase_series.pdf"
    assert pdf_file.exists()
    with open(pdf_file, "rb") as f:
        response = client.post(
            "/api/v1/literature/screen-and-split",
            files={"file": ("article_03_multicase_series.pdf", f.read(), "application/pdf")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["is_reportable"] is True
    assert data["patient_cases_count"] == 3
    assert len(data["individual_cases"]) == 3

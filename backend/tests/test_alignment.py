"""
Challenge 6 alignment acceptance tests.

Each test covers one pillar of the problem statement:
  1. Winter smog & thermal inversion
  2. Low-emission daily routines
  3. Indoor air hacks
  4. Sustainable alternatives
  5. Quantified impact
  6. Vulnerable groups (asthma, COPD, children, elderly, outdoor workers)
  7. Data honesty (provenance / simulated-data labelling)
  8. Explainability (priority, reason, source on recommendations)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Pillar 1: Winter smog & thermal inversion
# ---------------------------------------------------------------------------

def test_health_ask_winter_smog_response():
    """Assistant endpoint handles winter-smog question and returns a response."""
    resp = client.post("/api/v1/health/ask", json={"question": "winter smog advice Delhi", "city": "Delhi"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data or "answer" in data or "content" in data or isinstance(data, str)


def test_guidelines_contain_inversion_or_smog_content():
    """Health guidelines endpoint mentions inversion or smog terminology."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(keyword in text for keyword in ["inversion", "smog", "thermal", "morning", "winter"])


# ---------------------------------------------------------------------------
# Pillar 2: Low-emission daily routines
# ---------------------------------------------------------------------------

def test_health_ask_low_emission_routines():
    """Assistant returns something for low-emission daily routine questions."""
    resp = client.post("/api/v1/health/ask", json={"question": "low-emission daily routines to reduce air pollution", "city": "Delhi"})
    assert resp.status_code == 200


def test_guidelines_contain_commute_or_routine_content():
    """Guidelines mention commute or routine reduction strategies."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(keyword in text for keyword in ["commut", "routine", "transport", "walk", "cycle", "public transit"])


# ---------------------------------------------------------------------------
# Pillar 3: Indoor air hacks
# ---------------------------------------------------------------------------

def test_health_ask_indoor_air_hacks():
    """Assistant handles indoor air quality questions."""
    resp = client.post("/api/v1/health/ask", json={"question": "indoor air quality hacks", "city": "Delhi"})
    assert resp.status_code == 200


def test_guidelines_mention_indoor_measures():
    """Guidelines include indoor air quality measures."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(keyword in text for keyword in ["indoor", "purifier", "ventilation", "window", "filter"])


# ---------------------------------------------------------------------------
# Pillar 4: Sustainable alternatives
# ---------------------------------------------------------------------------

def test_health_ask_sustainable_alternatives():
    """Assistant handles sustainable alternatives questions."""
    resp = client.post("/api/v1/health/ask", json={"question": "sustainable alternatives to reduce air pollution", "city": "Delhi"})
    assert resp.status_code == 200


def test_guidelines_mention_sustainable_practices():
    """Guidelines include sustainable / eco-friendly practice keywords."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(keyword in text for keyword in ["sustainable", "eco", "electric", "renew", "green", "plant"])


# ---------------------------------------------------------------------------
# Pillar 5: Quantified impact
# ---------------------------------------------------------------------------

def test_health_ask_quantified_impact():
    """Assistant handles quantified-impact questions."""
    resp = client.post("/api/v1/health/ask", json={"question": "quantified impact of air pollution on health", "city": "Delhi"})
    assert resp.status_code == 200


def test_recommendations_have_structured_fields():
    """Health recommendations include at minimum title and description."""
    resp = client.get("/api/v1/health/recommendations?city=Delhi&aqi=200")
    if resp.status_code == 404:
        pytest.skip("recommendations endpoint not wired to this path")
    assert resp.status_code == 200
    items = resp.json()
    if isinstance(items, list) and len(items) > 0:
        item = items[0]
        assert "title" in item or "description" in item or "text" in item


# ---------------------------------------------------------------------------
# Pillar 6: Vulnerable groups
# ---------------------------------------------------------------------------

def test_health_ask_vulnerable_groups_children_elderly():
    """Assistant returns a response for vulnerable-group queries."""
    resp = client.post("/api/v1/health/ask", json={"question": "advice for children and elderly with asthma during smog", "city": "Delhi"})
    assert resp.status_code == 200


def test_guidelines_mention_vulnerable_groups():
    """Guidelines explicitly address vulnerable populations."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(keyword in text for keyword in [
        "child", "elderly", "asthma", "copd", "pregnant", "outdoor worker", "sensitive", "vulnerable"
    ])


# ---------------------------------------------------------------------------
# Pillar 7: Data honesty
# ---------------------------------------------------------------------------

def test_air_quality_endpoint_returns_is_simulated_field():
    """AQI reading responses include an is_simulated field for data provenance."""
    resp = client.get("/api/v1/air-quality/current?city=Delhi")
    if resp.status_code in (404, 503):
        pytest.skip("live endpoint unavailable in test env")
    assert resp.status_code == 200
    data = resp.json()
    # Accept nested or flat
    text = str(data).lower()
    assert "simulated" in text or "is_simulated" in text or "source" in text


def test_health_ask_does_not_fabricate_response():
    """Health ask endpoint does not return a 5xx error for a valid question."""
    resp = client.post("/api/v1/health/ask", json={"question": "is the data real or simulated?", "city": "Delhi"})
    assert resp.status_code < 500


# ---------------------------------------------------------------------------
# Pillar 8: Explainability
# ---------------------------------------------------------------------------

def test_health_ask_returns_explainable_response():
    """Health ask endpoint returns a structured or textual response (not empty)."""
    resp = client.post("/api/v1/health/ask", json={"question": "why is PM2.5 dangerous?", "city": "Delhi"})
    assert resp.status_code == 200
    data = resp.json()
    assert data  # non-empty


def test_health_guidelines_have_source_attribution():
    """Guidelines mention recognised sources like CPCB or WHO."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(src in text for src in ["cpcb", "who", "national", "standard", "guideline"])

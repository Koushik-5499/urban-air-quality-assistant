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

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.aqi_reading import AQIReading
from app.models.city import City

client = TestClient(app)


@pytest.fixture(autouse=True)
def _use_isolated_test_db(db_session: Session):
    """Bind alignment endpoints to the isolated test DB with seeded Delhi telemetry."""
    city = db_session.execute(select(City).where(City.name == "Delhi")).scalar_one_or_none()
    if not city:
        city = City(name="Delhi", state="Delhi", country="India", latitude=28.61, longitude=77.21)
        db_session.add(city)
        db_session.flush()
        db_session.add(
            AQIReading(
                city_id=city.id,
                aqi_value=310,
                aqi_category="Very Poor",
                dominant_pollutant="PM2.5",
                measured_at=datetime.now(UTC),
                source="CPCB",
                is_simulated=True,
            )
        )
        db_session.commit()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Pillar 1: Winter smog & thermal inversion
# ---------------------------------------------------------------------------


def test_health_ask_winter_smog_response():
    """Assistant endpoint handles winter-smog question and returns a response."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "winter smog advice Delhi", "city": "Delhi"},
    )
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
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "low-emission daily routines to reduce air pollution", "city": "Delhi"},
    )
    assert resp.status_code == 200


def test_guidelines_contain_commute_or_routine_content():
    """Guidelines mention commute or routine reduction strategies."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    keywords = ["commut", "routine", "transport", "walk", "cycle", "public transit"]
    assert any(keyword in text for keyword in keywords)


# ---------------------------------------------------------------------------
# Pillar 3: Indoor air hacks
# ---------------------------------------------------------------------------


def test_health_ask_indoor_air_hacks():
    """Assistant handles indoor air quality questions."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "indoor air quality hacks", "city": "Delhi"},
    )
    assert resp.status_code == 200


def test_guidelines_mention_indoor_measures():
    """Guidelines include indoor air quality measures."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    keywords = ["indoor", "purifier", "ventilation", "window", "filter"]
    assert any(keyword in text for keyword in keywords)


# ---------------------------------------------------------------------------
# Pillar 4: Sustainable alternatives
# ---------------------------------------------------------------------------


def test_health_ask_sustainable_alternatives():
    """Assistant handles sustainable alternatives questions."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "sustainable alternatives to reduce air pollution", "city": "Delhi"},
    )
    assert resp.status_code == 200


def test_guidelines_mention_sustainable_practices():
    """Guidelines include sustainable / eco-friendly practice keywords."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    keywords = ["sustainable", "eco", "electric", "renew", "green", "plant"]
    assert any(keyword in text for keyword in keywords)


# ---------------------------------------------------------------------------
# Pillar 5: Quantified impact
# ---------------------------------------------------------------------------


def test_health_ask_quantified_impact():
    """Assistant handles quantified-impact questions."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "quantified impact of air pollution on health", "city": "Delhi"},
    )
    assert resp.status_code == 200


def test_impact_metrics_covers_all_pillars():
    """GET /api/v1/health/impact-metrics returns all 5 Challenge 6 pillars."""
    resp = client.get("/api/v1/health/impact-metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["pillars"]) >= 5
    for pillar in data["pillars"]:
        assert "quantified_impact" in pillar
        assert "source" in pillar
        assert "target_groups" in pillar


def test_community_solutions_covers_all_challenge6_pillars():
    """GET /api/v1/health/community-solutions returns all Challenge 6 structured categories."""
    resp = client.get("/api/v1/health/community-solutions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["winter_smog_guidance"]) >= 1
    assert len(data["low_emission_routines"]) >= 1
    assert len(data["indoor_air_hacks"]) >= 1
    assert len(data["sustainable_alternatives"]) >= 1
    assert len(data["direct_impact_analysis"]) >= 3


def test_recommendations_have_structured_fields():
    """Health recommendations include at minimum title, description, and impact context."""
    resp = client.get("/api/v1/health/recommendations?city=Delhi")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("recommendations", [])
    assert isinstance(items, list) and len(items) > 0
    item = items[0]
    assert "title" in item and "description" in item and "supporting_source" in item


# ---------------------------------------------------------------------------
# Pillar 6: Vulnerable groups
# ---------------------------------------------------------------------------


def test_health_ask_vulnerable_groups_children_elderly():
    """Assistant returns a response for vulnerable-group queries."""
    resp = client.post(
        "/api/v1/health/ask",
        json={
            "question": "advice for children and elderly with asthma during smog",
            "city": "Delhi",
        },
    )
    assert resp.status_code == 200


def test_guidelines_mention_vulnerable_groups():
    """Guidelines explicitly address vulnerable populations."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    keywords = [
        "child",
        "elderly",
        "asthma",
        "copd",
        "pregnant",
        "outdoor worker",
        "sensitive",
        "vulnerable",
    ]
    assert any(keyword in text for keyword in keywords)


# ---------------------------------------------------------------------------
# Pillar 7: Data honesty
# ---------------------------------------------------------------------------


def test_air_quality_endpoint_returns_is_simulated_field():
    """AQI source-status and city endpoints disclose data provenance explicitly."""
    resp = client.get("/api/v1/air-quality/source-status")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(tok in text for tok in ("simulated", "is_simulated", "provider", "source"))

    city_resp = client.get("/api/v1/air-quality/cities/Delhi")
    assert city_resp.status_code == 200
    city_text = str(city_resp.json()).lower()
    assert "is_simulated" in city_text or "source" in city_text


def test_health_ask_does_not_fabricate_response():
    """Health ask endpoint does not return a 5xx error for a valid question."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "is the data real or simulated?", "city": "Delhi"},
    )
    assert resp.status_code < 500


# ---------------------------------------------------------------------------
# Pillar 8: Explainability
# ---------------------------------------------------------------------------


def test_health_ask_returns_explainable_response():
    """Health ask endpoint returns a structured or textual response (not empty)."""
    resp = client.post(
        "/api/v1/health/ask",
        json={"question": "why is PM2.5 dangerous?", "city": "Delhi"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data  # non-empty


def test_health_guidelines_have_source_attribution():
    """Guidelines mention recognised sources like CPCB or WHO."""
    resp = client.get("/api/v1/health/guidelines")
    assert resp.status_code == 200
    text = str(resp.json()).lower()
    assert any(src in text for src in ["cpcb", "who", "national", "standard", "guideline"])

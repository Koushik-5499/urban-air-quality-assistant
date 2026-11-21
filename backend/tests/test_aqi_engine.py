"""Comprehensive automated tests for CPCB NAQI calculation engine, sub-indices, and API endpoints."""

import pytest
from sqlalchemy.orm import Session

from app.db.seed import seed_cities
from app.integrations.mock.provider import MockAQIProvider
from app.models.aqi_reading import AQIReading
from app.services.aqi.calculator import AQICalculator
from app.services.aqi.dominant_pollutant import DominantPollutantResolver
from app.services.aqi.processor import AQIProcessingService
from app.services.aqi.validators import AQIValidator
from app.services.aqi_data_service import AQIDataService

# ---------------------------------------------------------
# Unit Tests: Breakpoints & Sub-Index Calculations
# ---------------------------------------------------------

def test_pm25_sub_index_breakpoints():
    """Verify PM2.5 calculations across all CPCB breakpoint boundaries."""
    # Boundary tests
    assert AQICalculator.calculate_sub_index("PM2.5", 0.0) == 0
    assert AQICalculator.calculate_sub_index("PM2.5", 30.0) == 50
    assert AQICalculator.calculate_sub_index("PM2.5", 60.0) == 100
    assert AQICalculator.calculate_sub_index("PM2.5", 90.0) == 200
    assert AQICalculator.calculate_sub_index("PM2.5", 120.0) == 300
    assert AQICalculator.calculate_sub_index("PM2.5", 250.0) == 400

    # Intermediate values
    assert AQICalculator.calculate_sub_index("PM2.5", 15.0) == 25
    # (45 - 30) / (60 - 30) * (100 - 51) + 51 = 0.5 * 49 + 51 = 75.5 -> 76
    assert AQICalculator.calculate_sub_index("PM2.5", 45.0) == 76

    # Severe threshold and ceiling
    assert AQICalculator.calculate_sub_index("PM2.5", 380.0) == 500
    assert AQICalculator.calculate_sub_index("PM2.5", 600.0) == 500


def test_pm10_sub_index_breakpoints():
    """Verify PM10 calculations across CPCB breakpoint boundaries."""
    assert AQICalculator.calculate_sub_index("PM10", 0.0) == 0
    assert AQICalculator.calculate_sub_index("PM10", 50.0) == 50
    assert AQICalculator.calculate_sub_index("PM10", 100.0) == 100
    assert AQICalculator.calculate_sub_index("PM10", 250.0) == 200
    assert AQICalculator.calculate_sub_index("PM10", 350.0) == 300
    assert AQICalculator.calculate_sub_index("PM10", 430.0) == 400
    assert AQICalculator.calculate_sub_index("PM10", 75.0) == 76
    assert AQICalculator.calculate_sub_index("PM10", 510.0) == 500


def test_no2_sub_index_breakpoints():
    """Verify NO2 calculations across CPCB breakpoint boundaries."""
    assert AQICalculator.calculate_sub_index("NO2", 0.0) == 0
    assert AQICalculator.calculate_sub_index("NO2", 40.0) == 50
    assert AQICalculator.calculate_sub_index("NO2", 80.0) == 100
    assert AQICalculator.calculate_sub_index("NO2", 180.0) == 200
    assert AQICalculator.calculate_sub_index("NO2", 280.0) == 300
    assert AQICalculator.calculate_sub_index("NO2", 400.0) == 400


def test_so2_sub_index_breakpoints():
    """Verify SO2 calculations across CPCB breakpoint boundaries."""
    assert AQICalculator.calculate_sub_index("SO2", 0.0) == 0
    assert AQICalculator.calculate_sub_index("SO2", 40.0) == 50
    assert AQICalculator.calculate_sub_index("SO2", 80.0) == 100
    assert AQICalculator.calculate_sub_index("SO2", 380.0) == 200
    assert AQICalculator.calculate_sub_index("SO2", 800.0) == 300
    assert AQICalculator.calculate_sub_index("SO2", 1600.0) == 400


def test_co_sub_index_breakpoints():
    """Verify CO calculations using mg/m3 unit."""
    assert AQICalculator.calculate_sub_index("CO", 0.0, unit="mg/m³") == 0
    assert AQICalculator.calculate_sub_index("CO", 1.0, unit="mg/m³") == 50
    assert AQICalculator.calculate_sub_index("CO", 2.0, unit="mg/m³") == 100
    assert AQICalculator.calculate_sub_index("CO", 10.0, unit="mg/m³") == 200
    assert AQICalculator.calculate_sub_index("CO", 17.0, unit="mg/m³") == 300
    assert AQICalculator.calculate_sub_index("CO", 34.0, unit="mg/m³") == 400
    assert AQICalculator.calculate_sub_index("CO", 51.0, unit="mg/m³") == 500


def test_o3_sub_index_breakpoints():
    """Verify O3 calculations across CPCB breakpoint boundaries."""
    assert AQICalculator.calculate_sub_index("O3", 0.0) == 0
    assert AQICalculator.calculate_sub_index("O3", 50.0) == 50
    assert AQICalculator.calculate_sub_index("O3", 100.0) == 100
    assert AQICalculator.calculate_sub_index("O3", 168.0) == 200
    assert AQICalculator.calculate_sub_index("O3", 208.0) == 300
    assert AQICalculator.calculate_sub_index("O3", 748.0) == 400


def test_nh3_and_pb_sub_index_breakpoints():
    """Verify NH3 and Pb calculations."""
    assert AQICalculator.calculate_sub_index("NH3", 200.0) == 50
    assert AQICalculator.calculate_sub_index("NH3", 400.0) == 100

    assert AQICalculator.calculate_sub_index("Pb", 0.5) == 50
    assert AQICalculator.calculate_sub_index("Pb", 1.0) == 100


# ---------------------------------------------------------
# Unit Tests: Input Validation & Edge Cases
# ---------------------------------------------------------

def test_negative_concentration_rejected():
    """Negative concentration must be rejected by validator and calculator."""
    is_valid, msg = AQIValidator.validate_concentration("PM2.5", -10.0, "µg/m³")
    assert is_valid is False
    assert "non-negative" in msg
    assert AQICalculator.calculate_sub_index("PM2.5", -10.0) is None


def test_incompatible_unit_rejected():
    """Incompatible units (e.g. CO in ug/m3 or PM2.5 in ppm) must be rejected."""
    # CO requires mg/m³
    is_valid_co, msg_co = AQIValidator.validate_concentration("CO", 1.5, "µg/m³")
    assert is_valid_co is False
    assert "Incompatible unit" in msg_co
    assert AQICalculator.calculate_sub_index("CO", 1.5, unit="µg/m³") is None

    # PM2.5 requires µg/m³
    is_valid_pm, _ = AQIValidator.validate_concentration("PM2.5", 35.0, "ppm")
    assert is_valid_pm is False


def test_unsupported_pollutant_rejected():
    """Pollutant code not recognized by CPCB NAQI must be rejected."""
    is_valid, msg = AQIValidator.validate_concentration("UNKNOWN_GAS", 15.0, "µg/m³")
    assert is_valid is False
    assert "not supported" in msg


# ---------------------------------------------------------
# Unit Tests: Dominant Pollutant & Tie-Breaking
# ---------------------------------------------------------

def test_dominant_pollutant_clear_winner():
    """Pollutant with highest sub-index is selected as dominant."""
    sub_indices = {"PM2.5": 145, "PM10": 110, "NO2": 65}
    assert DominantPollutantResolver.resolve_dominant_pollutant(sub_indices) == "PM2.5"


def test_dominant_pollutant_tie_breaking():
    """Ties are broken deterministically by health priority: PM2.5 > PM10 > NO2 > O3 > CO > SO2."""
    # Tie between PM2.5 and PM10 -> PM2.5 wins
    sub_indices_1 = {"PM2.5": 180, "PM10": 180, "NO2": 80}
    assert DominantPollutantResolver.resolve_dominant_pollutant(sub_indices_1) == "PM2.5"

    # Tie between NO2 and SO2 -> NO2 wins
    sub_indices_2 = {"NO2": 95, "SO2": 95, "PM2.5": 60}
    assert DominantPollutantResolver.resolve_dominant_pollutant(sub_indices_2) == "NO2"


# ---------------------------------------------------------
# Unit Tests: CPCB Data Sufficiency Rule
# ---------------------------------------------------------

def test_cpcb_sufficiency_rule():
    """CPCB requires at least 3 pollutants, at least one being PM2.5 or PM10."""
    # Case 1: Less than 3 pollutants -> Insufficient
    is_suff, _, missing = AQIValidator.evaluate_data_sufficiency(["PM2.5", "NO2"])
    assert is_suff is False
    assert any("At least 3" in m for m in missing)

    # Case 2: 3 pollutants, but neither PM2.5 nor PM10 -> Insufficient
    is_suff, _, missing = AQIValidator.evaluate_data_sufficiency(["NO2", "SO2", "CO"])
    assert is_suff is False
    assert any("particulate" in m for m in missing)

    # Case 3: 3 pollutants including PM2.5 -> Sufficient
    is_suff, _, missing = AQIValidator.evaluate_data_sufficiency(["PM2.5", "NO2", "CO"])
    assert is_suff is True
    assert len(missing) == 0

    # Case 4: 3 pollutants including PM10 -> Sufficient
    is_suff, _, missing = AQIValidator.evaluate_data_sufficiency(["PM10", "SO2", "O3"])
    assert is_suff is True
    assert len(missing) == 0


def test_overall_aqi_calculation_sufficient():
    """Overall AQI equals highest sub-index with proper category and dominant pollutant."""
    sub_indices = {
        "PM2.5": 145,  # Moderate
        "PM10": 95,    # Satisfactory
        "NO2": 60,     # Satisfactory
        "SO2": 45,     # Good
    }
    aqi, category, dominant, is_suff, expl, _ = AQICalculator.calculate_overall_aqi(sub_indices)
    assert is_suff is True
    assert aqi == 145
    assert category == "Moderately Polluted"
    assert dominant == "PM2.5"


def test_overall_aqi_calculation_insufficient():
    """Insufficient data returns None for overall AQI while identifying dominant pollutant."""
    sub_indices = {
        "PM2.5": 85,
        "NO2": 40,
    }
    aqi, category, dominant, is_suff, expl, missing = AQICalculator.calculate_overall_aqi(sub_indices)
    assert is_suff is False
    assert aqi is None
    assert category is None
    assert dominant == "PM2.5"
    assert len(missing) > 0


# ---------------------------------------------------------
# Integration Tests: Processor & Database Persistence
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_aqi_batch_processor_and_deduplication(db_session: Session):
    """Verify batch processing creates AQIReading records without duplicating on second run."""
    seed_cities(db_session)

    # Ingest 6 criteria pollutants for Delhi using mock provider
    mock_provider = MockAQIProvider()
    data_service = AQIDataService(provider=mock_provider)
    await data_service.sync_and_persist(db=db_session, city="Delhi")

    # Run processing
    res1 = AQIProcessingService.process_and_persist_aqi(db=db_session)
    assert res1.success is True
    assert res1.aqi_records_created > 0

    aqi_count_1 = db_session.query(AQIReading).count()
    assert aqi_count_1 > 0

    # Running processing again on the same measurements must NOT duplicate AQIReading records
    res2 = AQIProcessingService.process_and_persist_aqi(db=db_session)
    assert res2.aqi_records_created == 0
    assert db_session.query(AQIReading).count() == aqi_count_1


# ---------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_api_aqi_endpoints(client, db_session: Session):
    """Verify all /api/v1/aqi endpoints return correct responses and status codes."""
    seed_cities(db_session)

    # Ingest measurements for Delhi
    mock_provider = MockAQIProvider()
    data_service = AQIDataService(provider=mock_provider)
    await data_service.sync_and_persist(db=db_session, city="Delhi")

    # 1. GET /api/v1/aqi/calculate?city=Delhi
    calc_resp = await client.get("/api/v1/aqi/calculate?city=Delhi")
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["city_name"] == "Delhi"
    assert calc_data["aqi"] is not None
    assert calc_data["data_quality"] == "sufficient"
    assert "PM2.5" in calc_data["pollutant_subindices"]

    # 2. GET /api/v1/aqi/pollutant-subindices?city=Delhi
    sub_resp = await client.get("/api/v1/aqi/pollutant-subindices?city=Delhi")
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert "sub_indices" in sub_data
    assert "dominant_pollutant" in sub_data

    # 3. POST /api/v1/aqi/process
    process_resp = await client.post("/api/v1/aqi/process")
    assert process_resp.status_code == 200
    proc_data = process_resp.json()
    assert proc_data["success"] is True

    # 4. GET /api/v1/aqi/latest?city=Delhi
    latest_resp = await client.get("/api/v1/aqi/latest?city=Delhi")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["city_name"] == "Delhi"
    assert latest_data["aqi_value"] > 0
    assert latest_data["aqi_category"] in ["Good", "Satisfactory", "Moderately Polluted", "Poor", "Very Poor", "Severe"]

    # 5. GET /api/v1/aqi/history?city=Delhi
    history_resp = await client.get("/api/v1/aqi/history?city=Delhi")
    assert history_resp.status_code == 200
    hist_data = history_resp.json()
    assert hist_data["total"] >= 1
    assert len(hist_data["items"]) >= 1

    # 6. GET /api/v1/aqi/calculate?city=NonExistentCity -> 404
    resp_404 = await client.get("/api/v1/aqi/calculate?city=NonExistentCity")
    assert resp_404.status_code == 404


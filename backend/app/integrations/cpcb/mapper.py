"""Data mapper transforming CPCB data.gov.in raw records into NormalizedObservation schemas."""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.integrations.base import NormalizedObservation

logger = get_logger("app.integrations.cpcb.mapper")

# Indian Standard Time (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Pollutant code standardizations
POLLUTANT_MAP = {
    "PM2.5": "PM2.5",
    "PM 2.5": "PM2.5",
    "PM10": "PM10",
    "PM 10": "PM10",
    "NO2": "NO2",
    "SO2": "SO2",
    "CO": "CO",
    "OZONE": "O3",
    "O3": "O3",
    "NH3": "NH3",
}

# Unit standardizations
UNIT_MAP = {
    "µg/m3": "µg/m³",
    "ug/m3": "µg/m³",
    "µg/m³": "µg/m³",
    "mg/m3": "mg/m³",
    "mg/m³": "mg/m³",
    "ppm": "ppm",
    "ppb": "ppb",
}


class CPCBRecordMapper:
    """Transforms raw CPCB records into domain observation objects."""

    @classmethod
    def parse_datetime(cls, date_str: str | None) -> datetime:
        """Parse CPCB timestamp (IST: DD-MM-YYYY HH:MM:SS) and normalize to UTC."""
        if not date_str or not isinstance(date_str, str):
            return datetime.now(UTC)

        cleaned = date_str.strip()
        # Primary CPCB format: "20-11-2026 18:00:00"
        for fmt in ("%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt_naive = datetime.strptime(cleaned, fmt)
                dt_ist = dt_naive.replace(tzinfo=IST)
                return dt_ist.astimezone(UTC)
            except ValueError:
                continue

        # ISO format fallback
        try:
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            return dt.astimezone(UTC)
        except Exception:
            logger.warning("Unrecognized date format '%s', falling back to current UTC time", date_str)
            return datetime.now(UTC)

    @classmethod
    def parse_float(cls, value: Any) -> float | None:
        """Safely parse float value, returning None for missing or invalid values."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        val_str = str(value).strip().replace(",", "")
        if val_str.upper() in ("NA", "N/A", "-", "", "NULL", "NONE"):
            return None
        try:
            return float(val_str)
        except ValueError:
            return None

    @classmethod
    def map_record(cls, record: dict[str, Any]) -> NormalizedObservation | None:
        """Convert a single CPCB record dictionary into a NormalizedObservation."""
        if not isinstance(record, dict):
            return None

        # Extract location fields
        city = (record.get("city") or record.get("City") or "").strip()
        state = (record.get("state") or record.get("State") or "").strip()
        country = (record.get("country") or record.get("Country") or "India").strip()
        station = (record.get("station") or record.get("Station") or f"{city} Monitoring Station").strip()

        if not city or not state:
            return None

        # Extract and normalize pollutant code
        raw_pollutant = str(record.get("pollutant_id") or record.get("Pollutant") or "").strip().upper()
        if not raw_pollutant:
            return None
        pollutant_code = POLLUTANT_MAP.get(raw_pollutant, raw_pollutant)

        # Extract concentration (prefer avg, then max, then min)
        avg_val = cls.parse_float(record.get("pollutant_avg") or record.get("avg") or record.get("Avg"))
        if avg_val is None:
            avg_val = cls.parse_float(record.get("pollutant_max"))
        if avg_val is None:
            avg_val = cls.parse_float(record.get("pollutant_min"))

        # Skip records without valid non-negative concentration
        if avg_val is None or avg_val < 0.0:
            return None

        # Extract and normalize unit
        raw_unit = str(record.get("pollutant_unit") or record.get("unit") or "µg/m³").strip()
        unit = UNIT_MAP.get(raw_unit.lower(), raw_unit)

        # Parse timestamp
        last_update = record.get("last_update") or record.get("date") or record.get("timestamp")
        measured_at = cls.parse_datetime(last_update)

        # Parse coordinates if present
        lat = cls.parse_float(record.get("latitude") or record.get("lat"))
        lng = cls.parse_float(record.get("longitude") or record.get("lon") or record.get("lng"))

        external_id = str(record.get("id")) if record.get("id") else None

        return NormalizedObservation(
            country=country,
            state=state,
            city=city,
            station_name=station,
            external_station_id=external_id,
            latitude=lat,
            longitude=lng,
            pollutant_code=pollutant_code,
            concentration=round(avg_val, 2),
            unit=unit,
            measured_at=measured_at,
            source="CPCB",
            is_simulated=False,
            raw_data=record,
        )

    @classmethod
    def map_records(cls, raw_data: dict[str, Any]) -> list[NormalizedObservation]:
        """Map entire CPCB response records array."""
        records = raw_data.get("records", [])
        if not isinstance(records, list):
            return []

        observations: list[NormalizedObservation] = []
        for rec in records:
            obs = cls.map_record(rec)
            if obs is not None:
                observations.append(obs)

        return observations


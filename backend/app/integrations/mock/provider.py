"""Mock AQI data provider for testing and offline development."""

from datetime import UTC, datetime

from app.integrations.base import BaseAQIProvider, NormalizedObservation, ProviderMetadata

# Simulated observations matching the 10 supported Indian cities
MOCK_CITY_STATIONS = [
    ("Coimbatore", "Tamil Nadu", "SIDCO Industrial Estate Sensor", 11.0168, 76.9558),
    ("Chennai", "Tamil Nadu", "Adyar Coastal Station", 13.0827, 80.2707),
    ("Bengaluru", "Karnataka", "BTM Layout Node", 12.9716, 77.5946),
    ("Hyderabad", "Telangana", "HITEC City Sensor", 17.3850, 78.4867),
    ("Mumbai", "Maharashtra", "Bandra Kurla Complex Hub", 19.0760, 72.8777),
    ("Delhi", "Delhi", "Anand Vihar Telemetry Station", 28.6139, 77.2090),
    ("Kochi", "Kerala", "Marine Drive Node", 9.9312, 76.2673),
    ("Pune", "Maharashtra", "Shivajinagar Sensor", 18.5204, 73.8567),
    ("Kolkata", "West Bengal", "Victoria Memorial Observatory", 22.5726, 88.3639),
    ("Thoothukudi", "Tamil Nadu", "Pearl City Port Hub", 8.7642, 78.1348),
]

MOCK_POLLUTANTS = [
    ("PM2.5", 38.5, "µg/m³"),
    ("PM10", 72.0, "µg/m³"),
    ("NO2", 24.1, "µg/m³"),
    ("SO2", 11.3, "µg/m³"),
    ("CO", 0.85, "mg/m³"),
    ("O3", 28.0, "µg/m³"),
]


class MockAQIProvider(BaseAQIProvider):
    """Provides simulated observations clearly labeled as simulated."""

    def __init__(self):
        self.is_closed = False

    def get_metadata(self) -> ProviderMetadata:
        """Return mock provider metadata."""
        return ProviderMetadata(
            provider_name="Urban Air Quality Mock Provider",
            dataset_title="Simulated Real-time Air Quality Data for Indian Cities",
            publisher="Urban Air Quality Assistant Test Infrastructure",
            license="MIT / Development Use Only",
            base_url="http://mock.internal",
            resource_id="mock-aqi-resource-001",
            is_configured=True,
            supports_filtering=True,
        )

    async def fetch_observations(
        self,
        city: str | None = None,
        state: str | None = None,
        limit: int = 100,
    ) -> list[NormalizedObservation]:
        """Generate typed simulated observations for supported cities."""
        # Floor to current hour to mirror official CPCB hourly cadence
        now_utc = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        results: list[NormalizedObservation] = []

        target_stations = MOCK_CITY_STATIONS
        if city:
            target_stations = [s for s in target_stations if s[0].lower() == city.lower()]
        if state:
            target_stations = [s for s in target_stations if s[1].lower() == state.lower()]

        for c_name, s_name, station_label, lat, lng in target_stations:
            for p_code, conc, unit in MOCK_POLLUTANTS:
                results.append(
                    NormalizedObservation(
                        country="India",
                        state=s_name,
                        city=c_name,
                        station_name=station_label,
                        external_station_id=f"MOCK_{c_name[:3].upper()}_01",
                        latitude=lat,
                        longitude=lng,
                        pollutant_code=p_code,
                        concentration=conc,
                        unit=unit,
                        measured_at=now_utc,
                        source="SIMULATED",
                        is_simulated=True,
                        raw_data={"simulated": True},
                    )
                )

        return results[:limit]

    async def close(self) -> None:
        """No-op cleanup."""
        self.is_closed = True

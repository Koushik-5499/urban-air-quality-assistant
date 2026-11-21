"""CPCB Provider implementation satisfying BaseAQIProvider."""


from app.core.config import get_settings
from app.integrations.base import BaseAQIProvider, NormalizedObservation, ProviderMetadata
from app.integrations.cpcb.client import CPCBClient
from app.integrations.cpcb.mapper import CPCBRecordMapper


class CPCBProvider(BaseAQIProvider):
    """Integrates with the official CPCB Real-time Air Quality Index API via data.gov.in."""

    def __init__(self, client: CPCBClient | None = None):
        settings = get_settings()
        self.settings = settings
        self.client = client or CPCBClient(
            base_url=settings.CPCB_API_BASE_URL,
            api_key=settings.CPCB_API_KEY,
            timeout=settings.AQI_FETCH_TIMEOUT,
            max_retries=settings.AQI_MAX_RETRIES,
        )
        self.mapper = CPCBRecordMapper

    def get_metadata(self) -> ProviderMetadata:
        """Return provider attribution, license, and capability metadata."""
        return ProviderMetadata(
            provider_name="Central Pollution Control Board (CPCB)",
            dataset_title="Real-time Air Quality Index from various locations",
            publisher="Ministry of Environment, Forest and Climate Change, Government of India",
            license="Government Open Data License - India (GODL)",
            base_url=self.settings.CPCB_API_BASE_URL,
            resource_id="3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69",
            is_configured=bool(self.settings.CPCB_API_KEY),
            supports_filtering=True,
        )

    async def fetch_observations(
        self,
        city: str | None = None,
        state: str | None = None,
        limit: int = 100,
    ) -> list[NormalizedObservation]:
        """Fetch raw records from CPCB API and map to NormalizedObservation objects."""
        raw_data = await self.client.get_raw_records(city=city, state=state, limit=limit)
        return self.mapper.map_records(raw_data)

    async def close(self) -> None:
        """Close underlying client connections."""
        await self.client.close()


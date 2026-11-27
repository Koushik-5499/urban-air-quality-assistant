"""Asynchronous HTTP client for CPCB data.gov.in API."""

import asyncio
from typing import Any

import httpx

from app.core.logging import get_logger
from app.integrations.cpcb.exceptions import (
    CPCBAuthError,
    CPCBParseError,
    CPCBProviderError,
    CPCBRateLimitError,
    CPCBTimeoutError,
)

logger = get_logger("app.integrations.cpcb.client")


class CPCBClient:
    """Asynchronous HTTP client querying the official data.gov.in CPCB dataset."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization of httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "User-Agent": "UrbanAirQualityAssistant/1.0.0",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def _handle_http_status(
        self, response: httpx.Response, attempt: int
    ) -> bool:
        """Handle HTTP status checks. Returns True if caller should retry, raises on hard errors."""
        if response.status_code in (401, 403):
            logger.warning("CPCB API authentication failed (HTTP %s)", response.status_code)
            raise CPCBAuthError(f"CPCB authentication failed with HTTP {response.status_code}")

        if response.status_code == 429:
            logger.warning("CPCB API rate limit exceeded (HTTP 429)")
            raise CPCBRateLimitError("CPCB API rate limit exceeded")

        if response.status_code >= 500:
            if attempt <= self.max_retries:
                backoff = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    "CPCB API server error (HTTP %s). Retrying in %.2fs (attempt %s/%s)...",
                    response.status_code, backoff, attempt, self.max_retries,
                )
                await asyncio.sleep(backoff)
                return True  # retry
            raise CPCBProviderError(
                f"CPCB API server error HTTP {response.status_code} after retries"
            )
        return False  # no retry needed

    @staticmethod
    def _parse_json_body(response: httpx.Response) -> dict[str, Any]:
        """Parse and validate a JSON dict from an HTTP response."""
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise CPCBParseError("CPCB response root is not a JSON object")
            return data
        except ValueError as err:
            raise CPCBParseError(f"Invalid JSON received from CPCB API: {err}")

    async def get_raw_records(
        self,
        city: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch raw records from the data.gov.in CPCB endpoint.

        Implements bounded exponential backoff for transient 5xx/timeout errors.
        Permanent client errors (400, 401, 403) are never retried.
        """
        if not self.api_key:
            raise CPCBAuthError("CPCB API key is not configured. Set CPCB_API_KEY in backend/.env")

        client = self._get_client()

        params: dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        if city:
            params["filters[city]"] = city
        if state:
            params["filters[state]"] = state

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await client.get(self.base_url, params=params)

                should_retry = await self._handle_http_status(response, attempt)
                if should_retry:
                    continue

                response.raise_for_status()
                return self._parse_json_body(response)

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as err:
                if attempt <= self.max_retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Network error querying CPCB API (%s). Retrying in %.2fs "
                        "(attempt %s/%s)...",
                        type(err).__name__, backoff, attempt, self.max_retries,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise CPCBTimeoutError(
                    f"CPCB API request timed out or failed to connect: {err}"
                )

            except httpx.HTTPStatusError as err:
                raise CPCBProviderError(f"HTTP error querying CPCB API: {err}")

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

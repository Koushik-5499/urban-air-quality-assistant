"""Data normalization service for canonical city matching and pollutant categorization."""


# Supported Indian cities canonical mapping
# Maps lowercase aliases and historical names to (Canonical Name, Canonical State)
CANONICAL_CITIES: dict[str, tuple[str, str]] = {
    "coimbatore": ("Coimbatore", "Tamil Nadu"),
    "chennai": ("Chennai", "Tamil Nadu"),
    "madras": ("Chennai", "Tamil Nadu"),
    "bengaluru": ("Bengaluru", "Karnataka"),
    "bangalore": ("Bengaluru", "Karnataka"),
    "hyderabad": ("Hyderabad", "Telangana"),
    "mumbai": ("Mumbai", "Maharashtra"),
    "bombay": ("Mumbai", "Maharashtra"),
    "delhi": ("Delhi", "Delhi"),
    "new delhi": ("Delhi", "Delhi"),
    "kochi": ("Kochi", "Kerala"),
    "cochin": ("Kochi", "Kerala"),
    "pune": ("Pune", "Maharashtra"),
    "poona": ("Pune", "Maharashtra"),
    "kolkata": ("Kolkata", "West Bengal"),
    "calcutta": ("Kolkata", "West Bengal"),
    "thoothukudi": ("Thoothukudi", "Tamil Nadu"),
    "tuticorin": ("Thoothukudi", "Tamil Nadu"),
}

CORE_POLLUTANTS: set[str] = {"PM2.5", "PM10", "CO", "NO2", "SO2", "O3"}


class DataNormalizationService:
    """Provides canonical matching and standardization rules for environmental data."""

    @classmethod
    def match_canonical_city(
        cls,
        city_name: str,
        state_name: str | None = None,
    ) -> tuple[str, str] | None:
        """Match an arbitrary city string to one of the ten officially supported Indian cities.

        Handles case insensitivity, leading/trailing whitespace, and historical aliases.
        If state_name is provided, ensures state alignment when multiple matches exist.
        """
        if not city_name:
            return None

        clean_city = city_name.strip().lower()

        # Direct alias match
        if clean_city in CANONICAL_CITIES:
            canonical_name, canonical_state = CANONICAL_CITIES[clean_city]
            if state_name:
                clean_state = state_name.strip().lower()
                # Verify state roughly matches
                if clean_state not in canonical_state.lower() and canonical_state.lower() not in clean_state:
                    return None
            return canonical_name, canonical_state

        # Partial token match (e.g. "Delhi (ITO)" -> "Delhi")
        for alias, (c_name, c_state) in CANONICAL_CITIES.items():
            if alias in clean_city:
                if state_name:
                    clean_state = state_name.strip().lower()
                    if clean_state not in c_state.lower() and c_state.lower() not in clean_state:
                        continue
                return c_name, c_state

        return None

    @classmethod
    def is_core_pollutant(cls, pollutant_code: str) -> bool:
        """Verify whether a pollutant code belongs to the six core criteria pollutants."""
        return pollutant_code.upper() in CORE_POLLUTANTS


"""Dominant pollutant identification and deterministic tie-breaking rules."""


# CPCB tie-breaking priority ordered by public health severity:
# Fine particulates (PM2.5) first, followed by PM10, toxic combustion gases, oxidants, and heavy metals.
DOMINANT_TIE_BREAKER_PRIORITY: list[str] = [
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "CO",
    "SO2",
    "NH3",
    "Pb",
]


class DominantPollutantResolver:
    """Determines dominant pollutant from sub-indices using health-priority tie-breaking."""

    @classmethod
    def resolve_dominant_pollutant(cls, sub_indices: dict[str, int]) -> str | None:
        """Find the pollutant responsible for driving the highest sub-index.

        If multiple pollutants share the exact same maximum sub-index, the tie is broken
        deterministically using the public health priority hierarchy.
        """
        if not sub_indices:
            return None

        max_val = max(sub_indices.values())
        tied_candidates = [code for code, val in sub_indices.items() if val == max_val]

        if len(tied_candidates) == 1:
            return tied_candidates[0]

        # Break tie using priority list
        for priority_code in DOMINANT_TIE_BREAKER_PRIORITY:
            if priority_code in tied_candidates:
                return priority_code

        # Fallback to alphabetical if custom pollutant code
        return sorted(tied_candidates)[0]


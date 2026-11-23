"""Official Central Pollution Control Board (CPCB) NAQI breakpoint tables and metadata."""

from typing import NamedTuple


class BreakpointRange(NamedTuple):
    """Breakpoint definition for an AQI category interval."""

    c_low: float
    c_high: float
    i_low: int
    i_high: int
    category: str


class PollutantMetadata(NamedTuple):
    """Metadata describing required unit and averaging period for NAQI computation."""

    code: str
    name: str
    unit: str
    averaging_period: str
    description: str


POLLUTANT_INFO: dict[str, PollutantMetadata] = {
    "PM2.5": PollutantMetadata(
        code="PM2.5",
        name="Particulate Matter < 2.5 µm",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Fine inhalable particles",
    ),
    "PM10": PollutantMetadata(
        code="PM10",
        name="Particulate Matter < 10 µm",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Coarse inhalable particles",
    ),
    "NO2": PollutantMetadata(
        code="NO2",
        name="Nitrogen Dioxide",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Combustion gas emissions",
    ),
    "SO2": PollutantMetadata(
        code="SO2",
        name="Sulphur Dioxide",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Industrial emissions",
    ),
    "CO": PollutantMetadata(
        code="CO",
        name="Carbon Monoxide",
        unit="mg/m³",
        averaging_period="8-hour",
        description="Incomplete combustion gas (note unit is mg/m³)",
    ),
    "O3": PollutantMetadata(
        code="O3",
        name="Ozone",
        unit="µg/m³",
        averaging_period="8-hour",
        description="Ground-level photochemical oxidant",
    ),
    "NH3": PollutantMetadata(
        code="NH3",
        name="Ammonia",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Agricultural and waste emissions",
    ),
    "Pb": PollutantMetadata(
        code="Pb",
        name="Lead",
        unit="µg/m³",
        averaging_period="24-hour",
        description="Toxic heavy metal particulate",
    ),
}

# CPCB NAQI Breakpoint intervals: (C_low, C_high, I_low, I_high, Category)
# Source: Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate
# Change, Govt. of India
CPCB_BREAKPOINTS: dict[str, list[BreakpointRange]] = {
    "PM2.5": [
        BreakpointRange(0.0, 30.0, 0, 50, "Good"),
        BreakpointRange(30.0, 60.0, 51, 100, "Satisfactory"),
        BreakpointRange(60.0, 90.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(90.0, 120.0, 201, 300, "Poor"),
        BreakpointRange(120.0, 250.0, 301, 400, "Very Poor"),
        BreakpointRange(250.0, 380.0, 401, 500, "Severe"),
    ],
    "PM10": [
        BreakpointRange(0.0, 50.0, 0, 50, "Good"),
        BreakpointRange(50.0, 100.0, 51, 100, "Satisfactory"),
        BreakpointRange(100.0, 250.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(250.0, 350.0, 201, 300, "Poor"),
        BreakpointRange(350.0, 430.0, 301, 400, "Very Poor"),
        BreakpointRange(430.0, 510.0, 401, 500, "Severe"),
    ],
    "NO2": [
        BreakpointRange(0.0, 40.0, 0, 50, "Good"),
        BreakpointRange(40.0, 80.0, 51, 100, "Satisfactory"),
        BreakpointRange(80.0, 180.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(180.0, 280.0, 201, 300, "Poor"),
        BreakpointRange(280.0, 400.0, 301, 400, "Very Poor"),
        BreakpointRange(400.0, 520.0, 401, 500, "Severe"),
    ],
    "SO2": [
        BreakpointRange(0.0, 40.0, 0, 50, "Good"),
        BreakpointRange(40.0, 80.0, 51, 100, "Satisfactory"),
        BreakpointRange(80.0, 380.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(380.0, 800.0, 201, 300, "Poor"),
        BreakpointRange(800.0, 1600.0, 301, 400, "Very Poor"),
        BreakpointRange(1600.0, 2400.0, 401, 500, "Severe"),
    ],
    "CO": [
        BreakpointRange(0.0, 1.0, 0, 50, "Good"),
        BreakpointRange(1.0, 2.0, 51, 100, "Satisfactory"),
        BreakpointRange(2.0, 10.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(10.0, 17.0, 201, 300, "Poor"),
        BreakpointRange(17.0, 34.0, 301, 400, "Very Poor"),
        BreakpointRange(34.0, 51.0, 401, 500, "Severe"),
    ],
    "O3": [
        BreakpointRange(0.0, 50.0, 0, 50, "Good"),
        BreakpointRange(50.0, 100.0, 51, 100, "Satisfactory"),
        BreakpointRange(100.0, 168.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(168.0, 208.0, 201, 300, "Poor"),
        BreakpointRange(208.0, 748.0, 301, 400, "Very Poor"),
        BreakpointRange(748.0, 1000.0, 401, 500, "Severe"),
    ],
    "NH3": [
        BreakpointRange(0.0, 200.0, 0, 50, "Good"),
        BreakpointRange(200.0, 400.0, 51, 100, "Satisfactory"),
        BreakpointRange(400.0, 800.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(800.0, 1200.0, 201, 300, "Poor"),
        BreakpointRange(1200.0, 1800.0, 301, 400, "Very Poor"),
        BreakpointRange(1800.0, 2400.0, 401, 500, "Severe"),
    ],
    "Pb": [
        BreakpointRange(0.0, 0.5, 0, 50, "Good"),
        BreakpointRange(0.5, 1.0, 51, 100, "Satisfactory"),
        BreakpointRange(1.0, 2.0, 101, 200, "Moderately Polluted"),
        BreakpointRange(2.0, 3.0, 201, 300, "Poor"),
        BreakpointRange(3.0, 3.5, 301, 400, "Very Poor"),
        BreakpointRange(3.5, 5.0, 401, 500, "Severe"),
    ],
}

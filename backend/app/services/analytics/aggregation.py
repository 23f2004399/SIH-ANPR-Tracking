"""Traffic congestion metrics.

No camera calibration exists yet (that's not in any phase 1-5 task), so speed
is never computed here — the SOP is explicit that average_speed should only
be returned if it can be measured reliably. The metric we can actually support
from tracking data alone is vehicles per minute, used both as the density
proxy and as the input to congestion classification.
"""

# Vehicles/minute thresholds. Placeholder values — the SOP itself lists this
# as an open decision ("set thresholds from test data"), so these should be
# recalibrated once real footage is flowing through Phase 2.
CONGESTION_THRESHOLDS = {"clear_below": 2.0, "slow_below": 6.0}

CLEAR, SLOW, SEVERE = "Clear", "Slow", "Severe"


def classify_congestion(vehicles_per_minute: float) -> str:
    if vehicles_per_minute < CONGESTION_THRESHOLDS["clear_below"]:
        return CLEAR
    if vehicles_per_minute < CONGESTION_THRESHOLDS["slow_below"]:
        return SLOW
    return SEVERE


def compute_metrics(vehicle_count: int, window_minutes: float) -> dict:
    """vehicle_count must already be a count of DISTINCT tracks, not raw
    observation rows — a vehicle sitting in frame for 3 seconds is one
    vehicle, not three."""
    density = vehicle_count / window_minutes if window_minutes > 0 else 0.0
    return {
        "vehicle_count": vehicle_count,
        "density_metric": round(density, 3),
        "average_speed": None,
        "congestion_level": classify_congestion(density),
    }

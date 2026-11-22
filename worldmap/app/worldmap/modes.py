"""Transport mode of a movement – from Google activity names, typed words or speed."""
from __future__ import annotations

FLIGHT_KMH = 220.0
MIN_FLIGHT_KM = 150.0

# Google activity names and our transport words -> mode
ACTIVITY = (
    ("fly", ("FLYING", "flying", "Flug", "flight")),
    ("ferry", ("FERRY", "ferry", "Schiff", "boat", "SAILING")),
    ("rail", ("TRAIN", "SUBWAY", "TRAM", "BUS", "in train", "in subway", "in tram", "in bus", "Zug", "rail",
              "METRO", "in metro")),
    ("foot", ("WALKING", "RUNNING", "ON_FOOT", "CYCLING", "BICYCLE", "walking", "running", "cycling", "zu Fuss", "Velo")),
    ("road", ("VEHICLE", "DRIVING", "MOTORCYCLING", "passenger vehicle", "Auto", "Wohnmobil", "car", "driving")),
)


def mode_of_text(text: str | None) -> str | None:
    if not text:
        return None
    for mode, words in ACTIVITY:
        if any(w in text for w in words):
            return mode
    return None


def modes_of_transport(text: str | None) -> list[str]:
    out = []
    for part in (text or "").split("·"):
        m = mode_of_text(part.strip())
        if m and m not in out:
            out.append(m)
    return out


def mode_of_pair(a: dict, b: dict, dist_km: float) -> str:
    dt_h = max(1e-6, (b["ts"] - a["ts"]) / 3600)
    speed = dist_km / dt_h
    hinted = mode_of_text(b.get("hint")) or mode_of_text(a.get("hint"))
    if speed >= FLIGHT_KMH or (dist_km > 800 and dt_h < 24):
        if dist_km < MIN_FLIGHT_KM:
            return "jump"  # a few fast kilometres are GPS jumps, not flights
        if hinted in ("rail", "road", "ferry") and dist_km < 600:
            return hinted  # a train or car trip with a gap in the recording
        return "fly"
    if hinted and hinted != "fly":
        return hinted
    if speed < 7:
        return "foot"
    return "road"

"""Transport mode of a movement – from Google activity names, typed words or speed."""
from __future__ import annotations

FLIGHT_KMH = 220.0
MIN_FLIGHT_KM = 150.0
# nothing on the ground is faster: a "train" at 400 km/h was a plane (Google labels flights as trains at times)
MAX_KMH = {"rail": 320.0, "road": 200.0, "ferry": 80.0}

# Google activity names and our transport words -> mode
ACTIVITY = (
    ("fly", ("FLYING", "flying", "Flug", "flight", "Wasserflugzeug", "seaplane")),
    ("ferry", ("FERRY", "ferry", "Schiff", "Fähre", "boat", "SAILING")),
    ("rail", ("TRAIN", "SUBWAY", "TRAM", "BUS", "in train", "in subway", "in tram", "in bus", "Zug", "rail", "U-Bahn", "Tram",
              "METRO", "in metro")),
    ("foot", ("WALKING", "RUNNING", "ON_FOOT", "CYCLING", "BICYCLE", "walking", "running", "cycling", "zu Fuss", "Velo")),
    ("road", ("VEHICLE", "DRIVING", "MOTORCYCLING", "passenger vehicle", "Auto", "Wohnmobil", "car", "driving", "Bus",
              "Car", "Motorrad")),
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
        if hinted == "fly" and dist_km >= 20 and b["ts"] - a["ts"] >= 120 and speed <= 1200:
            return "fly"  # a piece of a recorded flight (points every few minutes while flying)
        if dist_km < MIN_FLIGHT_KM or b["ts"] - a["ts"] < 300:
            return "jump"  # a few fast kilometres or hundreds of km in no time are GPS jumps, not flights
        if hinted in ("rail", "road", "ferry") and dist_km < 600 and speed <= MAX_KMH[hinted]:
            return hinted  # a train or car trip with a gap in the recording (faster than that: Google got it wrong)
        return "fly"
    if hinted and hinted != "fly":
        return hinted
    if speed < 7:
        return "foot"
    return "road"


DETOUR = {"road": 1.25, "rail": 1.2, "ferry": 1.15, "foot": 1.3, "fly": 1.0}
LOCAL_KM_PER_DAY = {"road": 35, "rail": 10, "ferry": 5, "foot": 6, "fly": 0}


def estimate_km(dist_km: float, modes: list[str], nights: int) -> dict:
    """Kilometres of a trip without GPS (entered by hand or from a trip list), worked out offline.

    * the main way there and back: straight-line distance x a detour factor (roads and rails are not straight);
    * flights: the flight there and back plus the way to and from the airport by car or train;
    * on the spot: a few kilometres per day (car trips drive more than train trips).
    """
    modes = [m for m in modes if m in DETOUR] or ["road"]
    dist_km = max(0.0, float(dist_km or 0))
    days = max(1, int(nights or 0) + 1)
    out: dict = {}
    if "fly" in modes and dist_km >= 150:
        out["fly"] = 2 * dist_km
        ground = next((m for m in modes if m != "fly"), "road")
        out[ground] = out.get(ground, 0) + 2 * min(60.0, max(20.0, dist_km * 0.03)) + LOCAL_KM_PER_DAY[ground] * days * 0.5
    else:
        main = next((m for m in modes if m != "fly"), "road")
        out[main] = 2 * dist_km * DETOUR[main] + LOCAL_KM_PER_DAY[main] * days
        if "ferry" in modes and main != "ferry":
            out["ferry"] = min(2 * dist_km * 0.25, 400.0)  # a crossing, there and back
    return {m: round(v) for m, v in out.items() if v >= 1}

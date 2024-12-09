from dateutil.parser import isoparse

def parse_time(time_str, tz, default="N/A"):
    """Convert a time string to a timezone-aware datetime, or return a default."""
    return isoparse(time_str).astimezone(tz).isoformat() if time_str else default

def extract_correspondence(section, tz):
    """Extract transit section details."""
    return {
        "departure_time": parse_time(section["departure"]["time"], tz),
        "arrival_time": parse_time(section["arrival"]["time"], tz),
        "from_station": section["departure"]["place"].get("name", "Unknown"),
        "to_station": section["arrival"]["place"].get("name", "Unknown"),
        "transport_mode": section["transport"]["mode"],
        "transport_name": section["transport"]["name"],
        "agency": section["agency"].get("name", "Unknown"),
    }


def sanitize_value(value, default=None):
    return value if value is not None else default

def safe_string(value):
    """Retourne une chaîne ou une chaîne vide si la valeur est None ou incompatible."""
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        return "; ".join(map(str, value))  # Concatène les valeurs de la liste avec un séparateur
    return str(value)
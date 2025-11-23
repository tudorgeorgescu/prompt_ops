def safe_float(x, default=0.0):
    """Convert x to float safely, return default if conversion fails."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def safe_params(sd_params):
    """
    Process a list of parameter dictionaries, ensuring 'value' is a float.
    Each dict should have 'name' and 'value' keys.
    """
    out = []
    if isinstance(sd_params, list):
        for p in sd_params:
            if isinstance(p, dict):
                name = str(p.get("name", "")).strip()
                value = safe_float(p.get("value", 0.0), 0.0)
                out.append({"name": name, "value": value})

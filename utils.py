def safe_float(x, default=0.0):
    """Convert x to float safely, return default if conversion fails."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def normalize_params(sd_params):
    out = []
    if isinstance(sd_params, list):
        source = sd_params
    elif isinstance(sd_params, dict):
        # Convert dict {name: value} to list of dicts
        source = [{"name": k, "value": v} for k, v in sd_params.items()]
    else:
        source = []

    for p in source:
        if isinstance(p, dict):
            name = str(p.get("name", "")).strip()
            value = safe_float(p.get("value", 0.0), 0.0)
            if name:
                out.append({"name": name, "value": value})
    return out

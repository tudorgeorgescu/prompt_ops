def safe_float(x, default=0.0):def safe):
    out = []
    if isinstance(sd_params, list):
        for p in sd_params:
            if isinstance(p, dict):
                name = str(p.get("name", "")).strip()
                value = safe_float(p.get("value", 0.0), 0.0)
                out.append({"name": name, "value": value})
    return out
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


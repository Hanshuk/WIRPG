def validate_coordinate(value, min_val, max_val) -> bool:
    try:
        f = float(value)
        return min_val <= f <= max_val
    except (ValueError, TypeError):
        return False

def validate_longitude(val) -> bool:
    return validate_coordinate(val, -180.0, 180.0)

def validate_latitude(val) -> bool:
    return validate_coordinate(val, -90.0, 90.0)

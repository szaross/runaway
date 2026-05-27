_PRESETS = {
    "full": (800, 453),
    "small": (320, 181),
}
_MAX_VIZ_CELLS = 70_000


def adaptive_visualization_grid() -> tuple[int, int]:
    """Pick the densest browser-friendly grid preserving D17 aspect ratio."""
    full_w, full_h = _PRESETS["full"]
    if full_w * full_h <= _MAX_VIZ_CELLS:
        return full_w, full_h

    scale = (_MAX_VIZ_CELLS / (full_w * full_h)) ** 0.5
    width = max(_PRESETS["small"][0], int(full_w * scale))
    height = round(width * full_h / full_w)
    return width, height

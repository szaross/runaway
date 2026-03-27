try:
    from runaway.utils.png_to_wall_runs import (
        matrix_to_wall_runs_payload,
        png_to_matrix,
        rgb_to_value,
        save_wall_runs_json,
        wall_runs_payload_to_matrix,
    )
except ImportError:
    # Pillow / PNG support is optional. Importing runaway.utils should not fail
    # if the optional png extra is not installed; instead, using these helpers
    # will raise a clear ImportError at call time.
    def _png_optional_dependency_missing(*_args, **_kwargs):
        raise ImportError(
            "PNG utilities in runaway.utils require the optional 'png' extra "
            "(Pillow). Please install it to use these functions."
        )

    matrix_to_wall_runs_payload = _png_optional_dependency_missing
    png_to_matrix = _png_optional_dependency_missing
    rgb_to_value = _png_optional_dependency_missing
    save_wall_runs_json = _png_optional_dependency_missing
    wall_runs_payload_to_matrix = _png_optional_dependency_missing
__all__ = [
    "matrix_to_wall_runs_payload",
    "png_to_matrix",
    "rgb_to_value",
    "save_wall_runs_json",
    "wall_runs_payload_to_matrix",
]

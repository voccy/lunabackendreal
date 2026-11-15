import numpy as np
import main


def test_local_basis_is_orthonormal():
    east, north, up = main.local_basis(-89.9, 45.0)
    basis = np.vstack([east, north, up])
    assert np.allclose(basis @ basis.T, np.eye(3), atol=1e-10)


def test_interval_duration_is_in_hours():
    samples = [
        {"datetime_utc": "2026-01-01T00:00:00Z", "visible": True},
        {"datetime_utc": "2026-01-01T01:00:00Z", "visible": True},
        {"datetime_utc": "2026-01-01T02:00:00Z", "visible": False},
    ]
    result = main.intervals(samples, "visible")
    assert result[0]["duration_hours"] == 1.0

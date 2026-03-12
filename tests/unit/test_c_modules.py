import os
import glob
import ctypes
import pytest


def test_fuzzy_shared_library():
    """Verify that the compiled C shared library behaves as expected via the Cython wrapper."""
    # the compiled extension will have a platform-specific suffix
    pattern = os.path.abspath("c_modules/fuzzy_cython.*.so")
    matches = glob.glob(pattern)
    if not matches:
        pytest.skip(
            "Cython extension not built; run `python c_modules/setup.py build_ext --inplace` first"
        )

    lib = ctypes.CDLL(matches[0])
    lib.compute_lead_score.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.compute_lead_score.restype = ctypes.c_double
    score = lib.compute_lead_score(50.0, 50.0)
    assert 0 <= score <= 100


def test_cython_wrapper():
    """Import and call the Cython wrapper if built."""
    try:
        from c_modules.fuzzy_cython import lead_score
    except ImportError:
        pytest.skip(
            "Cython extension not built; see c_modules/README.md for instructions"
        )

    result = lead_score(50.0, 50.0)
    assert pytest.approx(50.0, rel=1e-1) == result

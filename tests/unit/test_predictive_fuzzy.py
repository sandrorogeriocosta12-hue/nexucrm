import os
import pytest

from vexus_hub.app.predictive_analytics import PredictiveAnalytics


def test_fuzzy_lead_score():
    """Ensure the PredictiveAnalytics helper calls the fuzzy engine correctly."""
    # compile library if missing
    lib_dir = os.path.join(os.getcwd(), "c_modules", "fuzzy")
    if not os.path.exists(os.path.join(lib_dir, "libfuzzy.so")):
        # try to build
        res = os.system(f'cd "{lib_dir}" && make')
        if res != 0:
            pytest.skip("Unable to build fuzzy library")

    pa = PredictiveAnalytics(clinic_id="test")
    score = pa._fuzzy_lead_score(65.0, 80.0)
    assert 0 <= score <= 100

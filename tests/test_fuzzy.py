import pytest

pytest.skip("legacy fuzzy tests disabled", allow_module_level=True)
import ctypes
import os


@pytest.fixture(scope="session")
def fuzzy_lib():
    lib_path = os.path.join(os.path.dirname(__file__), "../c_modules/fuzzy/libfuzzy.so")
    if not os.path.exists(lib_path):
        pytest.skip("Fuzzy library not built; run `make` in c_modules/fuzzy`")
    lib = ctypes.CDLL(lib_path)
    lib.fuzzy_system_load.argtypes = [ctypes.c_char_p]
    lib.fuzzy_system_load.restype = ctypes.c_void_p
    lib.fuzzy_system_evaluate.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.fuzzy_system_evaluate.restype = ctypes.c_double
    lib.fuzzy_system_free.argtypes = [ctypes.c_void_p]
    return lib


def test_fuzzy_score(fuzzy_lib):
    sys_ptr = fuzzy_lib.fuzzy_system_load(b"../c_modules/fuzzy/rules.json")
    assert sys_ptr is not None
    # first evaluate using only engagement/likelihood (JSON parser still supports two inputs)
    inputs = (ctypes.c_double * 2)(65.0, 80.0)
    score = fuzzy_lib.fuzzy_system_evaluate(sys_ptr, b"score", inputs)
    assert 0 <= score <= 100

    # now supply third "availability" dimension; low availability should reduce score
    inputs3 = (ctypes.c_double * 3)(65.0, 80.0, 0.0)
    score3 = fuzzy_lib.fuzzy_system_evaluate(sys_ptr, b"score", inputs3)
    assert score3 <= score

    # basic sanity on parsed objects: variables and rules present
    # this requires exposing structures; for test we just ensure evaluate works
    fuzzy_lib.fuzzy_system_free(sys_ptr)

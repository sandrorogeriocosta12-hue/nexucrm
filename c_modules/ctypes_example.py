import ctypes
import os

# Carrega a biblioteca
lib_path = os.path.join(os.path.dirname(__file__), "fuzzy", "libfuzzy.so")
lib = ctypes.CDLL(lib_path)

# Define protótipos
glib = lib
lib.fuzzy_system_load.argtypes = [ctypes.c_char_p]
lib.fuzzy_system_load.restype = ctypes.c_void_p

lib.fuzzy_system_evaluate.argtypes = [
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_double),
]
lib.fuzzy_system_evaluate.restype = ctypes.c_double

lib.fuzzy_system_free.argtypes = [ctypes.c_void_p]


class FuzzySystem:
    def __init__(self, config_file):
        self.ptr = lib.fuzzy_system_load(config_file.encode("utf-8"))
        if not self.ptr:
            raise RuntimeError("Failed to load fuzzy system")

    def evaluate(self, out_var, inputs):
        arr = (ctypes.c_double * len(inputs))(*inputs)
        return lib.fuzzy_system_evaluate(self.ptr, out_var.encode("utf-8"), arr)

    def __del__(self):
        if hasattr(self, "ptr") and self.ptr:
            lib.fuzzy_system_free(self.ptr)


# exemplo de uso
if __name__ == "__main__":
    fs = FuzzySystem(os.path.join(os.path.dirname(__file__), "fuzzy", "rules.json"))
    score = fs.evaluate("score", [65.0, 80.0])
    print(f"Lead Score: {score:.2f}")

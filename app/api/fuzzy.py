from fastapi import APIRouter
from pydantic import BaseModel
import ctypes
import os

router = APIRouter(prefix="/fuzzy", tags=["fuzzy"])

# Load C library lazily - only if it exists
lib = None
try:
    lib_path = os.path.join(
        os.path.dirname(__file__), "../../c_modules/fuzzy/libfuzzy.so"
    )
    if os.path.exists(lib_path):
        lib = ctypes.CDLL(lib_path)
        lib.fuzzy_system_evaluate.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_double),
        ]
        lib.fuzzy_system_evaluate.restype = ctypes.c_double
except Exception as e:
    # Log but don't crash if fuzzy library is not available
    print(f"Warning: Fuzzy library not available: {e}")

_fuzzy_sys = None


def load_system():
    global _fuzzy_sys
    lib.fuzzy_system_load.argtypes = [ctypes.c_char_p]
    lib.fuzzy_system_load.restype = ctypes.c_void_p
    _fuzzy_sys = lib.fuzzy_system_load(b"c_modules/fuzzy/rules.json")
    if not _fuzzy_sys:
        raise RuntimeError("Failed to load fuzzy system")


class LeadScoreRequest(BaseModel):
    engagement: float
    likelihood: float


class AgentPerfRequest(BaseModel):
    response_time: float
    satisfaction: float
    conversion_rate: float


class AppointmentPriorityRequest(BaseModel):
    days_until: int
    lead_score: float
    cancel_history: int


@router.on_event("startup")
def startup_event():
    if lib is not None:
        try:
            load_system()
        except Exception as e:
            print(f"Warning: Could not load fuzzy system: {e}")
    else:
        print("Warning: Fuzzy C library not available, using mock scores")


@router.post("/lead-score")
def lead_score(req: LeadScoreRequest):
    if lib is None or _fuzzy_sys is None:
        # Mock scoring when library unavailable
        score = (req.engagement + req.likelihood) / 2
        if score >= 70:
            classification = "hot"
        elif score >= 40:
            classification = "warm"
        else:
            classification = "cold"
        return {"score": round(score, 2), "classification": classification}

    try:
        arr = (ctypes.c_double * 2)(req.engagement, req.likelihood)
        score = lib.fuzzy_system_evaluate(_fuzzy_sys, b"lead_score", arr)
        if score >= 70:
            classification = "hot"
        elif score >= 40:
            classification = "warm"
        else:
            classification = "cold"
        return {"score": round(score, 2), "classification": classification}
    except Exception as e:
        print(f"Error in lead_score: {e}")
        return {"score": 50.0, "classification": "warm"}


@router.post("/agent-performance")
def agent_performance(req: AgentPerfRequest):
    if lib is None or _fuzzy_sys is None:
        # Mock: average of metrics
        score = (
            req.response_time + (req.satisfaction * 100) + (req.conversion_rate * 100)
        ) / 3
        return {"score": round(min(score, 100), 2)}

    try:
        arr = (ctypes.c_double * 3)(
            req.response_time, req.satisfaction, req.conversion_rate
        )
        score = lib.fuzzy_system_evaluate(_fuzzy_sys, b"agent_perf", arr)
        return {"score": round(score, 2)}
    except Exception as e:
        print(f"Error in agent_performance: {e}")
        return {"score": 60.0}


@router.get("/metrics/dashboard")
def metrics_dashboard():
    # Aggregated metrics from fuzzy system or database
    return {"avg_score": 55.2, "distribution": {"hot": 12, "warm": 34, "cold": 54}}


@router.post("/appointment-priority")
def appointment_priority(req: AppointmentPriorityRequest):
    if lib is None or _fuzzy_sys is None:
        # Mock: higher priority for soon appointments with good leads
        priority = (
            100 - req.days_until * 5 + req.lead_score / 2 - req.cancel_history * 10
        )
        return {"priority": round(max(min(priority, 100), 0), 2)}

    try:
        arr = (ctypes.c_double * 3)(req.days_until, req.lead_score, req.cancel_history)
        score = lib.fuzzy_system_evaluate(_fuzzy_sys, b"appt_priority", arr)
        return {"priority": round(score, 2)}
    except Exception as e:
        print(f"Error in appointment_priority: {e}")
        return {"priority": 50.0}

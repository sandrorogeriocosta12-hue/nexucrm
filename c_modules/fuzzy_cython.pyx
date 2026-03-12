# fuzzy_cython.pyx

cdef extern from "fuzzy_logic.h":
    double compute_lead_score(double engagement, double likelihood)


def lead_score(double engagement, double likelihood):
    """Chamador Python para compute_lead_score em C"""
    return compute_lead_score(engagement, likelihood)

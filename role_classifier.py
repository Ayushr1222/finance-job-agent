"""
role_classifier.py
"""


def classify_role(job_text):

    text = job_text.lower()

    fpa_words = [
        "fp&a",
        "fpa",
        "budgeting",
        "forecasting",
        "variance analysis",
        "financial planning",
    ]

    modelling_words = [
        "financial modelling",
        "financial modeling",
        "valuation",
        "dcf",
        "3-statement",
        "scenario analysis",
    ]

    analytics_words = [
        "financial analyst",
        "mis",
        "reporting",
        "power bi",
        "excel",
        "kpi",
    ]

    if any(k in text for k in fpa_words):
        return "fpa"

    if any(k in text for k in modelling_words):
        return "modelling"

    if any(k in text for k in analytics_words):
        return "analytics"

    return "finance"

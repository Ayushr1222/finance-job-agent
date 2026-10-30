"""
profile_loader.py
"""

from config import DEFAULT_ANSWERS


def load_profile():
    return {
        "full_name":
            DEFAULT_ANSWERS["full_name"],

        "email":
            DEFAULT_ANSWERS["email"],

        "phone":
            DEFAULT_ANSWERS["phone"],

        "education":
            """
PGDM — Finance (MBA Equivalent) | IMS Ghaziabad (2024 - 2026, CGPA: 8.3/10)
BBA | Amity University, Patna (2019 - 2022, 75.4%)
            """,

        "experience":
            """
Finance Intern — KPMG India, Noida (May 2025 - Jul 2025)
• Built and maintained budget vs. actual trackers in Excel, surfacing cost drivers and operational KPIs
• Executed variance analysis and ratio benchmarking across client portfolios
• Developed Python (Pandas) regression and correlation models for financial review cycles
• Supported financial due diligence on client income statements, balance sheets, and cash flow statements

Operations Executive — IndusInd Bank, Patna (Dec 2023 - Feb 2024)
• Managed banking operations, compliance reporting, and audit documentation across 200+ monthly transactions

Management Trainee — Ceasefire Industries Pvt. Ltd., Patna (Jul 2022 - Dec 2022)
• Prepared and maintained MIS reports tracking revenues, costs, and divisional KPIs
• Identified 10-12% variance between projected and actual sales volumes via monthly data analysis
            """,
    }
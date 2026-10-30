"""
job_filters.py — Role/location/keyword filtering criteria.

Pulled out of scraper.py so the cloud pipeline (pipeline.py -> cloud_run.py)
can import filter criteria without dragging in scraper.py's Playwright
dependency, which the jobspy-based cloud scrape no longer needs.

Retargeted to Ayush Sinha's resume (resume_base.docx): MBA Finance graduate
(IMS Ghaziabad, 2026), targeting FP&A, Financial Analyst, Financial Modelling,
and Corporate Finance roles.
"""

# Search terms actually sent to jobspy/Naukri/Unstop as `search_term` —
# what gets queried. Each term is multiplied by every location (and every
# site), so keep this list short. Seniority/level words in the term ensure
# entry-level / early-career matches rather than senior director roles.
TARGET_ROLES = [
    "Financial Analyst Fresher",
    "FP&A Analyst",
    "Junior Financial Analyst",
    "Associate Financial Analyst",
    "Finance Trainee",
    "Corporate Finance Analyst",
]

# Title-acceptance rule used by pipeline.role_matches(): a posting is kept
# if its title contains ALL words in at least one group below, in ANY order
# and not necessarily adjacent. Word-based rather than literal-phrase
# matching on purpose — real postings phrase the same role differently
# ("Financial Analyst - FP&A" vs "FP&A Financial Analyst"). Still
# gated by the MATCH_KEYWORDS/MIN_MATCH_COUNT floor below, so this doesn't
# admit irrelevant roles just from title words alone.
ROLE_WORD_GROUPS = [
    # Financial Analyst & Associates
    {"financial", "analyst"},
    {"finance", "analyst"},
    {"fp&a", "analyst"},
    {"fpa", "analyst"},
    {"fp&a", "associate"},
    {"fpa", "associate"},
    {"financial", "planning"},
    {"financial", "modeling"},
    {"financial", "modelling"},
    {"corporate", "finance"},
    {"valuation", "analyst"},
    {"budgeting", "analyst"},
    {"variance", "analyst"},
    {"finance", "associate"},
    {"financial", "associate"},
    {"finance", "trainee"},
    {"management", "trainee"},
    {"graduate", "trainee"},
    {"junior", "analyst"},
    {"finance", "executive"},
    {"accounts", "analyst"},
    {"commercial", "finance"},
    {"business", "finance"},
    {"investment", "analyst"},
    {"equity", "research"},
    {"portfolio", "analyst"},
    {"risk", "analyst"},
    {"credit", "analyst"},
    {"mis", "analyst"},
    {"mis", "executive"},
    {"reporting", "analyst"},
]

# Titles containing one of these phrases are rejected outright even if a
# ROLE_WORD_GROUPS group matches.
EXCLUDED_ROLE_PHRASES = [
    # Software & Tech
    "software engineer", "developer", "backend", "frontend", "full stack",
    "devops", "cloud engineer", "qa", "test engineer", "sdet", "automation tester",
    "data scientist", "machine learning", "ml engineer", "ai engineer",
    "system administrator", "network engineer", "hardware engineer",
    # Call center / BPO / Low-skill sales
    "telecaller", "bpo", "customer care", "customer support", "telesales",
    "field sales", "door to door", "real estate agent", "insurance agent",
    # Non-finance
    "graphic designer", "content writer", "teacher", "faculty", "trainer",
    "recruiter", "hr executive", "human resources",
]
EXCLUDED_ROLE_REDEEMERS = set()

# Delhi NCR search locations (Delhi, Noida, Gurgaon). Multi-city postings that
# include these still match (location_matches() is a substring check).
LOCATIONS = ["Delhi", "Noida", "Gurgaon"]

# Remote roles can be done from anywhere, so they're included — set False
# for office/hybrid jobs only. Controls both the extra "Remote"
# search in pipeline.sweep() and the "remote" pass in location_matches().
INCLUDE_REMOTE = True

# Aligned to Ayush's actual resume (resume_base.docx) — real skills only,
# so the confidence score reflects genuine fit and jd_analyzer never feeds
# the tailoring step a skill he doesn't have. Every entry below appears in
# his Skills, Experience or Projects sections.
MATCH_KEYWORDS = [
    # FP&A & Core Finance
    "fp&a", "financial planning", "budgeting", "forecasting", "variance analysis",
    "financial reporting", "mis", "cost monitoring", "kpi tracking",
    "financial modelling", "financial modeling", "3-statement", "three statement",
    "valuation", "dcf", "discounted cash flow", "scenario analysis", "sensitivity analysis",
    "benchmarking", "ratio analysis", "working capital", "ebitda", "operating leverage",
    "capital budgeting", "due diligence",
    # Accounting & Statements
    "p&l", "profit and loss", "balance sheet", "cash flow", "cash flow statement",
    "financial statements", "audit", "compliance", "rbi guidelines", "gaap",
    # Technical & Tools
    "excel", "advanced excel", "vlookup", "index-match", "pivot tables",
    "dynamic arrays", "power bi", "sql", "python", "pandas",
    "regression analysis", "dashboard", "dashboards", "data analysis",
    "data accuracy", "reporting templates",
]

# Minimum number of NON-generic MATCH_KEYWORDS a JD must hit (generic ones
# are listed below), and at least one must be a core finance/tool skill.
MIN_MATCH_COUNT = 2

# ── Skill weighting for ranking (pipeline.compute_confidence) ──────────────
# Core stack counts 3x, generic words almost nothing.
CORE_SKILLS = {
    "fp&a", "financial modelling", "financial modeling", "budgeting",
    "forecasting", "variance analysis", "financial reporting", "advanced excel",
    "excel", "power bi", "3-statement", "valuation", "balance sheet", "p&l", "cash flow",
}
GENERIC_SKILLS = {"reporting", "data analysis", "compliance", "audit", "dashboard", "mis", "data accuracy"}
CORE_SKILL_WEIGHT = 3
GENERIC_SKILL_WEIGHT = 0.5
OTHER_SKILL_WEIGHT = 2
# Must-have skills — a JD must mention at least one of these.
PROGRAMMING_SKILLS = {
    "excel", "advanced excel", "financial modelling", "financial modeling",
    "fp&a", "power bi", "sql", "python", "budgeting", "variance analysis",
    "financial reporting", "3-statement", "valuation", "ratio analysis",
}
# Weighted points that earn the full keyword score.
WEIGHTED_MATCH_CAP = 24

# JD text that says the role is genuinely open to freshers / early career — earns a
# ranking bonus (not required: many fresher JDs just don't say so).
FRESHER_SIGNALS = (
    r"\b(fresher|freshers|entry[- ]level|new grad(uate)?s?|recent graduates?|"
    r"20(24|25|26) (batch|pass ?outs?|graduates?)|batch of 20(24|25|26)|"
    r"management trainee|finance trainee|graduate trainee|"
    r"0\s*(-|–|to)\s*[123]\s*(years?|yrs?)|0 years experience|no (prior )?experience required)\b"
)
FRESHER_BONUS = 10

# Titles that name a specific finance/analyst role. Kept as SOFTWARE_TITLE_WORDS
# so pipeline.py's import remains unchanged.
SOFTWARE_TITLE_WORDS = {
    "finance", "financial", "fp&a", "fpa", "analyst", "modelling", "modeling",
    "valuation", "budgeting", "reporting", "accounts", "associate", "trainee",
    "executive", "excel",
}
GENERIC_TITLE_MIN_PROGRAMMING_SKILLS = 2

# Matched against the FULL JD text — only terms that disqualify a posting
# no matter where they appear.
BLOCKED_KEYWORDS = {
    "unpaid",
    "commission only",
}

# Matched against the TITLE only.
TITLE_ONLY_BLOCKED_KEYWORDS = {
    # Tech & Engineering
    "software",
    "developer",
    "engineer",
    "engineering",
    "frontend",
    "front end",
    "backend",
    "back end",
    "full stack",
    "fullstack",
    "devops",
    "qa",
    "sdet",
    "hardware",
    "electrical",
    "electronics",
    "mechanical",
    "civil",
    "chemical",
    "network",
    "sysadmin",
    # Non-finance
    "sales",
    "marketing",
    "medical",
    "nursing",
    "customer support",
    "designer",
    "graphic",
    "teacher",
    "content writer",
    "recruiter",
    # Internships
    "intern",
    "internship",
    # Seniority
    "senior",
    "sr",
    "lead",
    "principal",
    "staff",
    "architect",
    "manager",
    "head",
    "director",
    "vp",
    "vice president",
    "chief",
    "partner",
    "avp",
    "dgm",
    "gm",
    "ii",
    "iii",
}

# Third-party recruiting marketplaces that repost jobs on LinkedIn/Indeed
# under their own name as if THEY were the employer.
BLOCKED_COMPANIES = {
    "hire feed",
    "scoutit",
    "hired",
    "talentgigs",
}

# Maximum experience FLOOR a posting may require to be kept — candidate is
# an MBA graduate targeting early-career roles (0-2 years).
MAX_EXPERIENCE_YEARS = 2

# Employee-count thresholds + bonus points for the "big company" scoring
# boost in pipeline.compute_confidence(). jobspy reports company size as a
# bucketed string (e.g. "10,000+", "1,001 to 5,000") — parsed via
# pipeline.parse_company_size().
#
# Lowered back down 2026-08 (25/12 -> 10/5, set 2026-07) plus KEYWORD_MATCH_CAP/
# ATS_MATCH_BONUS added below — confirmed live against the real production
# DB (3,311 rows) that the 25/12 company bonus, stacked on top of a +40
# ATS-type bonus that ~83% of ALL postings already receive (detect_ats()
# scores anything not literally unrecognized as "non-generic", so LinkedIn/
# Naukri/Indeed postings get the same +40 as an actual Workday listing),
# was propping up repeat Genpact/PwC postings (10 real keyword matches,
# confidence 0.710) above genuinely stronger-fit postings at companies
# jobspy didn't report a size for (12-15 real keyword matches, confidence
# only 0.472-0.490 purely because company_size came back 0). Simulating
# the new weights across all 3,311 rows: 20 of the current top-40 postings
# by confidence are Genpact/PwC repeats propped up mainly by the company
# bonus and drop out, replaced by 20 postings with materially higher real
# keyword-match counts that were previously buried near 0.47-0.49.
BIG_COMPANY_MIN_EMPLOYEES = 1000
BIG_COMPANY_BONUS = 10
MID_COMPANY_MIN_EMPLOYEES = 200
MID_COMPANY_BONUS = 5

# compute_confidence() previously ran keyword match count through
# resume_scorer.score_resume() (0.6 per match + a placeholder ATS score
# worth up to 40) — that function is shared with dynamic_resume_builder.py's
# actual tailored-RESUME quality scoring (real ATS formatting/structure
# check), a genuinely different concern; reusing it here via a fake
# ats_result was a confusing coincidence, not an intentional shared
# formula, and its 0.6-per-match weighting made keyword fit almost
# irrelevant next to the flat ATS/company bonuses. compute_confidence()
# now has its own formula (see pipeline.py) where keyword match is the
# dominant factor: matches are scaled against KEYWORD_MATCH_CAP (chosen
# from the real distribution — median match count is 6, so 12 represents
# a genuinely strong, not just typical, fit) up to KEYWORD_MATCH_WEIGHT
# points, with the ATS/company-size bonuses reduced to real tiebreakers.
KEYWORD_MATCH_CAP = 12
KEYWORD_MATCH_WEIGHT = 75
ATS_MATCH_BONUS = 15

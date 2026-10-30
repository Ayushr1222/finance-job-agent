"""
summary_generator.py

Production ATS Summary Generator
"""

import re
import logging

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)

client = None
gemini_client = None

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

if GEMINI_API_KEY:
    from google import genai
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def _call_groq(prompt: str) -> str:
    if client is None:
        raise RuntimeError("Groq unavailable — no GROQ_API_KEY")
    # gpt-oss is a reasoning model: its hidden reasoning tokens count against
    # the completion budget, so the old 220-token cap (sized for a ~120-word
    # summary from llama-3.3) could leave no room for the answer itself.
    # reasoning_effort="low" keeps that overhead small; passed via
    # extra_body so it works on any groq SDK version.
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "low"},
    )
    content = (response.choices[0].message.content or "").strip()
    if not content:
        # Raise so generate_summary() falls through to Gemini instead of
        # writing an empty summary into the resume.
        raise RuntimeError(f"Groq returned an empty completion (finish_reason={response.choices[0].finish_reason})")
    return content


def _call_gemini(prompt: str) -> str:
    if gemini_client is None:
        raise RuntimeError("Gemini unavailable — no GEMINI_API_KEY")
    response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()


# Common preambles/wrapping an LLM sometimes adds despite being told
# "return only the summary" — stripped so they never end up verbatim in a
# resume a recruiter reads.
_LLM_PREAMBLE_RE_LIST = [
    r'^(?:sure[,!]?\s+)?here(?:\'s| is)\s+(?:the\s+)?(?:rewritten\s+|revised\s+|updated\s+|tailored\s+)?(?:professional\s+)?summary\s*:?\s*',
    r'^sure[,!]?\s*:?\s*',
]


def _clean_llm_output(text: str) -> str:
    text = text.strip().strip('"').strip("'").strip()
    for pattern in _LLM_PREAMBLE_RE_LIST:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return text


# Proper display casing for keywords that are acronyms/proper nouns — used
# only in the static fallback sentence below, so a technology name doesn't
# read as "Aws"/"Sql" if naively title-cased.
_DISPLAY_CASE = {
    "sql": "SQL", "power bi": "Power BI", "excel": "Excel",
    "advanced excel": "Advanced Excel", "python": "Python", "pandas": "Pandas",
    "fp&a": "FP&A", "fpa": "FP&A", "p&l": "P&L", "dcf": "DCF",
    "ebitda": "EBITDA", "mis": "MIS", "kpi": "KPI", "kpis": "KPIs",
    "kpi tracking": "KPI Tracking", "3-statement": "3-Statement Financial Modelling",
    "three statement": "3-Statement Financial Modelling",
    "financial modelling": "Financial Modelling", "financial modeling": "Financial Modeling",
    "variance analysis": "Variance Analysis", "budgeting": "Budgeting & Forecasting",
    "forecasting": "Forecasting", "financial reporting": "Financial Reporting",
    "working capital": "Working Capital Analysis", "ratio analysis": "Ratio Analysis",
    "due diligence": "Due Diligence", "scenario analysis": "Scenario Analysis",
    "sensitivity analysis": "Sensitivity Analysis", "operating leverage": "Operating Leverage",
    "capital budgeting": "Capital Budgeting", "rbi guidelines": "RBI Guidelines",
    "gaap": "GAAP", "kpmg": "KPMG", "rbi": "RBI", "vlookup": "VLOOKUP",
    "index-match": "INDEX-MATCH", "pivot tables": "Pivot Tables",
    "dynamic arrays": "Dynamic Arrays", "regression analysis": "Regression Analysis",
}


def _display_keyword(kw: str) -> str:
    return _DISPLAY_CASE.get(kw, kw[:1].upper() + kw[1:] if kw else kw)


def generate_summary(
    profile,
    job,
    keywords=None,
):

    keywords = keywords or []

    description = ""

    if isinstance(job, dict):
        description = job.get(
            "description",
            ""
        )
    else:
        description = str(job)

    current_summary = profile.get(
        "summary",
        ""
    )

    skills = profile.get(
        "skills",
        ""
    )

    experience = profile.get(
        "experience",
        ""
    )

    keyword_text = ", ".join(
        keywords[:20]
    )

    prompt = f"""
You are an expert resume writer.

Your task is NOT to invent new experience.

Rewrite ONLY the Professional Summary.

Current Summary

{current_summary}

Candidate Experience

{experience}

Technical Skills

{skills}

Target Job Description

{description}

Important ATS Keywords

{keyword_text}

Rules

1. 50-70 words — the resume must stay on one page.
2. Professional tone.
3. ATS optimized.
4. Mention only technologies already present in the candidate profile.
5. Naturally include the important keywords.
6. Do NOT exaggerate.
7. Do NOT mention years of experience unless already known.
8. Return only the summary.
"""

    # Returns (summary_text, source, llm_errors) — source/llm_errors let
    # callers (cloud_run.py) surface which path actually served each job,
    # and why, as a GitHub Actions annotation. A silent Groq/Gemini failure
    # here previously had no visible signal outside of logger.warning
    # (invisible without log access, which 403s without admin/write auth
    # on this repo) — confirmed live 2026-08-01: both APIs were failing
    # for 15/15 tailored resumes with no visible error text anywhere.
    llm_errors = {}
    try:
        return _fit_length(_clean_llm_output(_call_groq(prompt))), "groq", llm_errors
    except Exception as e:
        llm_errors["groq"] = str(e)
        logger.warning("Groq summary generation failed, falling back to Gemini: %s", e)

    try:
        return _fit_length(_clean_llm_output(_call_gemini(prompt))), "gemini", llm_errors
    except Exception as e:
        llm_errors["gemini"] = str(e)
        logger.warning("Gemini summary generation failed, using static fallback: %s", e)

    return _fit_length(_static_fallback_summary(keywords)), "fallback", llm_errors


# resume_base.docx is a one-page resume with only a few lines of slack
# (measured in Word, 2026-10: its own summary is ~53 words, and a 120-word
# summary — what the prompt used to ask for — pushed the whole EDUCATION
# section onto page 2). The prompt asks for 50-70 words, but LLMs overshoot
# word counts, so this is the enforced cap: trim back to the last full
# sentence that fits, falling back to a hard word cut only if no sentence
# ends within the limit.
SUMMARY_MAX_WORDS = 75


def _fit_length(text: str, max_words: int = SUMMARY_MAX_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    clipped = " ".join(words[:max_words])
    end = max(clipped.rfind(". "), clipped.rfind("! "), clipped.rfind("? "))
    if clipped.endswith((".", "!", "?")):
        return clipped
    if end > len(clipped) // 2:
        return clipped[:end + 1]
    return clipped.rstrip(",;:") + "."


def _static_fallback_summary(keywords) -> str:
    # Only reached when BOTH Groq and Gemini fail. The previous version
    # returned byte-identical prose across every JD except for one raw,
    # lowercase, comma-separated keyword clause bolted onto the end (e.g.
    # "...with expertise in python, sql, analytics, rds, ai, tableau, a/b
    # testing.") — an obvious "auto-generated" tell to any recruiter
    # comparing two of the candidate's applications, and ungrammatical
    # next to the properly capitalized prose around it. Weaves 2-3 real
    # keywords into an actual sentence instead, with correct display
    # casing for acronyms (via _display_keyword) rather than a bare dump.
    top = [_display_keyword(k) for k in keywords[:3]]
    if len(top) >= 2:
        keyword_clause = ", ".join(top[:-1]) + f", and {top[-1]}"
    elif top:
        keyword_clause = top[0]
    else:
        keyword_clause = None

    summary = (
        "MBA Finance professional (IMS Ghaziabad, CGPA 8.3/10) with Big 4 FP&A "
        "experience at KPMG India. Skilled in 3-statement financial modelling, "
        "variance analysis, budgeting, forecasting, and executive management reporting. "
        "Proficient in Advanced Excel, Power BI, Python, and SQL for automated financial "
        "modelling and KPI tracking. Seeking a Financial Analyst or FP&A role."
    )
    if keyword_clause:
        summary += f" Strong proficiency in {keyword_clause}."
    return summary
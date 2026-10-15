"""Explainable resume checks. Pure functions make this file easy to test."""

import re
import unicodedata
from datetime import datetime, timezone

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data import ACTION_VERBS, COMMON_TYPOS, SECTIONS, SKILLS

WEIGHTS = {"Structure": 20, "Content": 25, "Formatting": 15, "Language": 15, "Job match": 25}


def normalize(text):
    return unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")


def words(text):
    return re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)?", text.lower())


def contains_term(text, term):
    # Custom boundaries avoid matching Java in JavaScript or C++ in C++17.
    pattern = r"(?<![\w+#])" + re.escape(term) + r"(?![\w+#])"
    return bool(re.search(pattern, text, re.IGNORECASE))


def extract_skills(text):
    found = []
    for name, aliases in SKILLS.items():
        if any(contains_term(text, alias) for alias in aliases):
            found.append(name)
    return sorted(found, key=str.lower)


def heading_name(line):
    # Recognize standalone headings and inline labels such as "Skills: Python".
    label = line.strip().lstrip("# ").split(":", 1)[0].strip().lower()
    for name, aliases in SECTIONS.items():
        if label in aliases:
            return name
    return None


def find_achievement_lines(text):
    achievements = []
    current_section = None
    has_sections = any(heading_name(line) for line in text.splitlines())
    for line in text.splitlines():
        heading = heading_name(line)
        if heading:
            current_section = heading
            continue
        clean = re.sub(r"^\s*(?:[-*•◦▪‣]|\d+[.)])\s*", "", line).strip()
        tokens = words(clean)
        is_bullet = bool(re.match(r"^\s*(?:[-*•◦▪‣]|\d+[.)])\s*", line))
        starts_action = bool(tokens and tokens[0] in ACTION_VERBS)
        starts_weak = bool(re.match(r"^(worked|responsible|helped|assisted)\b", clean, re.I))
        eligible = current_section in {"Experience", "Projects"} or not has_sections
        if eligible and len(tokens) >= 5 and (is_bullet or starts_action or starts_weak):
            achievements.append(clean)
    return achievements


def has_metric(line):
    # A year or phone number alone is not an achievement. Look for useful units.
    return bool(re.search(
        r"\b\d+(?:[.,]\d+)?\s*(?:%|percent\b|users\b|customers\b|records\b|"
        r"hours\b|minutes\b|seconds\b|ms\b|requests\b|tests\b|endpoints\b|"
        r"files\b|reports\b|students\b|members\b|projects\b|datasets\b|x\b)"
        r"|[$₹€£]\s*\d+", line, re.IGNORECASE
    ))


def language_issues(text):
    issues = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for token in set(words(line)):
            if token in COMMON_TYPOS:
                issues.append({"line": line_number, "text": token,
                               "suggestion": f"Consider '{COMMON_TYPOS[token]}'."})
        for match in re.finditer(r"\b([A-Za-z]+)\s+\1\b", line, re.IGNORECASE):
            issues.append({"line": line_number, "text": match.group(),
                           "suggestion": "Check this repeated word."})
        if len(words(line)) > 40:
            issues.append({"line": line_number, "text": line[:140],
                           "suggestion": "Consider splitting this long line into shorter bullets."})
        if re.search(r"\b(i am|i have|my responsibilities|responsible for)\b", line, re.I):
            issues.append({"line": line_number, "text": line[:140],
                           "suggestion": "Start with a direct action verb and describe your contribution."})
    return sorted(issues, key=lambda issue: (issue["line"], issue["text"]))


def compare_job(resume, job):
    resume_skills = extract_skills(resume)
    required = extract_skills(job)
    matched = sorted(set(resume_skills) & set(required), key=str.lower)
    missing = sorted(set(required) - set(resume_skills), key=str.lower)
    result = {"available": bool(job.strip()), "resume_skills": resume_skills,
              "job_skills": required, "matched": matched, "missing": missing,
              "coverage": None, "similarity": None, "score": None,
              "keywords": [], "note": "Add a job description to calculate role alignment."}
    if not job.strip():
        return result

    # TF-IDF gives each word a weight. Cosine similarity compares the two vectors.
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    try:
        matrix = vectorizer.fit_transform([resume, job])
        similarity = float(cosine_similarity(matrix[0], matrix[1])[0][0]) * 100
        names = vectorizer.get_feature_names_out()
        job_weights = matrix[1].toarray()[0]
        top_indices = job_weights.argsort()[::-1]
        for index in top_indices:
            term = str(names[index])
            if job_weights[index] > 0 and len(term) >= 3 and not term.isdigit():
                result["keywords"].append({"term": term, "found": contains_term(resume, term)})
            if len(result["keywords"]) == 12:
                break
    except ValueError:
        # For example: an input containing only English stop words.
        similarity = 0.0

    result["similarity"] = round(similarity, 1)
    if required:
        coverage = len(matched) / len(required) * 100
        result["coverage"] = round(coverage, 1)
        result["score"] = round(0.75 * coverage + 0.25 * similarity)
        result["note"] = "75% skill coverage + 25% TF-IDF similarity. Mentions are not proof of proficiency."
    else:
        result["score"] = round(similarity)
        result["note"] = "No job skills matched the small dictionary. This score uses TF-IDF only and is less informative."
    return result


def analyze_resume(text, job_description="", metadata=None):
    text = normalize(text)
    job_description = normalize(job_description)
    metadata = metadata or {"source": "Pasted text", "pages": None, "warnings": []}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    word_count = len(words(text))
    sections = sorted({heading_name(line) for line in lines if heading_name(line)})
    bullets = find_achievement_lines(text)
    action_lines = [line for line in bullets if words(line)[0] in ACTION_VERBS]
    metric_lines = [line for line in bullets if has_metric(line)]
    issues = language_issues(text)
    job = compare_job(text, job_description)
    checks = []

    def check(category, title, passed, detail, advice):
        checks.append({"category": category, "title": title, "passed": bool(passed),
                       "detail": detail, "advice": advice})

    for section in ["Education", "Skills"]:
        check("Structure", f"{section} section", section in sections,
              f"Looks for a recognizable {section.lower()} heading.",
              f"Add a clear '{section}' heading on its own line.")
    check("Structure", "Experience or projects", bool(set(sections) & {"Experience", "Projects"}),
          "Projects count for students who do not yet have work experience.",
          "Include an Experience or Projects section with your contributions.")
    has_email = bool(re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text))
    check("Structure", "Email found", has_email, "Checks for an email address in extracted text.",
          "Put a professional contact email in the document body.")

    action_ratio = len(action_lines) / len(bullets) if bullets else 0
    metric_ratio = len(metric_lines) / len(bullets) if bullets else 0
    check("Content", "Contribution bullets", len(bullets) >= 3,
          f"Found {len(bullets)} contribution lines; this demo targets at least 3.",
          "Write at least three specific contribution bullets under Experience or Projects.")
    check("Content", "Action verbs", action_ratio >= 0.6,
          f"{len(action_lines)} of {len(bullets)} contribution lines start with a recognized action verb.",
          "Start more bullets with verbs such as Built, Analyzed, Implemented or Improved.")
    check("Content", "Measurable outcomes", metric_ratio >= 0.4,
          f"{len(metric_lines)} of {len(bullets)} contribution lines contain a recognized metric.",
          "Add real measurements where available: users, time saved, test count or percentage improvement. Never invent numbers.")
    check("Content", "Concise bullets", bool(bullets) and all(len(words(line)) <= 35 for line in bullets),
          "This demo targets no more than 35 words per contribution line.",
          "Keep each contribution focused on an action, method and result.")

    check("Formatting", "Readable length", 180 <= word_count <= 1000,
          f"Found {word_count} words; the learning heuristic uses 180–1,000 words.",
          "Review the amount of detail for your experience level. The length range is a project heuristic.")
    check("Formatting", "Text organized into lines", len(lines) >= 8,
          f"Found {len(lines)} non-empty lines.",
          "Use separate lines for headings and bullets, then check the extracted-text preview.")
    check("Formatting", "No obvious extraction corruption", "�" not in text and "\x00" not in text,
          "Looks for replacement characters and null bytes.",
          "Re-export the resume using standard fonts and check its copied text.")
    check("Formatting", "Simple text separators", sum(line.count("|") >= 3 for line in lines) < 3,
          "Repeated pipe-separated columns can be a reading-order warning; this is not a visual layout check.",
          "Consider a simpler single-column layout and verify the reading order.")

    check("Language", "Common typo check", not any(word in COMMON_TYPOS for word in words(text)),
          "Checks only the small typo dictionary in data.py.", "Review the spelling suggestions below.")
    check("Language", "Repeated words", not re.search(r"\b([A-Za-z]+)\s+\1\b", text, re.I),
          "Looks for consecutive repeated words.", "Remove accidental repeated words.")
    check("Language", "Direct phrasing", not re.search(r"\b(i am|i have|my responsibilities|responsible for)\b", text, re.I),
          "Looks for a few indirect phrases.", "Replace indirect phrases with actions and evidence.")
    check("Language", "Readable line length", all(len(words(line)) <= 40 for line in lines),
          "Flags lines with more than 40 words.", "Split dense lines into shorter bullets.")

    categories = []
    for name, weight in WEIGHTS.items():
        category_checks = [item for item in checks if item["category"] == name]
        if name == "Job match":
            score = job["score"]
        else:
            score = round(sum(item["passed"] for item in category_checks) / len(category_checks) * 100)
        categories.append({"name": name, "weight": weight, "score": score, "checks": category_checks})

    available = [category for category in categories if category["score"] is not None]
    total_weight = sum(category["weight"] for category in available)
    overall = round(sum(category["score"] * category["weight"] for category in available) / total_weight)
    recommendations = [item["advice"] for item in checks if not item["passed"]]
    if job["missing"]:
        recommendations.insert(0, "Review these job skills and add evidence only if accurate: " + ", ".join(job["missing"]) + ".")
    strengths = [item["title"] for item in checks if item["passed"]]
    return {
        "title": "ATS Resume Scorer — Learning Report",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overall_score": overall,
        "label": "Strong foundation" if overall >= 80 else "Room to improve" if overall >= 60 else "Start with the basics",
        "disclaimer": "An explainable project heuristic, not an employer ATS score or hiring prediction.",
        "scoring_note": f"Weighted average over {total_weight} available weight points. AI feedback does not change this score.",
        "word_count": word_count, "sections": sections, "categories": categories,
        "bullet_count": len(bullets), "action_bullets": action_lines, "metric_bullets": metric_lines,
        "strengths": strengths, "recommendations": recommendations,
        "language_issues": issues, "job": job, "file": metadata,
        "ai": {"status": "off", "message": "Optional AI review was not requested.", "review": None},
    }

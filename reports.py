"""Convert the report dictionary into a readable downloadable text report."""


def report_as_text(report):
    lines = [report["title"], "=" * 55, report["created_at"],
             f"Score: {report['overall_score']}/100 — {report['label']}",
             report["disclaimer"], report["scoring_note"],
             f"Words: {report['word_count']} | Contribution lines: {report['bullet_count']}",
             "Sections: " + ", ".join(report["sections"]), "", "SCORE BREAKDOWN"]
    for category in report["categories"]:
        score = category["score"]
        lines.append(f"{category['name']}: {score if score is not None else 'N/A'} (weight {category['weight']})")
        for check in category["checks"]:
            lines.append(f"  {'PASS' if check['passed'] else 'REVIEW'} — {check['title']}: {check['detail']}")
    for heading, items in [("STRENGTHS", report["strengths"]), ("RECOMMENDATIONS", report["recommendations"]),
                           ("FILE NOTES", report["file"]["warnings"])]:
        lines.extend(["", heading])
        lines.extend("- " + item for item in items)
        if not items:
            lines.append("None from these checks.")
    job = report["job"]
    lines.extend(["", "JOB ALIGNMENT", job["note"],
                  "Resume skill mentions: " + ", ".join(job["resume_skills"]),
                  "Matched job skills: " + ", ".join(job["matched"]),
                  "Missing job skills: " + ", ".join(job["missing"]),
                  f"Skill coverage: {job['coverage']} | TF-IDF similarity: {job['similarity']}"])
    for keyword in job["keywords"]:
        lines.append(f"- {keyword['term']}: {'found' if keyword['found'] else 'not found'}")
    lines.extend(["", "BASIC LANGUAGE CHECKS", "Limited rules, not a complete grammar or spell check."])
    for issue in report["language_issues"]:
        lines.append(f"- Line {issue['line']}: {issue['text']} — {issue['suggestion']}")
    ai = report["ai"]
    lines.extend(["", "OPTIONAL AI REVIEW", ai["message"]])
    if ai["review"]:
        review = ai["review"]
        lines.append(review["summary"])
        for item in review["skill_checks"]:
            lines.extend([f"- {item['skill']} ({item['status']}): {item['explanation']}",
                          f"  Job quote: {item['job_evidence']}", f"  Resume quote: {item['resume_evidence']}"])
        for field in ["writing_suggestions", "bullet_rewrites"]:
            lines.append(field.replace("_", " ").upper())
            for item in review[field]:
                lines.extend(["- Original: " + item["original"], "  Suggestion: " + item["suggestion"], "  Why: " + item["reason"]])
        lines.extend("- " + item for item in review["recommendations"])
        lines.append(f"Items removed for unsupported quotes or new numbers: {review['discarded_items']}")
    return "\n".join(lines)

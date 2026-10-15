"""Flask connects the browser to our ordinary Python functions."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request, session

from ai_review import get_ai_review
from analyzer import analyze_resume, words
from parser import MAX_TEXT_CHARS, parse_upload
from reports import report_as_text

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # New local session key each restart.
app.config.update(MAX_CONTENT_LENGTH=6 * 1024 * 1024,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def render_home(error=None, resume_text="", job_description=""):
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return render_template("index.html", error=error, resume_text=resume_text,
                           job_description=job_description,
                           ai_ready=bool(os.getenv("OPENAI_API_KEY", "").strip()))


@app.get("/")
def home():
    if request.args.get("demo") == "1":
        return render_home(
            resume_text=(BASE_DIR / "samples" / "sample_resume.txt").read_text(encoding="utf-8"),
            job_description=(BASE_DIR / "samples" / "sample_job.txt").read_text(encoding="utf-8"),
        )
    return render_home()


@app.post("/analyze")
def analyze():
    # The form token prevents another website from silently submitting this form.
    expected = session.get("csrf_token", "")
    submitted = request.form.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, submitted):
        return render_home("Your form expired. Please submit it again."), 400

    text = request.form.get("resume_text", "").strip()
    job = request.form.get("job_description", "").strip()
    upload = request.files.get("resume_file")
    has_upload = upload is not None and bool(upload.filename)
    metadata = {"source": "Pasted text", "pages": None, "warnings": []}
    try:
        if has_upload and text:
            raise ValueError("Use either a file or pasted resume text. Clear one before submitting.")
        if not has_upload and not text:
            raise ValueError("Upload a resume or paste its text to get started.")
        if has_upload:
            text, metadata = parse_upload(upload)
        if len(text) > MAX_TEXT_CHARS or len(job) > 15000:
            raise ValueError("Use at most 30,000 resume characters and 15,000 job-description characters.")
        if len(words(text)) < 20:
            raise ValueError("Please provide at least 20 words of resume text for a useful analysis.")
        report = analyze_resume(text, job, metadata)
        if request.form.get("use_ai") == "yes":
            report["ai"] = get_ai_review(text, job)
        return render_template("report.html", report=report, extracted_text=text,
                               report_text=report_as_text(report))
    except ValueError as error:
        # Keep pasted inputs so the user does not need to type everything again.
        return render_home(str(error), request.form.get("resume_text", "")[:MAX_TEXT_CHARS], job[:15000]), 400


@app.errorhandler(413)
def too_large(error):
    return render_home("The request is too large. Use a resume file below 5 MB and shorter text inputs."), 413


@app.after_request
def protect_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


if __name__ == "__main__":
    # Local learning server. Debug is off so errors cannot expose personal data.
    app.run(host="127.0.0.1", port=5000, debug=False)

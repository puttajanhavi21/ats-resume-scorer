# Verification notes

Verified on Windows with Python 3.12.14 on 14 October 2026. Exact installed package versions are in `requirements-tested.txt`.

## Automated verification

28 tests pass using Python's built-in `unittest` runner. The checks cover:

- Skill aliases, whole-term boundaries and Java versus JavaScript.
- Metric detection without counting a year alone as an achievement.
- Correct weighting with no job description, recognized skills and unknown job vocabulary.
- Stop-word-only input, repeated skill mentions and score bounds.
- Section headings, common typos and repeated words.
- Actual TXT, DOCX and generated text-based PDF extraction.
- DOCX paragraph/table order and informational warnings.
- Encrypted, long, empty, corrupt, oversized and unsupported files.
- Flask home/demo pages, file/paste submission, validation and request limits.
- Form token validation, escaped user HTML and response cache headers.
- Embedded report JSON and generated text-report content.
- AI opt-in, missing key, unsupported evidence, invented numeric values, incomplete output and provider errors.
- The installed OpenAI SDK's actual structured-request/response parsing using a fake HTTP transport, with no external API call.

`pip check` also passes with no broken dependency requirements.

## Browser verification

The local app was opened in a browser. The fictional example produced an overall score of 87/100, including a 47/100 job-match category. The form, report, score breakdown and visible explanatory text were inspected. TXT and JSON downloads completed successfully. No warning/error console messages were recorded in that flow.

The downloaded report was checked against the generated data and is included in `samples/sample_report.txt`. A screenshot of the report is included in `samples/app_preview.png`.

## Limits of this verification

- No live or paid OpenAI request was made. Account credentials, billing, model access and generated-response quality must be tried with your own API account.
- Tests validate the implemented rules, not commercial ATS accuracy or hiring outcomes.
- PDF fixtures are intentionally simple; complex real-world layouts need manual extracted-text review.
- The browser Print / Save as PDF command is provided, but an actual operating-system print/save dialog was not exercised.
- The Windows launcher is provided for convenience; verification used the equivalent direct Python commands.
- Responsive CSS is included. Browser visual inspection used the available desktop viewport, not a complete device/browser test matrix.

## Run it yourself

From the project folder, after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

On macOS/Linux, use `.venv/bin/python` instead. The automated suite does not require a real API key or network access.

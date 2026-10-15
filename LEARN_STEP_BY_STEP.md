# Learn it, rebuild it, explain it

The aim is not to memorize the finished files. Rebuild one feature at a time, predict what it should do, run it, and explain why the result makes sense.

## What you should know first

Practice Python strings, lists, dictionaries, sets, loops, `if`, functions, imports and `try/except`. Learn the idea of an HTML form and an HTTP request. You can learn the other concepts while building.

A dictionary is a labeled container:

```python
report = {"score": 75, "missing": ["Docker"]}
print(report["score"])
```

A function receives inputs and returns a result:

```python
def score_checks(passed, total):
    return round(passed / total * 100)
```

`analyzer.py` mostly combines these ideas. The AI file uses small Pydantic classes to describe response fields; leave it until the end.

## The whole request in one picture

```text
Browser form
    |
    | POST /analyze
    v
app.py validates the request
    |
    +-- uploaded file --> parser.py --> plain text
    +-- pasted text -----------------> plain text
    |
    v
analyzer.py + data.py --> report dictionary
    |
    +-- AI checkbox enabled --> ai_review.py --> extra feedback
    |
    v
report.html displays the report
    |
    +-- reports.py --> TXT download
    +-- report dictionary --> JSON download
    +-- browser print --> paper / PDF
```

No database sits in the middle. The HTML report already contains the data needed for downloads. The full extracted resume is displayed separately so the user can check it; TXT/JSON exports omit the full raw resume, although findings may contain excerpts. Printed reports include the text preview.

## Stage 1 — Build a tiny Python checker

Create a separate practice folder. Write a script with a resume string and three checks: Education present, Skills present, email present. Initially use `"education" in resume.lower()` so you understand the basic idea.

Then test the sentence “My education taught me useful skills.” Your simple check calls those headings even though they are ordinary words. Improve it by splitting into lines and comparing complete heading labels. This is why the finished project has `heading_name()`.

**Checkpoint:** explain the difference between detecting a word and detecting a heading. Add “Academic Qualifications” as an Education alias and test it.

## Stage 2 — Understand `data.py`

Read the dictionary keys and values. A key such as `"NLP"` is the displayed name. Its list contains alternate spellings such as `"natural language processing"`.

Use a loop to search aliases. Keep one result per canonical skill. The finished function uses regular expressions to avoid partial matches: Java should not match JavaScript. `re.escape()` turns characters like `+` into literal symbols, so C++ works correctly.

**Checkpoint:** add a skill you actually use and two reasonable aliases. Show that Java is not detected from JavaScript alone. Do not assume that an alias dictionary is semantic AI.

## Stage 3 — Compare two skill lists

Python sets make matching easy:

```python
resume_skills = {"Python", "Flask"}
job_skills = {"Python", "Flask", "Docker"}
matched = resume_skills & job_skills
missing = job_skills - resume_skills
coverage = len(matched) / len(job_skills) * 100
print(matched, missing, coverage)
```

Here coverage is about 66.7%. Handle an empty job set before dividing. In the real project, a missing job description gets N/A rather than a fake zero.

**Checkpoint:** explain why repeating “Python” ten times does not improve set coverage. Then explain why merely mentioning Python does not prove proficiency.

## Stage 4 — Add text similarity

Read `compare_job()` in `analyzer.py`. Focus on these operations:

```python
vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
matrix = vectorizer.fit_transform([resume, job])
similarity = cosine_similarity(matrix[0], matrix[1])[0][0]
```

TF means term frequency: how often a word appears. IDF gives relatively less weight to terms shared across documents. The vectorizer creates a numeric representation for each text. `(1, 2)` includes individual words and pairs of words. Cosine similarity measures the direction alignment of those vectors. Here their values are nonnegative, so the result ranges from 0 to 1.

Identical meaningful text should be near 1. Different wording may score poorly even when the meaning is similar. This is a lexical method, not a semantic model. The project uses it alongside dictionary coverage, and displays the two values separately.

**Checkpoint:** compare “I built web applications” with “I developed websites.” Explain why shared meaning does not guarantee a high lexical score. Try a stop-word-only input and inspect the error handling.

## Stage 5 — Check contribution bullets and language

Read `find_achievement_lines()`, `has_metric()` and `language_issues()`.

The contribution-line function tracks which section is currently being read. It accepts bullets or recognizable action-style lines in Experience/Projects. It checks the first word against `ACTION_VERBS`. A metric check searches for numbers with useful units. A year alone does not count.

The local spelling checker is deliberately a small list of common typos. It does not label every unfamiliar technology or person's name as wrong. Repeated words and long lines are separate checks.

**Checkpoint:** test “Built an app in 2024” and “Built an app used by 50 students.” Explain why only the second has a recognized metric. Add a typo rule, then create a sentence that should and should not trigger it.

## Stage 6 — Assemble a report dictionary

Read `analyze_resume()` from top to bottom. It first calculates facts, then creates individual checks, then groups them into categories. The small inner `check()` function avoids repeating the same dictionary creation code.

Study `WEIGHTS` and calculate one result by hand using `SCORING_AND_LIMITATIONS.md`. A weighted average lets one category contribute more than another. The chosen weights are design decisions, not learned hiring rules.

The final return value contains the score, details, strengths, recommendations and job comparison. Keeping analysis in ordinary functions means it can run without Flask, which makes testing easier.

**Checkpoint:** change the action-verb threshold from 60% to 75%. Predict what should change for a four-bullet resume with two strong openers before you run it.

## Stage 7 — Connect Flask

Read `app.py`. `Flask(__name__)` creates the application. A route decorator connects a URL to a function. The GET route displays the form. The POST route reads the user's fields and calls the analysis functions.

`request.form` contains text fields. `request.files` contains uploaded files. `render_template()` inserts Python values into HTML using Jinja. In a template, `{{ value }}` displays a value and `{% for item in items %}` repeats a block.

The hidden form token is stored in Flask's signed session cookie and compared on submission. Its purpose is to stop other websites from silently submitting the form. Resume text and reports are not put in the session. The code keeps this small protection in `app.py`; it is not the core scoring logic.

**Checkpoint:** first build a form with one textarea and display its word count. Only then add the full report. Trace an empty submission through the error path.

## Stage 8 — Add document uploads

Read `parser.py`. A file is bytes; the analyzer wants text. TXT bytes are decoded as UTF-8. `PdfReader` extracts PDF page text. `Document` reads DOCX body content. `BytesIO` lets libraries treat in-memory bytes like a file.

The parser checks extensions, size, page count and extraction results. It returns text plus metadata such as warnings. Errors become friendly `ValueError` messages for the route to display.

Do not confuse extracting text with seeing the document. An image-only PDF is still a PDF, but there may be no usable text to extract. Fonts and columns can also affect reading order.

**Checkpoint:** upload a TXT, a text-based PDF and a DOCX. Compare the preview with the source. Try an empty file and a damaged file and explain the resulting messages.

## Stage 9 — Read the interface and exports

Read `base.html` first, then `index.html`, then `report.html`. Template inheritance avoids copying the header/footer into every page. CSS classes control appearance. The interface uses standard HTML instead of a frontend framework.

`app.js` adds character counting, a loading message and local download buttons. `JSON.parse()` reads report data embedded by Jinja's `tojson` filter. A browser `Blob` creates a downloadable file. This avoids adding server-side report storage or a separate download API.

Jinja escapes ordinary values so uploaded text is displayed as text instead of executable HTML. Never add `|safe` to resume or AI content. `tojson` safely prepares values for the JSON script blocks.

**Checkpoint:** change one visual color, then add a report field such as the detected section count. Trace it from Python to HTML and to the JSON export.

## Stage 10 — Add Generative AI last

Read `ai_review.py` in this order: the response classes, `quote_exists()`, `validate_evidence()`, `INSTRUCTIONS`, then `get_ai_review()`.

The Pydantic classes describe structured output. For example, a skill check has a name, a constrained status, two evidence strings and an explanation. They are data shapes, not inheritance-heavy application architecture. The API returns a parsed `Review` object, and `.model_dump()` converts it into a familiar dictionary.

The model receives instructions separately from document text. The prompt asks it to treat documents as data, compare meaning, cite evidence and preserve facts. No tools are available to the model. Quote validation removes unsupported excerpts, and the rewrite filter rejects new numeric values. These are useful checks, not proof that a model cannot make mistakes.

Missing credentials, timeout/provider failures, refusal and incomplete output should not destroy the local report. Tests mock those situations. The API key stays on the Python side, in an ignored `.env` file, and AI is opt-in for each submission.

**Checkpoint:** explain the difference between a dictionary alias, TF-IDF similarity and semantic interpretation. Explain why a valid quote can still be misinterpreted. Test with fictional information before using personal documents.

## Stage 11 — Test behavior

Read `tests/test_project.py`. `unittest` is part of Python. An assertion states what should be true. For example, JavaScript must not create a Java match, no-job scoring must exclude that category, and a corrupted PDF must show an error.

The Flask test client submits requests without opening a browser. The AI tests replace network-dependent objects with mocks so tests are reproducible and free. Passing mocked tests verifies integration behavior; it does not verify live model quality or API account access.

**Checkpoint:** write one regression test for a bug you find. Confirm that it fails before your fix and passes afterward.

## Explain it in an interview

Practice a short explanation in your own words:

“I built a Flask application that extracts resume text and produces an explainable report. The local pipeline uses section rules, action-verb and metric checks, a skill-alias dictionary, and TF-IDF cosine similarity. An optional language-model review adds semantic evidence and writing suggestions. I validate quoted evidence, keep AI feedback separate from the numerical score, and test file parsing and failure cases.”

Be ready for these questions:

1. **Why Flask?** It keeps request handling and templates small while the analysis remains plain Python.
2. **Is the score accurate?** It is an explicit heuristic. You would need a labeled evaluation dataset and defined targets before making accuracy claims.
3. **Is TF-IDF semantic AI?** No. It represents lexical features. The optional language model handles contextual interpretation.
4. **What happens without a job description or API key?** General local analysis still runs; missing features are marked unavailable rather than fabricated.
5. **Can someone game the score?** Yes. Keyword mentions and simple thresholds can be manipulated. That is a limitation, not a hiring decision system.
6. **What did you personally change?** Show a real extension, its design reasoning and a test you wrote.

After you understand, rebuild and customize it, describe what you actually completed. Possible resume bullets:

- Built a Flask resume analyzer with PDF/DOCX/TXT extraction, explainable quality checks and downloadable evaluation reports.
- Implemented skill-alias matching and TF-IDF cosine similarity to compare resumes with job descriptions and identify keyword gaps.
- Added an optional Generative AI review with structured outputs, evidence-quote validation and graceful API-failure handling.

Use the third bullet only after configuring and trying the AI feature yourself. Do not claim that you trained a model, replicated a real ATS or achieved measured accuracy unless you actually did that work.

## Your first independent extension

Pick one: expand skills for a different career domain, support another section heading, improve wrapped-bullet detection, or add an evaluation CSV with manually labeled cases. Write down the limitation, change the smallest relevant function, and test the behavior. Being able to explain that change matters more than having a larger feature list.

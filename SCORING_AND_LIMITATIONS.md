# Scoring and limitations

Every threshold here is a project design choice. No hiring dataset was used to train or validate these scores. They help you inspect resume-writing signals; they do not reproduce a commercial ATS.

## Overall score

| Category | Weight | Category calculation |
| --- | ---: | --- |
| Structure | 20 | Four equally weighted checks |
| Content | 25 | Four equally weighted checks |
| Formatting | 15 | Four equally weighted text checks |
| Language | 15 | Four equally weighted limited checks |
| Job match | 25 | Skill coverage combined with TF-IDF similarity |

For each of the first four categories, `score = round(passed_checks / 4 * 100)`.

The overall score is `round(sum(category_score * weight) / sum(available_weights))`.

With a job description, available weights sum to 100. Without one, Job match is N/A and the other weights sum to 75. A missing job description is not scored as zero.

Example: structure 100, content 75, formatting 100, language 75, job match 60:

```text
(100*20 + 75*25 + 100*15 + 75*15 + 60*25) / 100 = 80
```

AI output never changes the numerical score. This keeps repeated local analyses explainable. Labels are 80–100: Strong foundation; 60–79: Room to improve; 0–59: Start with the basics.

## Exact checks

Structure passes one check for each of: a recognized Education heading, a recognized Skills heading, either Experience or Projects, and an email-shaped string. Summary and Certifications are detected but are not required. Projects count for students without employment history.

Content checks: at least three contribution lines; at least 60% begin with a listed action verb; at least 40% contain a recognized metric; all contribution lines have at most 35 words. The last check also requires at least one contribution line.

Contribution lines must have at least five alphabetic tokens and start with a bullet, listed action verb or a short list of weak openers. When recognized headings exist, only lines under Experience or Projects are eligible. Otherwise, such lines anywhere in the input are eligible. Wrapped bullet lines are not reliably joined. Headings with an inline body after a colon are detected, but a contribution on that same heading line is not counted.

Metrics are numbers with recognized units (percent, users, tests, hours and other units in `has_metric`) or currency amounts. A year alone is not a metric. This still cannot prove that a number describes impact or is true.

Formatting checks: 180–1,000 alphabetic word tokens; at least eight non-empty lines; no replacement characters/null bytes; fewer than three lines containing at least three pipe separators. DOCX table warnings and extraction notices are informational and do not deduct additional points. These rules do not measure margins, fonts, page layout, document accessibility or commercial ATS parsing reliability.

Language checks: none of the listed common typos; no consecutive repeated word; none of four indirect phrases; no line longer than 40 words. A score of 100 only means those few rules passed. It does not mean perfect grammar or spelling. English is the supported language for the dictionaries and tokenizer.

## Job match

1. Extract canonical skill names using the manually maintained aliases in `data.py`.
2. `coverage = matched_job_skills / recognized_job_skills * 100`.
3. Fit `TfidfVectorizer` on the resume and job description with English stop words removed, unigrams and bigrams, and at most 5,000 features.
4. Compute cosine similarity between their vectors, then multiply it by 100.
5. If the job contains recognized skills, `job_score = round(0.75 * coverage + 0.25 * similarity)`.
6. If there are no recognized skills, use TF-IDF similarity alone and show a warning.

TF-IDF weights are fitted to just two documents. This is a small demonstration, not a calibrated relevance model. Repeated skill mentions do not increase dictionary coverage, though repetition can change TF-IDF vectors. The displayed top 12 job terms may include generic language; they are not necessarily requirements and do not independently affect the score.

Skill matching handles aliases and boundaries but not negation, proficiency or required/preferred distinctions. “No experience with Docker” still contains Docker. The dictionary is oriented toward software and data roles. Terms outside it can be missed. Avoid adding unsupported claims just to raise the score.

## Optional semantic AI review

The language model receives the resume and job description and returns structured evidence, writing suggestions and recommendations. Supported/partial skills require a non-empty quote from both documents; not-found skills require a job quote and an empty resume quote. Whitespace and case are normalized for quote matching.

Writing suggestions and bullet rewrites require an original quote present in the resume. New numeric values are rejected. This filter cannot catch all fabricated facts, changed meaning, false skill interpretations, or changes such as “5 tests” to “5 million users.” It verifies text grounding, not factual correctness. AI summaries and general recommendations are not independently grounded by the filter. Human review is essential before reuse.

## File handling limits

- PDF text extraction does not perform OCR or reliably reconstruct visual reading order. Mixed text/image PDFs may yield incomplete content.
- Encrypted PDFs, PDFs longer than ten pages and unreadable files are rejected.
- DOCX body paragraphs and tables are read in order. Headers, footers, text boxes and images are not extracted. Tables produce a warning.
- File/request/text limits and an expanded-DOCX size check reduce accidental overload. They are not complete protection against adversarial documents. The PDF content-size check occurs after decompression, and PDF libraries may consume significant resources while parsing.
- The local development server is intended for your own learning and documents. Public deployments need document processing in an isolated worker with resource limits, plus authentication and rate limiting.

## Sensible next improvements

Add domain-specific skills, evaluate false positives against a manually labeled sample, distinguish required/preferred job skills, improve wrapped-bullet extraction, and add an optional OCR workflow. Measure a feature before making accuracy claims about it.

"""Turn PDF, DOCX or UTF-8 TXT uploads into ordinary Python strings."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from docx import Document
from pypdf import PdfReader

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 30000
MAX_PDF_PAGES = 10


def parse_upload(upload):
    """Return (text, metadata). Never save the uploaded file in our project."""
    extension = Path(upload.filename).suffix.lower()
    if extension not in {".pdf", ".docx", ".txt"}:
        raise ValueError("Please upload a PDF, DOCX or UTF-8 TXT file.")

    data = upload.read(MAX_FILE_BYTES + 1)
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("The resume must be smaller than 5 MB.")

    metadata = {"source": extension[1:].upper(), "pages": None, "warnings": []}
    try:
        if extension == ".txt":
            text = data.decode("utf-8-sig")
            if "\x00" in text:
                raise ValueError("This does not look like a plain-text file. Use UTF-8 TXT.")

        elif extension == ".pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError("This file is not a valid PDF.")
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise ValueError("Please upload an unencrypted PDF.")
            metadata["pages"] = len(reader.pages)
            if metadata["pages"] > MAX_PDF_PAGES:
                raise ValueError("Please use a resume with 10 pages or fewer.")
            parts = []
            for page in reader.pages:
                # A small PDF can contain a large decompressed content stream.
                content = page.get_contents()
                if content is not None and len(content.get_data()) > 10 * 1024 * 1024:
                    raise ValueError("This PDF page is too complex. Export a simpler PDF.")
                parts.append(page.extract_text() or "")
            text = "\n".join(parts)
            if any(len(part.strip()) < 30 for part in parts):
                metadata["warnings"].append(
                    "At least one PDF page has little extractable text. Check the text preview; images are not read."
                )

        else:
            # DOCX is a ZIP archive. Reject oversized expanded contents first.
            with ZipFile(BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 20 * 1024 * 1024:
                    raise ValueError("This DOCX expands to more than 20 MB. Use a simpler file.")
            document = Document(BytesIO(data))
            parts = []
            # Preserve the order of paragraphs and tables in the document body.
            for block in document.iter_inner_content():
                if hasattr(block, "text"):
                    parts.append(block.text)
                else:
                    for row in block.rows:
                        parts.append(" | ".join(cell.text for cell in row.cells))
            text = "\n".join(parts)
            if document.tables:
                metadata["warnings"].append(
                    "Tables were found in the DOCX. Check the reading order and consider a single-column layout."
                )
            metadata["warnings"].append(
                "DOCX headers, footers, images and text boxes are not extracted. Keep important details in the document body."
            )

    except UnicodeDecodeError as error:
        raise ValueError("Please save your text file using UTF-8 encoding.") from error
    except (BadZipFile, OSError, KeyError) as error:
        raise ValueError("This file could not be read. Try exporting it again.") from error
    except ValueError:
        raise
    except Exception as error:
        # File libraries raise several different errors for damaged documents.
        raise ValueError("This document could not be read. Try another file or paste its text.") from error

    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("The extracted resume is too long. Use at most 30,000 characters.")
    if len(text.strip()) < 50:
        raise ValueError("Not enough text was found. Scanned PDFs need OCR first; you can also paste the resume text.")
    return text.strip(), metadata

"""Build the public, redacted copy of the CV and verify it.

Reads   originals/CV_Swatantra_Dhara.pdf   (private, git-ignored)
Writes  assets/Swatantra_Dhara_CV.pdf      (published)

What is removed (the text itself is deleted from the page content, not covered):
  * the contact line with the phone number and e-mail address,
  * every other e-mail address (supervisors' addresses in parentheses),
  * the "Documents:" short-link line,
  * mailto:/tel: links and short-link annotations.

The script then re-opens the result and fails loudly if any of that text can
still be extracted (with two independent PDF libraries) or found in the raw,
decompressed PDF objects.

Usage:  pip install pymupdf pypdf
        python scripts/redact_cv.py
(Tested with PyMuPDF 1.24.14 and pypdf 6.x.)
"""
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pypdf

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "originals" / "CV_Swatantra_Dhara.pdf"
DST = ROOT / "assets" / "Swatantra_Dhara_CV.pdf"

SHORTLINK_HOSTS = ("tinyurl.com", "bit.ly")

PHONE_LINE = re.compile(r"Mobile\s*:|\+\d{2}\s*\d{6,}")
PAREN_EMAIL = re.compile(r"\(\s*([\w.+-]+@[\w-]+(?:\.[\w-]+)+)\s*\)")
SHORTLINK_LINE = re.compile(r"Documents\s*:|" + "|".join(re.escape(h) for h in SHORTLINK_HOSTS), re.I)

FORBIDDEN = [
    re.compile(r"\d{10}"),                       # any 10-digit run (phone)
    re.compile(r"\+91"),
    re.compile("|".join(re.escape(h) for h in SHORTLINK_HOSTS), re.I),
]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# Exact private strings (phone number, short-link ID, ...) to hunt for in the raw
# PDF objects, one per line. Kept in the git-ignored originals/ folder so they are
# never committed to this public repository.
TERMS_FILE = ROOT / "originals" / "redaction_terms.txt"
PRIVATE_TERMS = ([t.strip() for t in TERMS_FILE.read_text(encoding="utf-8").splitlines() if t.strip()]
                 if TERMS_FILE.exists() else [])


def lines_of(page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"])
            yield fitz.Rect(line["bbox"]), line["spans"], text


def shrink(rect):
    """Keep the redaction inside the line's own band so neighbours are untouched."""
    h = rect.height
    return fitz.Rect(rect.x0 - 0.5, rect.y0 + 0.2 * h, rect.x1 + 0.5, rect.y1 - 0.2 * h)


def redact(doc):
    for page in doc:
        for rect, spans, text in lines_of(page):
            # Whole line: the contact line (phone/e-mail) and the documents short-link.
            if PHONE_LINE.search(text) or SHORTLINK_LINE.search(text):
                page.add_redact_annot(shrink(rect), fill=False)
                continue
            # Only the "(address)" part of lines such as "Supervisor: Name (address)".
            for em in PAREN_EMAIL.finditer(text):
                for hit in page.search_for(em.group(0), clip=rect):
                    page.add_redact_annot(shrink(hit), fill=False)
            # Any other line that still carries an e-mail address goes entirely.
            if EMAIL.search(PAREN_EMAIL.sub("", text)):
                page.add_redact_annot(shrink(rect), fill=False)

        # Remove link annotations that point at private targets.
        for link in page.get_links():
            uri = (link.get("uri") or "").lower()
            if uri.startswith(("mailto:", "tel:")) or any(h in uri for h in SHORTLINK_HOSTS):
                page.delete_link(link)

        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=fitz.PDF_REDACT_LINE_ART_NONE,
        )

    # Metadata: keep only title and author, drop XMP packet.
    doc.del_xml_metadata()
    doc.set_metadata({"title": "Curriculum Vitae – Swatantra Dhara", "author": "Swatantra Dhara"})


def raw_objects(path):
    """Every PDF object, with streams decompressed, as text.

    Embedded font programs are binary glyph outlines (they cannot hold page
    text), so their streams are skipped; their dictionaries are still checked.
    """
    doc = fitz.open(path)
    font_programs = set()
    for xref in range(1, doc.xref_length()):
        obj = doc.xref_object(xref, compressed=False)
        for key in ("FontFile", "FontFile2", "FontFile3"):
            m = re.search(rf"/{key} (\d+) 0 R", obj)
            if m:
                font_programs.add(int(m.group(1)))
    for xref in range(1, doc.xref_length()):
        try:
            yield xref, doc.xref_object(xref, compressed=False)
            if doc.xref_is_stream(xref) and xref not in font_programs:
                yield xref, doc.xref_stream(xref).decode("latin-1", "replace")
        except Exception:
            continue


def verify(before_lines, path):
    problems = []
    fitz_text = "\n".join(p.get_text() for p in fitz.open(path))
    pypdf_text = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(path).pages)
    for name, text in (("PyMuPDF", fitz_text), ("pypdf", pypdf_text)):
        for pat in FORBIDDEN:
            for m in pat.finditer(text):
                problems.append(f"{name} text still contains {m.group(0)!r}")
        for m in EMAIL.finditer(text):
            problems.append(f"{name} text still contains e-mail {m.group(0)!r}")
    for xref, obj in raw_objects(path):
        for pat in FORBIDDEN[1:]:
            m = pat.search(obj)
            if m:
                ctx = obj[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                problems.append(f"raw object {xref} contains {pat.pattern!r}: ...{ctx}...")
        for m in EMAIL.finditer(obj):
            problems.append(f"raw object {xref} contains e-mail {m.group(0)!r}")
        for term in PRIVATE_TERMS:
            if term.lower() in obj.lower():
                problems.append(f"raw object {xref} contains a private term from {TERMS_FILE.name}")
    for name, text in (("PyMuPDF", fitz_text), ("pypdf", pypdf_text)):
        for term in PRIVATE_TERMS:
            if term.lower() in text.lower():
                problems.append(f"{name} text still contains a private term from {TERMS_FILE.name}")
    for page in fitz.open(path):
        for link in page.get_links():
            uri = (link.get("uri") or "").lower()
            if uri.startswith(("mailto:", "tel:")) or any(h in uri for h in SHORTLINK_HOSTS):
                problems.append(f"link annotation still present: {uri}")

    after = [t.strip() for p in fitz.open(path) for _, _, t in lines_of(p)]
    removed = [l for l in before_lines if l not in after]
    added = [l for l in after if l not in before_lines]
    return problems, removed, added, pypdf_text


def main():
    if not SRC.exists():
        sys.exit(f"Missing {SRC}")
    doc = fitz.open(SRC)
    before = [t.strip() for p in doc for _, _, t in lines_of(p)]
    redact(doc)
    doc.subset_fonts()
    DST.parent.mkdir(parents=True, exist_ok=True)
    doc.save(DST, garbage=4, deflate=True, clean=True)

    problems, removed, added, text = verify(before, DST)
    print("Changed lines (before -> after):")
    for l in removed:
        print("  -", l)
    for l in added:
        print("  +", l)
    if problems:
        print("\nREDACTION FAILED:")
        for p in problems:
            print("  !", p)
        DST.unlink()
        sys.exit(1)
    print(f"\nOK: {DST.relative_to(ROOT)} written; no phone number, e-mail address or short-link "
          f"found by PyMuPDF, pypdf or the raw-object scan.")


if __name__ == "__main__":
    main()

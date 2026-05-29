from __future__ import annotations

import io
import base64
import re
import tempfile
import textwrap
import zipfile
from pathlib import Path

import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from generate_dataset.convert_docs_to_txt import (
    ocr_image,
    ocr_pdf,
    read_html_text,
    read_pdf_text,
    read_docx_text,
    read_doc_text,
)
from philter import Philter


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_FILTERS = ROOT_DIR / "configs" / "philter_delta.json"
PERSISTENT_OUTPUT_DIR = ROOT_DIR / "data" / "redacted_out_pdf"


def ensure_unique_name(name: str, seen: dict[str, int]) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix or ".pdf"
    count = seen.get(name, 0)
    if count == 0:
        seen[name] = 1
        return name

    seen[name] = count + 1
    return f"{stem}_{count}{suffix}"


def write_text_to_pdf(text: str, output_pdf: Path) -> None:
    page_width, page_height = letter
    margin_left = 0.75 * inch
    margin_top = 0.75 * inch
    margin_bottom = 0.75 * inch
    line_height = 12
    wrap_width = 105

    pdf = canvas.Canvas(str(output_pdf), pagesize=letter)
    pdf.setFont("Courier", 10)

    y = page_height - margin_top
    for raw_line in text.splitlines():
        wrapped_lines = textwrap.wrap(raw_line, width=wrap_width) or [""]
        for line in wrapped_lines:
            if y <= margin_bottom:
                pdf.showPage()
                pdf.setFont("Courier", 10)
                y = page_height - margin_top
            pdf.drawString(margin_left, y, line)
            y -= line_height

    pdf.save()


def render_pdf_preview_pages(pdf_bytes: bytes, max_pages: int = 2) -> list[dict]:
    try:
        import fitz  # type: ignore
    except Exception as e:
        print(f"[DEBUG] fitz import failed: {e}")
        return []

    if not pdf_bytes:
        print(f"[DEBUG] pdf_bytes is empty")
        return []

    previews: list[dict] = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total = min(len(doc), max_pages)
        for page_index in range(total):
            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
            previews.append(
                {
                    "page": page_index + 1,
                    "png_bytes": pix.tobytes("png"),
                }
            )
        doc.close()
        print(f"[DEBUG] Generated {len(previews)} preview pages successfully")
    except Exception as e:
        print(f"[DEBUG] PDF preview rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return []

    return previews


def render_embedded_pdf(pdf_bytes: bytes, *, height: int = 700) -> None:
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    data_url = f"data:application/pdf;base64,{encoded}"
    # Render directly in Streamlit's page DOM to avoid iframe-in-iframe PDF plugin issues.
    st.markdown(
        f"""
        <object data=\"{data_url}\" type=\"application/pdf\" width=\"100%\" height=\"{height}\" style=\"border:1px solid #ddd; border-radius:6px;\">
            <embed src=\"{data_url}\" type=\"application/pdf\" width=\"100%\" height=\"{height}\" />
            <p>PDF preview is not supported in this browser view.</p>
        </object>
        """,
        unsafe_allow_html=True,
    )


def build_layout_preview_pdf(
    original_pdf_bytes: bytes,
    original_text: str,
    redacted_text: str,
) -> bytes | None:
    try:
        import fitz  # type: ignore
    except Exception as e:
        print(f"[DEBUG] fitz import failed in layout preview: {e}")
        return None

    if not original_pdf_bytes or not original_text or not redacted_text:
        print(f"[DEBUG] Missing input: pdf_bytes={bool(original_pdf_bytes)}, orig_text={bool(original_text)}, redacted_text={bool(redacted_text)}")
        return None

    max_len = min(len(original_text), len(redacted_text))
    starred_indices = {i for i in range(max_len) if redacted_text[i] == "*" and not original_text[i].isspace()}
    if not starred_indices:
        print(f"[DEBUG] No redacted regions found (no asterisks)")
        return None

    candidate_terms: set[str] = set()
    for match in re.finditer(r"\b[\w'-]{2,}\b", original_text):
        start, end = match.span()
        if any(idx in starred_indices for idx in range(start, end)):
            term = match.group(0).strip()
            if len(term) >= 2:
                candidate_terms.add(term)

    if not candidate_terms:
        print(f"[DEBUG] No candidate redaction terms found")
        return None

    terms_to_redact = sorted(candidate_terms, key=len, reverse=True)
    print(f"[DEBUG] Attempting to redact {len(terms_to_redact)} terms in layout preview")
    try:
        doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
        for page in doc:
            for term in terms_to_redact:
                for rect in page.search_for(term):
                    page.add_redact_annot(rect, fill=(0, 0, 0))
            page.apply_redactions()

        out_bytes = doc.tobytes()
        doc.close()
        print(f"[DEBUG] Layout preview PDF generated successfully ({len(out_bytes)} bytes)")
        return out_bytes
    except Exception as e:
        print(f"[DEBUG] Layout preview PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ── Body-aware redaction helpers ─────────────────────────────────────────────

# Section headings that mark the start of the narrative body in clinical notes.
BODY_SECTION_MARKERS = [
    r"^Clinical Note[s]?:",
    r"^Presenting Complaint[s]?:",
    r"^History of Present Illness:",
    r"^History:",
    r"^Assessment:",
    r"^Subjective:",
    r"^Chief Complaint:",
    r"^Progress Note:",
    r"^Consultation Note:",
    r"^Letter Body:",
]

# ── Body PHI patterns (HIPAA Safe Harbor + NHS/UK equivalents) ───────────────
# Each entry: (regex_pattern, replacement_text, re_flags)
# Patterns are applied in order; more-specific patterns come first.

_BODY_PHI_PATTERNS: list[tuple[str, str, int]] = [

    # ── PATIENT / CONTACT NAMES — run FIRST so labels are intact ─────────────
    # Expanded label list; uses [ \t]+ (not \s+) to avoid crossing line breaks.
    (
        r"(?:Patient(?:[ \t]+Name)?|Full[ \t]+Name|Name|Next[ \t]+of[ \t]+Kin|"
        r"Emergency[ \t]+Contact|Family[ \t]+Member|Relative|Carer|Guardian|"
        r"Referred[ \t]+by|Author|Dictated[ \t]+by|Signed[ \t]+by|"
        r"Consultant|Clinician|Attending|Nurse|Therapist|Physiotherapist|"
        r"Pharmacist|Surgeon|Registrar|GP|Key[ \t]+Worker|Keyworker|"
        r"Reviewed[ \t]+by|Seen[ \t]+by|Prepared[ \t]+by|Attended[ \t]+by)"
        r"[ \t]*:[ \t]+(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Mx\.?)?[ \t]*"
        r"([A-Z][^\W\d_]+(?:[ \t]+[A-Z][^\W\d_]+){1,2})",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Honorific + Name anywhere in text  e.g.  "Mr John Smith"  "Mrs Angela Hayes"
    (
        r"\b(?:Mr|Mrs|Ms|Miss|Mx)\.?\s+([A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Narrative "seen/reviewed/examined/referred by [Dr] Name"
    # (?i:...) makes only the trigger words case-insensitive; [A-Z][^\W\d_]+ is case-sensitive
    # so medication names starting with lowercase are NOT captured.
    (
        r"(?i:seen\s+by|reviewed\s+by|attended\s+by|referred\s+(?:to|by)|"
        r"examined\s+by|assessed\s+by|treated\s+by|presented\s+to|"
        r"admitted\s+under|under\s+(?:the\s+)?care\s+of|care\s+of)"
        r"\s+(?:Dr\.?\s+|Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+)?([A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # ── IDENTIFIERS ──────────────────────────────────────────────────────────

    # Email addresses
    (
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        0,
    ),
    # URLs  http/https/www
    (
        r"https?://[^\s\"'<>]+|www\.[^\s\"'<>]+",
        "[URL]",
        0,
    ),
    # IP addresses  IPv4
    (
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "[IP]",
        0,
    ),
    # US Social Security Number  XXX-XX-XXXX
    (
        r"\b\d{3}-\d{2}-\d{4}\b",
        "[SSN]",
        0,
    ),
    # NHS Number  841 229 7701  /  841-229-7701
    (
        r"\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b",
        "[NHS-NO]",
        0,
    ),
    # National Insurance (UK)  QQ 12 34 56 C
    (
        r"\b[A-Z]{2}\s*\d{2}\s*\d{2}\s*\d{2}\s*[A-D]\b",
        "[NI-NO]",
        0,
    ),
    # Medical / hospital record numbers — separator mandatory, PAT removed
    (
        r"\b(?:HSP|MRN|MR|REC|REF|ID)[\-:#]\s*[A-Z0-9]{4,12}\b",
        "[MED-ID]",
        0,
    ),
    # Insurance / member ID  labelled
    (
        r"(?i)(?:Insurance|Member|Policy|Plan|Group|Insurer)\s+(?:ID|No\.?|Number)[:\s]+[A-Z0-9\-]{4,20}",
        "[INS-ID]",
        0,
    ),
    # Account / billing numbers  labelled
    (
        r"(?i)(?:Account|Billing|Invoice|Claim|Auth(?:orisation)?)\s+(?:No\.?|Number|#)[:\s]+[A-Z0-9\-]{4,20}",
        "[ACCT-NO]",
        0,
    ),
    # Device serial numbers  e.g.  SN: ABC-123456
    (
        r"(?i)(?:Serial|Device|S/N|SN)[:\s#]+[A-Z0-9\-]{5,20}",
        "[SERIAL-NO]",
        0,
    ),
    # Vehicle licence plates (UK format)  AB12 CDE
    (
        r"\b[A-Z]{2}\d{2}\s?[A-Z]{3}\b|\b[A-Z]\d{3}\s?[A-Z]{3}\b",
        "[REG-PLATE]",
        0,
    ),
    # Dictation / transcription metadata lines
    (
        r"(?i)(?:Dictated|Transcribed|Signed|Authored)\s+(?:by|on)[:\s]+.+",
        "[DICTATION-META]",
        0,
    ),

    # ── PHONE / FAX ──────────────────────────────────────────────────────────
    # UK mobile / landline
    (
        r"(?:\+44\s?|0)(?:\d[\s\-]?){9,11}\b",
        "[PHONE]",
        0,
    ),
    # US phone  (XXX) XXX-XXXX
    (
        r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}\b",
        "[PHONE]",
        0,
    ),

    # ── DATES ────────────────────────────────────────────────────────────────
    # Written dates — day-first and month-first, with optional ordinal suffixes
    # e.g. 3 February 2024 / 19th June 2024 / Feb 21, 2024 / February 1st, 2024
    (
        r"(?i)\b\d{1,2}(?:st|nd|rd|th)?[\s\-]+(?:January|February|March|April|May|June|July|August"
        r"|September|October|November|December"
        r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{4}\b",
        "[DATE]",
        0,
    ),
    (
        r"(?i)\b(?:January|February|March|April|May|June|July|August"
        r"|September|October|November|December"
        r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}\b",
        "[DATE]",
        0,
    ),
    # DD/MM/YYYY  DD-MM-YYYY  DD.MM.YYYY
    (
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b",
        "[DATE]",
        0,
    ),
    # Age over 89
    (
        r"(?i)\b(?:aged?\s+)?(?:9[0-9]|1[0-9]{2})\s*[-\s]?(?:years?\s*[-\s]?old|y\.?o\.?|yr\.?s?)\b",
        "[AGE-OVER-89]",
        0,
    ),

    # ── ADDRESSES ────────────────────────────────────────────────────────────
    # Labelled address field
    (
        r"(?im)^(?:Address|Home\s+Address|Postal\s+Address|Correspondence\s+Address)\s*:\s*.+$",
        "[ADDRESS]",
        0,
    ),
    # "Flat N, Building Name"
    (
        r"(?i)\bFlat\s+\w+,\s+[A-Z][a-zA-Z\s]+(?:Apartments?|House|Building|Court|Mews|Towers?)\b",
        "[ADDRESS]",
        0,
    ),
    # Number + Street
    (
        r"(?i)\b\d+[A-Za-z]?\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3}"
        r"\s+(?:Street|Road|Avenue|Lane|Drive|Close|Way|Place|Court"
        r"|Gardens|Terrace|Crescent|Grove|Walk|Mews|Row|Square|Hill|Park|Flats?|Apartments?)\b",
        "[ADDRESS]",
        0,
    ),
    # Street-only line (no house number) in letter footers/signatures
    (
        r"(?im)^(?:[A-Z][^\n]{0,60})\b(?:Street|Road|Avenue|Lane|Drive|Close|Way|Place|Court"
        r"|Gardens|Terrace|Crescent|Grove|Walk|Mews|Row|Square|Hill|Park)\b\.?$",
        "[ADDRESS]",
        0,
    ),
    # Facility line used as part of postal address block
    (
        r"(?im)^(?:[A-Z][^\n]{0,80})\b(?:Hospital|Infirmary|Surgery|Practice|Clinic|Centre|Center|Trust|Unit)\b[^\n]*$",
        "[ADDRESS]",
        0,
    ),
    # UK postcode
    (
        r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b",
        "[POSTCODE]",
        0,
    ),
    # US ZIP
    (
        r"\b\d{5}(?:-\d{4})?\b",
        "[ZIP]",
        0,
    ),

    # ── PROVIDER / CLINIC / EMPLOYER NAMES (label+colon required) ────────────
    # Provider lines with initials + credentials  e.g. "Dr D Fine MD FRCP"
    (
        r"(?im)^\s*(?:Dr\.?|Doctor|Prof\.?|Professor)\s+(?:[A-Z]\.?\s+){1,3}[A-Z][^\W\d_]+"
        r"(?:\s+[A-Z][^\W\d_]+)?(?:\s+(?:MD|FRCP|MRCP|MBBS|MBChB|PhD|DPhil|BSc|MSc|RN|RGN|FRCPath|FACS))*\s*$",
        "[PROVIDER-NAME]",
        0,
    ),
    # Dr / Doctor / Prof names
    (
        r"\b(?:Dr\.?|Doctor|Prof\.?|Professor)\s+[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+)?\b",
        "[PROVIDER-NAME]",
        0,
    ),
    # GMC / NMC registration numbers
    (
        r"(?i)\bGMC\s*:?\s*\d{6,8}\b|\bNMC\s*:?\s*\d{6,8}[A-Z]?\b",
        "[REG-NO]",
        0,
    ),
    # Clinic / hospital — label+colon required
    (
        r"(?i)(?:Referred?\s+to|Clinic|Hospital|Practice|Centre|Center|Trust|Ward)\s*:\s*"
        r"[A-Z][a-zA-Z\s]{2,50}(?:Clinic|Hospital|Infirmary|Surgery|Practice|Centre|Center|Trust|Ward|Unit|NHS)\b",
        "[ORG-NAME]",
        0,
    ),
    # Employer — label+colon required
    (
        r"(?i)Employer\s*:\s*"
        r"[A-Z][a-zA-Z0-9\s\.,&\-]{2,50}(?:Ltd\.?|plc|Inc\.?|LLC|LLP|Co\.?|Corp\.?|Systems?|Services?|Solutions?|Group|Associates?)\b",
        "[EMPLOYER]",
        0,
    ),
    # School — label+colon required
    (
        r"(?i)(?:School|University|College|Academy|Institute)\s*:\s*"
        r"[A-Z][a-zA-Z\s]{2,50}(?:School|University|College|Academy|Institute)\b",
        "[SCHOOL]",
        0,
    ),

    # ── MISC ─────────────────────────────────────────────────────────────────
    # Standalone initials  J.M.H.
    (
        r"\b[A-Z]\.(?:[A-Z]\.){1,3}",
        "[INITIALS]",
        0,
    ),
    # Uppercase names that appear after salutation markers in letters
    (
        r"(?m)(?:\bDear[ \t]+\[PROVIDER-NAME\][ \t]+|\bcc[ \t]*:[ \t]*|\bRe[ \t]+)"
        r"([A-Z]{2,}(?:[ \t]+[A-Z]{2,}){1,2})\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),
    # Identifying occupations — label+colon required
    (
        r"(?i)(?:Occupation|Works?\s+as|Job|Profession)\s*:\s*"
        r"(?:local\s+mayor|mayor|MP|minister|NFL\s+player|Premier\s+League|celebrity|"
        r"CEO|headteacher|head\s+teacher|judge|bishop|chief\s+constable)[^\n]*",
        "[OCCUPATION-ID]",
        0,
    ),
]

def split_header_body(text: str, custom_marker: str = "") -> tuple[str, str, int]:
    """Return (header_text, body_text, split_index).

    The header is everything *before* the first recognised clinical section
    heading.  The body is that heading and everything after it.
    If no heading is found the entire text is treated as header (full philter
    redaction) and body is empty.
    """
    markers = list(BODY_SECTION_MARKERS)
    if custom_marker.strip():
        markers.insert(0, re.escape(custom_marker.strip()))

    for marker in markers:
        m = re.search(marker, text, re.MULTILINE | re.IGNORECASE)
        if m:
            idx = m.start()
            return text[:idx], text[idx:], idx

    return text, "", len(text)


def targeted_body_redact(text: str) -> str:
    """Apply HIPAA Safe Harbor + NHS targeted redaction to body text only.

    Redacts: names, initials, DOB, age >89, address, postcode/ZIP, phone/fax,
    email, SSN, NHS/NI numbers, medical record IDs, insurance/account/billing
    numbers, appointment/surgery dates, provider names, clinic/hospital names,
    employer/school names, emergency contact names, device serials,
    vehicle/licence plates, URLs, IP addresses, biometric labels,
    identifying occupations, dictation metadata.

    Everything else (clinical observations, medications, diagnoses, etc.)
    is left in its original format.
    """
    for pattern, replacement, flags in _BODY_PHI_PATTERNS:
        if callable(replacement):
            text = re.sub(pattern, replacement, text, flags=flags)
        else:
            text = re.sub(pattern, replacement, text, flags=flags)

    lines = text.splitlines()

    # Redact person name on next line after "cc:" in letter-style layouts.
    # Example:
    #   cc:
    #   Hazel Daniels
    cc_only = re.compile(r"(?i)^cc\s*:\s*$")
    name_line = re.compile(
        r"^[A-Z][^\W\d_]+(?:['-][A-Z][^\W\d_]+)?"
        r"(?:\s+[A-Z][^\W\d_]+(?:['-][A-Z][^\W\d_]+)?){1,2}$"
    )
    for i in range(len(lines) - 1):
        if cc_only.match(lines[i].strip()):
            # Skip one optional blank line between cc: and the recipient name.
            j = i + 1
            if j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                candidate = lines[j].strip()
                if candidate and candidate not in {"[NAME]", "[ADDRESS]", "[POSTCODE]", "[ZIP]"}:
                    if name_line.match(candidate):
                        lines[j] = "[NAME]"

    # Address block cleanup for letters: if an address/facility line is found,
    # also redact the immediately following city/town line when it is a short
    # title-cased phrase (e.g., "Southampton").
    address_like = re.compile(
        r"\b(?:Street|Road|Avenue|Lane|Drive|Close|Way|Place|Court|Gardens|Terrace|Crescent|"
        r"Grove|Walk|Mews|Row|Square|Hill|Park|Hospital|Infirmary|Surgery|Practice|Clinic|"
        r"Centre|Center|Trust|Unit|Address)\b",
        re.IGNORECASE,
    )
    city_line = re.compile(r"^[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2}$")

    for i in range(len(lines) - 1):
        current = lines[i].strip()
        nxt = lines[i + 1].strip()
        if not nxt or nxt in {"[ADDRESS]", "[POSTCODE]", "[ZIP]"}:
            continue

        if current in {"[ADDRESS]"} and city_line.match(nxt):
            lines[i + 1] = "[ADDRESS]"
            continue

        if current in {"[POSTCODE]", "[ZIP]", ""}:
            continue

        if address_like.search(current) and city_line.match(nxt):
            lines[i + 1] = "[ADDRESS]"

    # Inline address completion: if a line already has [ADDRESS] and [POSTCODE],
    # collapse any remaining city/county chunks between them into [ADDRESS].
    for i in range(len(lines)):
        line = lines[i]
        if "[ADDRESS]" in line and "[POSTCODE]" in line:
            line = re.sub(
                r"\[ADDRESS\](?:\s*,\s*[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2}){1,4}(?=\s*\.?\s*\[POSTCODE\])",
                "[ADDRESS]",
                line,
            )
        lines[i] = line

    text = "\n".join(lines)
    return text


def run_philter_body_aware(
    input_dir: Path,
    output_dir: Path,
    filters_path: Path,
    body_marker: str = "",
) -> None:
    """Two-pass redaction:
    1. Run full philter over every file (header gets full redaction).
    2. Locate the body section in the *original* text and replace the
       philter-redacted body with a targeted redaction (name / NHS ID /
       dates / Dr name / address / location only).
    """
    # Pass 1 – full philter redaction
    philter_config = {
        "verbose": False,
        "run_eval": False,
        "finpath": str(input_dir),
        "foutpath": str(output_dir),
        "outformat": "asterisk",
        "filters": str(filters_path),
        "cachepos": None,
    }
    filterer = Philter(philter_config)
    filterer.map_coordinates()
    filterer.transform()

    # Pass 2 – replace body portion with targeted output
    for orig_txt in sorted(input_dir.glob("*.txt")):
        redacted_file = output_dir / orig_txt.name
        if not redacted_file.exists():
            continue

        original_text = orig_txt.read_text(encoding="utf-8", errors="replace")
        redacted_text = redacted_file.read_text(encoding="utf-8", errors="replace")

        _header_orig, body_orig, split_pos = split_header_body(original_text, body_marker)
        if not body_orig:
            continue  # no body detected – keep full philter output

        header_redacted = redacted_text[:split_pos]
        body_targeted = targeted_body_redact(body_orig)
        redacted_file.write_text(header_redacted + body_targeted, encoding="utf-8")


# ── Standard (full) philter pipeline ─────────────────────────────────────────

def run_philter_on_folder(input_dir: Path, output_dir: Path, filters_path: Path) -> None:
    philter_config = {
        "verbose": False,
        "run_eval": False,
        "finpath": str(input_dir),
        "foutpath": str(output_dir),
        "outformat": "asterisk",
        "filters": str(filters_path),
        "cachepos": None,
    }

    filterer = Philter(philter_config)
    filterer.map_coordinates()
    filterer.transform()


# ── Targeted-only pipeline (whole document, no Philter) ──────────────────────

def run_targeted_only_on_folder(input_dir: Path, output_dir: Path) -> None:
    """Apply the targeted PHI regex patterns to the WHOLE document.

    Skips Philter entirely so medications, diagnoses, lab values and ordinary
    English words (confirmed, initially, engineer, etc.) are preserved.
    Only items matched by ``_BODY_PHI_PATTERNS`` are replaced with placeholders.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for src in input_dir.glob("*.txt"):
        original = src.read_text(encoding="utf-8")
        redacted = targeted_body_redact(original)
        (output_dir / src.name).write_text(redacted, encoding="utf-8")


def app() -> None:
    st.set_page_config(page_title="Philter Document Redactor", layout="wide")
    st.title("Philter Document Redactor")
    st.write("Upload PDF, DOC, DOCX, HTML, TXT, or image files, redact PHI, and download the output.")

    uploaded_files = st.file_uploader(
        "Upload documents (PDF, DOC, DOCX, HTML, JPEG, TXT)",
        type=["pdf", "doc", "docx", "html", "htm", "jpeg", "jpg", "txt"],
        accept_multiple_files=True,
    )

    use_ocr_fallback = st.checkbox(
        "Use OCR fallback if embedded PDF text is missing",
        value=True,
    )

    preview_pages = st.slider(
        "Preview pages per file",
        min_value=1,
        max_value=5,
        value=2,
        help="Shows side-by-side original and redacted page previews.",
    )

    custom_filter_path = st.text_input(
        "Filter config path",
        value=str(DEFAULT_FILTERS),
    )

    st.markdown("---")
    redaction_mode = st.radio(
        "Redaction mode",
        options=[
            "Full Philter (all PHI everywhere)",
            "Body-aware (full in header, targeted in body)",
            "Targeted only (whole document — preserves medications & common words)",
        ],
        index=2,
        help=(
            "**Full Philter** — original behaviour: redacts all PHI everywhere "
            "(may also redact common/clinical words).\n\n"
            "**Body-aware** — full Philter in the header (above 'Clinical Note:' etc.), "
            "targeted PHI-only in the body.\n\n"
            "**Targeted only (whole document)** — across the *entire* document only "
            "specific PHI patterns are redacted: names, initials, DOB, age >89, "
            "address, postcode/ZIP, phone, email, SSN, NHS/NI number, medical record ID, "
            "insurance/billing/account numbers, dates, provider names, clinic/hospital names, "
            "employer/school names, emergency contacts, device serials, vehicle plates, "
            "URLs, IP addresses, identifying occupations, dictation metadata.\n"
            "Medications, diagnoses, lab values, and everyday words (confirmed, initially, "
            "engineer, etc.) are left untouched."
        ),
    )
    body_targeted_mode = redaction_mode.startswith("Body-aware")
    targeted_only_mode = redaction_mode.startswith("Targeted only")

    body_marker_override = ""
    if body_targeted_mode:
        body_marker_override = st.text_input(
            "Body section starts after (optional override)",
            value="",
            placeholder="e.g.  Clinical Note:  — leave blank for auto-detection",
            help="Type the exact heading line where the narrative body begins. "
                 "Leave blank to use auto-detection.",
        )
        st.caption(
            "Header → full redaction (all PHI).  "
            "Body → redacts only: names, NHS ID, dates, Dr names, addresses, locations."
        )

    if "results" not in st.session_state:
        st.session_state["results"] = []
    if "failed" not in st.session_state:
        st.session_state["failed"] = []
    if "zip_bytes" not in st.session_state:
        st.session_state["zip_bytes"] = None

    if st.button("Redact Documents", type="primary"):
        if not uploaded_files:
            st.error("Please upload at least one document.")
            return

        filters_path = Path(custom_filter_path).expanduser().resolve()
        if not filters_path.exists():
            st.error(f"Filter config not found: {filters_path}")
            return

        st.session_state["results"] = []
        st.session_state["failed"] = []
        st.session_state["zip_bytes"] = None

        PERSISTENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="philter_gui_") as tmp_dir:
            tmp_root = Path(tmp_dir)
            input_pdf_dir = tmp_root / "input_pdf"
            ingested_txt_dir = tmp_root / "ingested_txt"
            redacted_txt_dir = tmp_root / "redacted_txt"

            input_pdf_dir.mkdir(parents=True, exist_ok=True)
            ingested_txt_dir.mkdir(parents=True, exist_ok=True)
            redacted_txt_dir.mkdir(parents=True, exist_ok=True)

            seen_names: dict[str, int] = {}
            txt_name_to_original_pdf: dict[str, str] = {}
            txt_name_to_original_pdf_bytes: dict[str, bytes] = {}
            txt_name_to_original_text: dict[str, str] = {}

            for upload in uploaded_files:
                safe_name = ensure_unique_name(upload.name, seen_names)
                pdf_path = input_pdf_dir / safe_name
                upload_bytes = upload.getvalue()
                pdf_path.write_bytes(upload_bytes)

                text = ""
                status = ""
                file_ext = Path(safe_name).suffix.lower()

                if file_ext == ".pdf":
                    text, status = read_pdf_text(pdf_path)
                    if (not text) and use_ocr_fallback:
                        text, status = ocr_pdf(pdf_path)
                elif file_ext == ".docx":
                    text, status = read_docx_text(pdf_path)
                elif file_ext == ".doc":
                    text, status = read_doc_text(pdf_path)
                elif file_ext == ".txt":
                    try:
                        text = pdf_path.read_text(encoding="utf-8", errors="replace").strip()
                        status = "ok" if text else "empty"
                    except Exception as exc:
                        text, status = "", f"txt read error: {exc}"
                elif file_ext in [".html", ".htm"]:
                    text, status = read_html_text(pdf_path)
                elif file_ext in [".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif"]:
                    text, status = ocr_image(pdf_path)
                else:
                    text, status = "", f"unsupported file type: {file_ext}"

                if not text:
                    st.session_state["failed"].append(
                        {
                            "file": safe_name,
                            "reason": f"Text extraction failed ({status})",
                        }
                    )
                    continue

                txt_name = f"{Path(safe_name).stem}.txt"
                txt_path = ingested_txt_dir / txt_name
                txt_path.write_text(text + "\n", encoding="utf-8")
                txt_name_to_original_pdf[txt_name] = safe_name
                txt_name_to_original_pdf_bytes[txt_name] = upload_bytes
                txt_name_to_original_text[txt_name] = text

            if any(ingested_txt_dir.glob("*.txt")):
                try:
                    if targeted_only_mode:
                        run_targeted_only_on_folder(ingested_txt_dir, redacted_txt_dir)
                    elif body_targeted_mode:
                        run_philter_body_aware(
                            ingested_txt_dir,
                            redacted_txt_dir,
                            filters_path,
                            body_marker=body_marker_override,
                        )
                    else:
                        run_philter_on_folder(ingested_txt_dir, redacted_txt_dir, filters_path)
                except Exception as exc:
                    st.error(f"Philter redaction failed: {exc}")
                    return
            else:
                st.error("No files were successfully extracted to text — no redaction was run.")
                for f in st.session_state["failed"]:
                    st.warning(f"\u274c {f['file']}: {f['reason']}")
                return

            for redacted_txt_file in sorted(redacted_txt_dir.glob("*.txt")):
                redacted_text = redacted_txt_file.read_text(encoding="utf-8", errors="replace")
                original_pdf_name = txt_name_to_original_pdf.get(
                    redacted_txt_file.name,
                    f"{redacted_txt_file.stem}.pdf",
                )
                redacted_pdf_name = f"{Path(original_pdf_name).stem}_redacted.pdf"
                disk_pdf_path = PERSISTENT_OUTPUT_DIR / redacted_pdf_name
                original_pdf_bytes = txt_name_to_original_pdf_bytes.get(redacted_txt_file.name, b"")
                original_text = txt_name_to_original_text.get(redacted_txt_file.name, "")
                write_text_to_pdf(redacted_text, disk_pdf_path)
                pdf_bytes = disk_pdf_path.read_bytes()
                layout_preview_pdf_bytes = build_layout_preview_pdf(
                    original_pdf_bytes=original_pdf_bytes,
                    original_text=original_text,
                    redacted_text=redacted_text,
                )

                original_previews = render_pdf_preview_pages(original_pdf_bytes, max_pages=preview_pages) if original_pdf_bytes else []
                redacted_previews = render_pdf_preview_pages(pdf_bytes, max_pages=preview_pages)

                st.info(
                    f"Debug for `{original_pdf_name}`: "
                    f"original_pdf_bytes={len(original_pdf_bytes)}, "
                    f"redacted_pdf_bytes={len(pdf_bytes)}, "
                    f"original_previews={len(original_previews)}, "
                    f"redacted_previews={len(redacted_previews)}"
                )

                st.session_state["results"].append(
                    {
                        "source_pdf": original_pdf_name,
                        "original_pdf_bytes": original_pdf_bytes,
                        "redacted_pdf_name": redacted_pdf_name,
                        "pdf_bytes": pdf_bytes,
                        "layout_preview_pdf_bytes": layout_preview_pdf_bytes,
                        "saved_path": str(disk_pdf_path),
                        "original_page_previews": original_previews,
                        "redacted_page_previews": redacted_previews,
                    }
                )

            if st.session_state["results"]:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for result in st.session_state["results"]:
                        zipf.writestr(result["redacted_pdf_name"], result["pdf_bytes"])
                st.session_state["zip_bytes"] = zip_buffer.getvalue()

    if st.session_state["results"]:
        st.success(f"Generated {len(st.session_state['results'])} redacted PDF file(s).")
        st.caption(f"Saved PDF output folder: {PERSISTENT_OUTPUT_DIR}")

        if st.session_state["zip_bytes"]:
            st.download_button(
                "Download all redacted PDFs (zip)",
                data=st.session_state["zip_bytes"],
                file_name="redacted_pdfs.zip",
                mime="application/zip",
            )

        st.subheader("Outputs")
        for result in st.session_state["results"]:
            st.markdown(f"**Source:** {result['source_pdf']}")
            st.caption(f"Saved file: {result['saved_path']}")
            st.download_button(
                label=f"Download {result['redacted_pdf_name']}",
                data=result["pdf_bytes"],
                file_name=result["redacted_pdf_name"],
                mime="application/pdf",
            )

            with st.expander("Show document preview (original vs redacted)"):
                original_previews = result.get("original_page_previews", [])
                redacted_previews = result.get("redacted_page_previews", [])
                row_count = max(len(original_previews), len(redacted_previews))

                if row_count == 0:
                    st.caption("Preview unavailable for this file.")
                else:
                    for i in range(row_count):
                        left_col, right_col = st.columns(2)
                        orig = original_previews[i] if i < len(original_previews) else None
                        red = redacted_previews[i] if i < len(redacted_previews) else None

                        if orig:
                            left_col.markdown(f"**Original page {orig['page']}**")
                            left_col.image(orig["png_bytes"], use_container_width=True)
                        else:
                            left_col.caption("No original preview")

                        if red:
                            right_col.markdown(f"**Redacted page {red['page']}**")
                            right_col.image(red["png_bytes"], use_container_width=True)
                        else:
                            right_col.caption("No redacted preview")

            with st.expander("Show redacted PDF"):
                render_embedded_pdf(result["pdf_bytes"])

            with st.expander("Show embedded PDFs (original vs redacted vs layout-preserving preview)"):
                left_col, mid_col, right_col = st.columns(3)

                with left_col:
                    st.markdown("**Original PDF**")
                    original_pdf_bytes = result.get("original_pdf_bytes", b"")
                    if original_pdf_bytes:
                        render_embedded_pdf(original_pdf_bytes)
                    else:
                        st.caption("Original PDF is unavailable for this file.")

                with mid_col:
                    st.markdown("**Redacted PDF**")
                    render_embedded_pdf(result["pdf_bytes"])

                with right_col:
                    st.markdown("**Layout-Preserving Redacted Preview**")
                    layout_preview_pdf_bytes = result.get("layout_preview_pdf_bytes")
                    if layout_preview_pdf_bytes:
                        render_embedded_pdf(layout_preview_pdf_bytes)
                    else:
                        st.caption("Preview unavailable for this file.")

    if st.session_state["failed"]:
        st.warning("Some files could not be processed.")
        for failed in st.session_state["failed"]:
            st.write(f"- {failed['file']}: {failed['reason']}")


if __name__ == "__main__":
    app()

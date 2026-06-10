from __future__ import annotations

import io
import base64
import importlib.util
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
PERSISTENT_TXT_OUTPUT_DIR = ROOT_DIR / "data" / "redacted_out"
_PTEREDACTYL_ANALYSER = None
_PTEREDACTYL_REGEX_ANALYSER = None


def has_pteredactyl() -> bool:
    return importlib.util.find_spec("pteredactyl") is not None


def apply_pteredactyl_redaction(text: str) -> str:
    """Apply full pteredactyl entities, then fall back to regex-only if needed."""
    global _PTEREDACTYL_ANALYSER
    global _PTEREDACTYL_REGEX_ANALYSER

<<<<<<< HEAD
=======
    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

    # Disable SSL verification for Hugging Face downloads (corporate network)
    import os
    os.environ["HF_HUB_DISABLE_SSL"] = "1"
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["CURL_CA_BUNDLE"] = ""

>>>>>>> 32d52ad (new branch)
    try:
        import pteredactyl as pt  # type: ignore
    except Exception:
        return text

    try:
        if _PTEREDACTYL_ANALYSER is None:
            _PTEREDACTYL_ANALYSER = pt.create_analyser(
                regex_entities=pt.DEFAULT_REGEX_ENTITIES,
            )

        # Full entity pass (PERSON, LOCATION, ORGANIZATION, etc.) + regex entities.
        redacted = pt.anonymise(
            text,
            analyser=_PTEREDACTYL_ANALYSER,
            entities=pt.DEFAULT_ENTITIES,
            regex_entities=pt.DEFAULT_REGEX_ENTITIES,
            rebuild_regex_recognisers=False,
        )

    except Exception as full_error:
        print(f"[DEBUG] pteredactyl full-entity pass failed, falling back to regex-only: {full_error}")
        try:
            if _PTEREDACTYL_REGEX_ANALYSER is None:
                _PTEREDACTYL_REGEX_ANALYSER = pt.create_analyser(
                    regex_entities=pt.DEFAULT_REGEX_ENTITIES,
                )

            redacted = pt.anonymise(
                text,
                analyser=_PTEREDACTYL_REGEX_ANALYSER,
                entities=[],
                regex_entities=pt.DEFAULT_REGEX_ENTITIES,
                rebuild_regex_recognisers=False,
            )
        except Exception as regex_error:
            print(f"[DEBUG] pteredactyl redaction skipped due to error: {regex_error}")
            return text

    try:
        # Regex entities
        redacted = redacted.replace("<EMAIL_ADDRESS>", "[EMAIL]")
        redacted = redacted.replace("<POSTCODE>", "[POSTCODE]")
        redacted = redacted.replace("<NHS_NUMBER>", "[NHS-NO]")

        # NER entities
        redacted = redacted.replace("<PERSON>", "[NAME]")
        redacted = redacted.replace("<LOCATION>", "[ADDRESS]")
        redacted = redacted.replace("<ORGANIZATION>", "[ORG-NAME]")
        redacted = redacted.replace("<AGE>", "[AGE]")
        redacted = redacted.replace("<PHONE_NUMBER>", "[PHONE]")
        redacted = redacted.replace("<DATE_TIME>", "[DATE]")
        redacted = redacted.replace("<DEVICE>", "[SERIAL-NO]")
        redacted = redacted.replace("<ZIP>", "[ZIP]")
        redacted = redacted.replace("<PROFESSION>", "[OCCUPATION-ID]")
        redacted = redacted.replace("<USERNAME>", "[USERNAME]")
        redacted = redacted.replace("<ID>", "[MED-ID]")

        return redacted
    except Exception as e:
        print(f"[DEBUG] pteredactyl token mapping failed: {e}")
        return text
<<<<<<< HEAD
=======
        redacted = redacted.replace("<PERSON>", "[NAME]")
        redacted = redacted.replace("<LOCATION>", "[ADDRESS]")
        redacted = redacted.replace("<ORGANIZATION>", "[ORG-NAME]")
        redacted = redacted.replace("<AGE>", "[AGE]")
        redacted = redacted.replace("<PHONE_NUMBER>", "[PHONE]")
        redacted = redacted.replace("<DATE_TIME>", "[DATE]")
        redacted = redacted.replace("<DEVICE>", "[SERIAL-NO]")
        redacted = redacted.replace("<ZIP>", "[ZIP]")
        redacted = redacted.replace("<PROFESSION>", "[OCCUPATION-ID]")
        redacted = redacted.replace("<USERNAME>", "[USERNAME]")
        redacted = redacted.replace("<ID>", "[MED-ID]")

        return redacted
    except Exception as e:
        print(f"[DEBUG] pteredactyl token mapping failed: {e}")
        return text
>>>>>>> 32d52ad (new branch)


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
    # Capture stops at: 2+ spaces (column gap), the next "Word:" label on the same line,
    # or end-of-line. Inter-word spacing inside a name is restricted to a single space
    # so wide column gaps cannot pull the next label into the name.
    (
        r"(?:Patient(?:[ \t]+Name)?|Full[ \t]+Name|Name|Next[ \t]+of[ \t]+Kin|"
        r"Emergency[ \t]+Contact|Family[ \t]+Member|Relative|Carer|Guardian|"
        r"Referred[ \t]+by|Author|Dictated[ \t]+by|Signed[ \t]+by|"
        r"Consultant|Clinician|Attending|Nurse|Therapist|Physiotherapist|"
        r"Pharmacist|Surgeon|Registrar|GP|Requester|Key[ \t]+Worker|Keyworker|"
        r"Reviewed[ \t]+by|Seen[ \t]+by|Prepared[ \t]+by|Attended[ \t]+by|"
        r"Clinical[ \t]+Lead|Lead[ \t]+Clinician|Lead[ \t]+Nurse|Lead[ \t]+Consultant|"
        r"Named[ \t]+Nurse|Named[ \t]+Doctor|Key[ \t]+Clinician|Responsible[ \t]+Clinician|"
        r"Responsible[ \t]+Consultant|Allocated[ \t]+Nurse|Care[ \t]+Coordinator|"
        r"Keyworker|Key[ \t]+Worker|Dietitian|Dietician|Social[ \t]+Worker|"
        r"Occupational[ \t]+Therapist|Speech[ \t]+Therapist|Podiatrist|Radiologist|"
        r"Anaesthetist|Anesthesiologist|Oncologist|Cardiologist|Neurologist)"
        r"[ \t]*:[ \t]+(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Mx\.?)?[ \t]*"
        r"((?:[A-Z][A-Za-z'\-]*(?:(?:,[ \t]*[A-Z]\.?)|(?:,[ \t]*[A-Z][A-Za-z'\-]+(?:[ \t]+[A-Z][A-Za-z'\-]+){0,2}))?(?:[ \t]+\([A-Z]+\))?"
        r"|[A-Z]\.?[A-Za-z'\-]*)(?:[ \t][A-Z]\.?[A-Za-z'\-]*){0,3})"
        r"(?=[ \t]{2,}|[ \t]+[A-Z][A-Za-z'\-]*[ \t]*:|[ \t]*$|[\r\n])",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        re.MULTILINE,
    ),

    # Columnar name fields — NO colon, label separated from value by 2+ spaces/tabs
    # e.g. "Name   Konstantopoulos Aqk Adult"  (header table format)
    (
        r"(?:Patient(?:[ \t]+Name)?|Full[ \t]+Name|Name|Clinical[ \t]+Lead|"
        r"Lead[ \t]+Clinician|Consultant|Registrar|Dietitian|Social[ \t]+Worker)"
        r"[ \t]{2,}(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Mx\.?)?[ \t]*"
        r"((?:[A-Z][A-Za-z'\-]+)(?:[ \t][A-Z][A-Za-z'\-]+){0,4})"
        r"(?=[ \t]{2,}|[ \t]*$|[\r\n])",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        re.MULTILINE,
    ),

    # Label on one line, name on the next line (common in table-style referral forms)
    # e.g. "Clinical Lead:\nFAZLEEN, AISHATH (DR)" / "Requester:\nMonsuru-Oke, Mosunmoluwa"
    (
        r"(?im)^(\s*(?:Clinical\s+Lead|Requester|Consultant(?:\s*&\s*specialty)?|"
        r"Responsible\s+Consultant|Referring\s+team(?:\s+and\s+bleep\s+number)?)\s*:\s*)\r?\n(\s*)"
        r"([A-Z][A-Za-z'\-]+(?:,\s*[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})?"
        r"(?:\s+\([A-Z]+\))?)\s*$",
        lambda m: m.group(1) + "\n" + m.group(2) + "[NAME]",
        0,
    ),

    # Name appearing immediately after a [MED-ID] token on the same line
    # e.g. "Patient [MED-ID]:   Felwick"  or  "Dietitian's Patient [MED-ID]:   Vasso K."
    (
        r"(?i)(?:\[MED-ID\][ \t]*:?[ \t]+)((?:[A-Z][A-Za-z'\-]+)(?:[ \t]+[A-Z]\.?)?(?:[ \t][A-Z][A-Za-z'\-]+){0,2})",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Contact No / Contact Bleep label + name (e.g. "Contact No:   Vasso K.")
    (
        r"(?i)(?:Contact[ \t]+(?:No\.?|Name|Person)[ \t]*:[ \t]+)((?:[A-Z][A-Za-z'\-]+)(?:[ \t]+[A-Z]\.?)?(?:[ \t][A-Z][A-Za-z'\-]+){0,2})",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Standalone "by [Name]" pattern (e.g. "[MED-ID] by EMMA WHITEHEAD", "Completed by Dr Smith")
    (
        r"\bby\s+(?:Dr\.?\s+|Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+)?([A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})\b",
        lambda m: m.group(0).replace(m.group(1), "[PROVIDER-NAME]"),
        0,
    ),

    # Honorific + Name anywhere in text  e.g.  "Mr John Smith"  "MR MALCOLM MAIR"
    (
        r"(?i)\b(?:Mr|Mrs|Ms|Miss|Mx)\.?\s+((?:(?:[A-Za-z]\.?(?:\s+|$)){1,3}[A-Za-z][^\W\d_]+)|(?:[A-Za-z][^\W\d_]+(?:\s+[A-Za-z][^\W\d_]+){0,2}))\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        re.IGNORECASE,
    ),

    # Nurse / Sister title + name
    (
        r"\b(?:Sister|Senior\s+Sister|Nurse|Staff\s+Nurse|Charge\s+Nurse|Matron)\s+"
        r"((?:(?:[A-Z]\.?(?:\s+|$)){1,3}[A-Z][A-Za-z'\-]+)|(?:[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})|(?:[A-Z][^\W\d_]*\s+[A-Z]\.?(?:\s+[A-Z][A-Za-z'\-]+)+))\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Names on the line after common labels
    (
        r"(?im)^((?:Seen\s+By|Reviewed\s+By|Prepared\s+By|Responsible\s+Consultant|"
        r"Consultant(?:\s+Surgeons?)?|Nurse|Sister)\s*)\r?\n(\s*)"
        r"((?:(?:[A-Z]\.?(?:\s+|$)){1,4}[A-Z][A-Z'\-]+)|(?:[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,3})|(?:[A-Z][^\W\d_]*\s+[A-Z]\.?(?:\s+[A-Z][A-Z'\-]+)+))\s*$",
        lambda m: m.group(1) + "\n" + m.group(2) + "[NAME]",
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

    # Names followed by commas and roles (e.g. "contact details of Mick Cullen and Claire Barnes, our paediatric gastroenterology specialist nurses")
    (
        r"(?i:contact\s+details?\s+of|staff\s+(?:members?|team)?|team\s+members?)\s+"
        r"((?:[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})(?:\s+and\s+[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,2})*)"
        r"(?:\s*,\s*(?:our|the|a)\s+[a-z\s]+(?:nurse|doctor|therapist|specialist|clinician|consultant|staff))\b",
        lambda m: m.group(0).replace(m.group(1), "[NAME]"),
        0,
    ),

    # Standalone first-name mentions in narrative clinical prose
    # e.g. "Alice has...", "Alice was...", "Alice will..."
    (
        r"\b([A-Z][a-z]{2,})\b(?=\s+(?:has|had|have|was|were|is|are|will|would|can|could|"
        r"did|does|reports?|reported|states?|stated|presented|attended|reviewed|"
        r"informed|noted|advised|complains?|denies|continues|remains|improved|"
        r"deteriorated|struggling|scheduled|requested|discussed|seen|"
        r"came|comes|coming|arrived|arrives|saw|sees|seeing|told|tells|telling|"
        r"feels|felt|appears?|appeared|looks?|looked|seems?|seemed|"
        r"explained|explains|mentioned|mentions|describes|described|"
        r"asked|asks|wanted|wants|needs|needed|underwent|undergoes|"
        r"started|starts|stopped|stops|received|receives|takes|took|taking|"
        r"agreed|agrees|declined|declines|brought|brings))",
        lambda m: "[NAME]" if m.group(1).lower() not in {
            "he", "she", "him", "his", "her", "hers", "they", "them", "their", "theirs",
            "january", "february", "march", "april", "may", "june", "july", "august",
            "september", "october", "november", "december", "monday", "tuesday",
            "wednesday", "thursday", "friday", "saturday", "sunday"
        } else m.group(1),
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
    # Hospital / patient / ward number label on same line as value
    # e.g. "Hospital No: 0096218"  "Hospital Number: 0556486"  "Patient Num 12345"
    (
        r"(?i)\b(?:Hospital|Patient|Inpatient|Outpatient|Ward|Admission|Episode|Case|Encounter)\s+"
        r"(?:No\.?|Number|Num\.?)(?:\s+No\.?)?\s*[:\-]?\s*([A-Z0-9]{4,12})\b",
        lambda m: m.group(0).replace(m.group(1), "[MED-ID]"),
        0,
    ),
    # Patient identifier embedded in prose/reference lines
    (
        r"(?i)(\bpatient\s+)([A-Z0-9]{4,12})\b",
        lambda m: m.group(1) + "[MED-ID]",
        0,
    ),
    # Our Ref lines that repeat a local identifier after a slash
    (
        r"(?i)(\bOur\s+Ref\s*:[^\n]{0,120}?/\s*)([A-Z0-9]{4,12})\b",
        lambda m: m.group(1) + "[MED-ID]",
        0,
    ),
    # Hospital / patient number label on one line, value on the next line
    # e.g. "Hospital Number\n0556486"
    (
        r"(?im)^((?:Hospital|Patient|Inpatient|Outpatient|Ward|Admission|Episode|Case|Encounter)\s+"
        r"(?:No\.?|Number|Num\.?)(?:\s+No\.?)?\s*)\n(\s*)([A-Z0-9]{4,12})\s*$",
        lambda m: m.group(1) + "\n" + m.group(2) + "[MED-ID]",
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
    # Contact Bleep / Pager — 4- or 5-digit internal extension after label
    (
        r"(?i)(?:Contact\s+)?Bleep\s*:?\s*(\d{3,5})\b",
        lambda m: m.group(0).replace(m.group(1), "[BLEEP]"),
        0,
    ),
    # Contact No / Ext / Extension — short numeric after label
    (
        r"(?i)(?:Contact\s+No|Ext(?:ension)?|Extn|Internal\s+No)\.?\s*:?\s*(\d{3,6})\b",
        lambda m: m.group(0).replace(m.group(1), "[PHONE]"),
        0,
    ),
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
        r"(?i)\b\d+[A-Za-z]?\s+[A-Z][a-zA-Z.']+(?:\s+[A-Z][a-zA-Z.']+){0,3}"
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
    # PO Box postal lines
    (
        r"(?im)^\s*(?:P\.?\s*O\.?\s*Box|PO\s*Box)\s*[A-Z0-9\-/ ]{1,20}(?:,?\s+[A-Z][^\n]{0,60})?$",
        "[ADDRESS]",
        0,
    ),
    # Facility line used as part of a postal address block.
    # Keep this conservative so narrative doctor-note lines are not removed.
    (
        r"(?im)^(?=.{3,90}$)(?!.*\b(?:i|we|he|she|they|patient|reviewed|diagnosed|presented|"
        r"complains?|reported|noted|today|yesterday|history|assessment|plan)\b)"
        r"(?:[A-Z][a-zA-Z&'.\-]+(?:\s+[A-Z][a-zA-Z&'.\-]+){0,7}\s+"
        r"(?:Hospital|Infirmary|Surgery|Practice|Clinic|Centre|Center|Trust|Unit)"
        r"(?:\s+[A-Z][a-zA-Z&'.\-]+){0,4})$",
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
        r"\b(?:Dr\.?|Doctor|Prof\.?|Professor)\s+"
        r"(?:(?:[A-Z]\.?(?:\s+|$)){1,4}[A-Z][^\W\d_]+|[A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+)?)\b",
        "[PROVIDER-NAME]",
        0,
    ),
    # Uppercase provider style used in summaries, e.g. "DR T HOLLINGWORTH"
    (
        r"(?i)\b(?:DR|DOCTOR|PROF|PROFESSOR)\.?\s+"
        r"((?:[A-Z]\.?(?:\s+|$)){1,3}[A-Z][A-Z'\-]+(?:\s+[A-Z][A-Z'\-]+){0,2})\b",
        lambda m: m.group(0).replace(m.group(1), "[PROVIDER-NAME]"),
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
    # Standalone organization line commonly used in letter headers/addresses
    (
        r"(?im)^\s*(?:The\s+)?[A-Z][a-zA-Z&'.\-]+(?:\s+[A-Z][a-zA-Z&'.\-]+){0,6}\s+"
        r"(?:Group|Practice|Clinic|Hospital|Infirmary|Centre|Center|Trust|Unit)\s*$",
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
    # Sign-off name lines after valedictions (common in letters)
    (
        r"(?im)^(Yours\s+sincerely)\s*\r?\n([A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,3})\s*$",
        lambda m: f"{m.group(1)}\n[NAME]",
        0,
    ),
    (
        r"(?im)^(Kind\s+regards)\s*\r?\n([A-Z][^\W\d_]+(?:\s+[A-Z][^\W\d_]+){0,3})\s*$",
        lambda m: f"{m.group(1)}\n[NAME]",
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


def targeted_body_redact(text: str, *, use_pteredactyl_rules: bool = False) -> str:
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
    # Normalize OCR-exported non-breaking spaces so [ \t]-based regexes match reliably.
    text = text.replace("\u00A0", " ")

    # Track redactions: original_word -> redaction_token
    redacted_words: dict[str, str] = {}

    # Pre-scan: extract bare names that appear with Dr/Prof titles so that
    # inline occurrences without any title are caught in the post-pass sweep.
    _titled_name_re = re.compile(
        r"\b(?:Dr\.?|Doctor|Prof\.?|Professor)\s+"
        r"((?:[A-Z][a-z][a-zA-Z'\-]*\s+){0,2}[A-Z][a-z][a-zA-Z'\-]*)",
    )
    for _m in _titled_name_re.finditer(text):
        bare = _m.group(1).strip().rstrip(".")
        if bare:
            redacted_words[bare] = "[PROVIDER-NAME]"

    for pattern, replacement, flags in _BODY_PHI_PATTERNS:
        if callable(replacement):
            # Wrap the lambda to capture what was replaced
            def make_wrapper(orig_replacement, orig_pattern):
                def wrapper(m):
                    result = orig_replacement(m)
                    # If the replacement is a bracket token, try to extract the original word
                    if isinstance(result, str) and "[" in result and "]" in result:
                        # Common patterns: [NAME], [PROVIDER-NAME], [MED-ID], etc.
                        original_text = m.group(0)
                        # Try to extract names from the original match
                        for group_idx in range(1, len(m.groups()) + 1):
                            try:
                                captured = m.group(group_idx)
                                if captured and isinstance(captured, str):
                                    # Store the mapping if this looks like a name or ID
                                    if re.search(r"[A-Z][a-z]+|[A-Z0-9]{4,12}", captured):
                                        redacted_words[captured] = result
                            except:
                                pass
                    return result
                return wrapper

            text = re.sub(pattern, make_wrapper(replacement, pattern), text, flags=flags)
        else:
            text = re.sub(pattern, replacement, text, flags=flags)

    lines = text.splitlines()

    # Redact recipient block after "cc:", "Copy to:", "Copies to:", "Distribution:" etc.
    # Example:
    #   Copy to:
    #   Catherine Foley
    #   Specialist Dietitian
    #   Minerva House
    cc_header = re.compile(
        r"(?i)^(?:cc|c\.c\.?|copy\s+to|copies\s+to|copied\s+to|distribution|"
        r"recipients?)\s*:\s*$"
    )
    name_line = re.compile(
        r"^[A-Z][^\W\d_]+(?:['-][A-Z][^\W\d_]+)?"
        r"(?:\s+[A-Z][^\W\d_]+(?:['-][A-Z][^\W\d_]+)?){1,2}$"
    )
    role_line = re.compile(
        r"(?i)^(?:(?:[A-Z][a-zA-Z]+\s+){0,2})?(?:Dietitian|Nurse|Doctor|Consultant|Registrar|"
        r"Surgeon|Therapist|Physiotherapist|Pharmacist|Psychologist|Psychiatrist|"
        r"Specialist|Practitioner|GP|Manager|Coordinator|Secretary|Officer|"
        r"Sister|Matron|Midwife|Radiographer|Sonographer|Anaesthetist|"
        r"Counsellor|Counselor|Optometrist|Podiatrist|Dentist|"
        r"Social\s+Worker|Health\s+Visitor|Care\s+Worker|Support\s+Worker)"
        r"(?:\s+[A-Z][a-zA-Z]+){0,3}(?:\s+(?:in|of)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,4})?$"
    )
    address_block_line = re.compile(
        r"(?i)^(?:[\/\#,\-]?\s*)?(?:\d+[A-Za-z]?\s+)?"
        r"[A-Z0-9][A-Za-z0-9'.,&()\-/\s]{0,80}"
        r"(?:Street|St\.?|Road|Rd\.?|Avenue|Ave\.?|Lane|Ln\.?|Drive|Dr\.?|Close|Way|"
        r"Place|Court|Gardens|Terrace|Crescent|Grove|Walk|Mews|Row|Square|Hill|Park|"
        r"House|Building|Centre|Center|Clinic|Hospital|Infirmary|Surgery|Practice|Unit)\b.*$"
    )
    postal_org_line = re.compile(
        r"(?i)^(?:Directorate|Department|Division|Service|Team|Care\s+Group|"
        r"Medical\s+Team|Clinical\s+Team|Specialty|Speciality)\b.{0,90}$"
    )
    mailpoint_line = re.compile(r"(?i)^Mailpoint\b.{0,40}$")
    postcode_only_line = re.compile(r"(?i)^\s*[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\s*$")
    for i in range(len(lines)):
        if cc_header.match(lines[i].strip()):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            block_count = 0
            while j < len(lines) and lines[j].strip() and block_count < 8:
                candidate = lines[j].strip()
                if candidate in {"[NAME]", "[ADDRESS]", "[POSTCODE]", "[ZIP]",
                                 "[PROVIDER-NAME]", "[ORG-NAME]"}:
                    j += 1
                    block_count += 1
                    continue
                if address_block_line.match(candidate) or postal_org_line.match(candidate) or mailpoint_line.match(candidate):
                    lines[j] = "[ADDRESS]"
                elif role_line.match(candidate):
                    lines[j] = "[PROVIDER-NAME]"
                elif postcode_only_line.match(candidate):
                    lines[j] = "[POSTCODE]"
                elif name_line.match(candidate):
                    prev_token = lines[j - 1].strip() if j - 1 >= 0 else ""
                    if prev_token in {"[ADDRESS]", "[POSTCODE]", "[ZIP]"}:
                        lines[j] = "[ADDRESS]"
                    else:
                        lines[j] = "[NAME]"
                j += 1
                block_count += 1

    # Redact standalone person-name lines when they are clearly part of
    # clinician/contact blocks (name line adjacent to a role line).
    for i in range(len(lines)):
        candidate = lines[i].strip()
        if not candidate or candidate in {"[NAME]", "[PROVIDER-NAME]", "[ADDRESS]", "[POSTCODE]", "[ZIP]"}:
            continue
        if not name_line.match(candidate):
            continue
        if role_line.match(candidate):
            continue

        prev_line = lines[i - 1].strip() if i > 0 else ""
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        if role_line.match(prev_line) or role_line.match(next_line):
            lines[i] = "[NAME]"
            redacted_words[candidate] = "[NAME]"

    # Address block cleanup for letters: if an address/facility line is found,
    # also redact the immediately following city/town line when it is a short
    # title-cased phrase (e.g., "Southampton").
    address_like = re.compile(
        r"\b(?:Street|Road|Avenue|Lane|Drive|Close|Way|Place|Court|Gardens|Terrace|Crescent|"
        r"Grove|Walk|Mews|Row|Square|Hill|Park|Hospital|Infirmary|Surgery|Practice|Clinic|"
        r"Centre|Center|Trust|Unit|Address|Directorate|Department|Division|Service|Team|"
        r"Care\s+Group|Mailpoint)\b",
        re.IGNORECASE,
    )
    city_line = re.compile(r"^[A-Z][^\W\d_]*\.?(?:,?\s+[A-Z][^\W\d_]*\.?)*$")

    for i in range(len(lines) - 1):
        current = lines[i].strip()
        nxt = lines[i + 1].strip()
        if not nxt or nxt in {"[ADDRESS]", "[POSTCODE]", "[ZIP]"}:
            continue

        if current in {"[ADDRESS]"} and city_line.match(nxt):
            lines[i + 1] = "[ADDRESS]"
            continue

        if current in {"[POSTCODE]", "[ZIP]"} and (
            city_line.match(nxt)
            or postal_org_line.match(nxt)
            or mailpoint_line.match(nxt)
            or address_block_line.match(nxt)
        ):
            lines[i + 1] = "[ADDRESS]"
            continue

        if current in {"[POSTCODE]", "[ZIP]", ""}:
            continue

        if current in {"[ADDRESS]"} and (postal_org_line.match(nxt) or mailpoint_line.match(nxt) or address_block_line.match(nxt)):
            lines[i + 1] = "[ADDRESS]"
            continue

        if address_like.search(current) and city_line.match(nxt):
            lines[i + 1] = "[ADDRESS]"

        elif address_like.search(current) and (postal_org_line.match(nxt) or mailpoint_line.match(nxt) or address_block_line.match(nxt)):
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

        # If a line contains one or more redacted person/provider markers
        # followed by an inline postal address and then a postcode, collapse
        # the whole address chunk.
        line = re.sub(
            r"((?:\[(?:NAME|PROVIDER-NAME)\]\s*){1,3},?\s*)"
            r"(?:\d+[A-Za-z]?\s+)?"
            r"(?:[A-Za-z0-9][A-Za-z0-9'\.\-/]*"
            r"(?:\s+[A-Za-z0-9][A-Za-z0-9'\.\-/]*){0,3})"
            r"(?:\s*,\s*(?:[A-Za-z0-9][A-Za-z0-9'\.\-/]*"
            r"(?:\s+[A-Za-z0-9][A-Za-z0-9'\.\-/]*){0,3})){1,4}"
            r"\s*\.?\s*(?=\[(?:POSTCODE|ZIP)\])",
            r"\1[ADDRESS] ",
            line,
            flags=re.IGNORECASE,
        )

        # If a line still contains trailing name tokens after a redacted marker,
        # collapse the remainder to the same marker.
        line = re.sub(
            r"\[NAME\](?:\s+(?:[A-Z]\.?(?=\s|$)|[A-Z][A-Z'\-]+|[A-Z][a-z][A-Za-z'\-]*))+",
            "[NAME]",
            line,
        )
        line = re.sub(
            r"\[NAME\]\s+[A-Z][^\W\d_]+(?=\s*[-,:])",
            "[NAME]",
            line,
        )
        line = re.sub(
            r"\[PROVIDER-NAME\](?:\s+(?:[A-Z]\.?(?=\s|$)|[A-Z][A-Z'\-]+|[A-Z][a-z][A-Za-z'\-]*))+",
            "[PROVIDER-NAME]",
            line,
        )

        # Clean up any remaining slash-delimited local identifiers after an
        # earlier [MED-ID] replacement on the same line.
        line = re.sub(r"(\[MED-ID\]\s*/\s*)([A-Z0-9]{4,12})\b", r"\1[MED-ID]", line)

        lines[i] = line

    text = "\n".join(lines)

    # ── POST-PASS: Check for re-occurrences of redacted words ─────────────────
    # For each word that was redacted, search the entire text for any remaining
    # instances and redact them too. This catches cases where a name or ID appeared
    # multiple times but only the first instance was caught by the regex patterns.
    if redacted_words:
        for original_word, token in redacted_words.items():
            # Build a pattern that matches the word as a whole word, but NOT
            # if it's already inside brackets (e.g. "[NAME]" or "[MED-ID]")
            # Use negative lookbehind/lookahead to avoid words already bracketed.
            word_pattern = r"\b" + re.escape(original_word) + r"\b"
            # Check that it's not already bracketed
            word_pattern = r"(?<!\[)" + word_pattern + r"(?!\])"
            # Replace any un-bracketed occurrences with the token
            text = re.sub(word_pattern, token, text, flags=re.IGNORECASE)

    if use_pteredactyl_rules:
        text = apply_pteredactyl_redaction(text)

    return text


def run_philter_body_aware(
    input_dir: Path,
    output_dir: Path,
    filters_path: Path,
    body_marker: str = "",
    use_pteredactyl_rules: bool = False,
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
        body_targeted = targeted_body_redact(
            body_orig,
            use_pteredactyl_rules=use_pteredactyl_rules,
        )
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

def run_targeted_only_on_folder(
    input_dir: Path,
    output_dir: Path,
    use_pteredactyl_rules: bool = False,
) -> None:
    """Apply the targeted PHI regex patterns to the WHOLE document.

    Skips Philter entirely so medications, diagnoses, lab values and ordinary
    English words (confirmed, initially, engineer, etc.) are preserved.
    Only items matched by ``_BODY_PHI_PATTERNS`` are replaced with placeholders.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for src in input_dir.glob("*.txt"):
        original = src.read_text(encoding="utf-8")
        redacted = targeted_body_redact(
            original,
            use_pteredactyl_rules=use_pteredactyl_rules,
        )
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

    pteredactyl_installed = has_pteredactyl()
    use_pteredactyl_rules = st.checkbox(
        "Use full pteredactyl entities (PERSON, LOCATION, ORG, IDs, dates, phones, regex)",
        value=pteredactyl_installed,
        disabled=not pteredactyl_installed,
        help=(
            "Applies pteredactyl DEFAULT_ENTITIES and DEFAULT_REGEX_ENTITIES as an "
            "extra pass after the project's targeted rules."
        ),
    )
    if not pteredactyl_installed:
        st.caption(
            "pteredactyl not installed. Install with: "
            r".\\.venv311\\Scripts\\python.exe -m pip install pteredactyl"
        )

    output_format = st.radio(
        "Output format",
        options=["PDF only", "TXT only", "Both PDF and TXT"],
        index=0,
        help=(
            "Choose what to generate after redaction.\n\n"
            "- **PDF only** — generate a redacted PDF for download.\n"
            "- **TXT only** — generate a plain-text .txt file (faster; no preview).\n"
            "- **Both PDF and TXT** — generate both formats."
        ),
    )
    want_pdf = output_format in {"PDF only", "Both PDF and TXT"}
    want_txt = output_format in {"TXT only", "Both PDF and TXT"}

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
        PERSISTENT_TXT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
                        run_targeted_only_on_folder(
                            ingested_txt_dir,
                            redacted_txt_dir,
                            use_pteredactyl_rules=use_pteredactyl_rules,
                        )
                    elif body_targeted_mode:
                        run_philter_body_aware(
                            ingested_txt_dir,
                            redacted_txt_dir,
                            filters_path,
                            body_marker=body_marker_override,
                            use_pteredactyl_rules=use_pteredactyl_rules,
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
                stem = Path(original_pdf_name).stem
                redacted_pdf_name = f"{stem}_redacted.pdf"
                redacted_txt_name = f"{stem}_redacted.txt"
                disk_pdf_path = PERSISTENT_OUTPUT_DIR / redacted_pdf_name
                disk_txt_path = PERSISTENT_TXT_OUTPUT_DIR / redacted_txt_name
                original_pdf_bytes = txt_name_to_original_pdf_bytes.get(redacted_txt_file.name, b"")
                original_text = txt_name_to_original_text.get(redacted_txt_file.name, "")

                # Always have the redacted text in memory; only write/build PDF if requested.
                txt_bytes = redacted_text.encode("utf-8")
                if want_txt:
                    disk_txt_path.write_text(redacted_text, encoding="utf-8")

                if want_pdf:
                    write_text_to_pdf(redacted_text, disk_pdf_path)
                    pdf_bytes = disk_pdf_path.read_bytes()
                    layout_preview_pdf_bytes = build_layout_preview_pdf(
                        original_pdf_bytes=original_pdf_bytes,
                        original_text=original_text,
                        redacted_text=redacted_text,
                    )

                    # For non-PDF uploads the stored bytes are not a PDF; generate a
                    # text-rendered PDF so fitz can produce preview images.
                    if original_pdf_bytes and Path(original_pdf_name).suffix.lower() == ".pdf":
                        original_preview_bytes = original_pdf_bytes
                    elif original_text:
                        orig_preview_path = tmp_root / f"{stem}_orig_preview.pdf"
                        write_text_to_pdf(original_text, orig_preview_path)
                        original_preview_bytes = orig_preview_path.read_bytes()
                    else:
                        original_preview_bytes = b""

                    original_previews = render_pdf_preview_pages(original_preview_bytes, max_pages=preview_pages) if original_preview_bytes else []
                    redacted_previews = render_pdf_preview_pages(pdf_bytes, max_pages=preview_pages)

                    st.info(
                        f"Debug for `{original_pdf_name}`: "
                        f"original_pdf_bytes={len(original_pdf_bytes)}, "
                        f"redacted_pdf_bytes={len(pdf_bytes)}, "
                        f"original_previews={len(original_previews)}, "
                        f"redacted_previews={len(redacted_previews)}"
                    )
                else:
                    pdf_bytes = b""
                    layout_preview_pdf_bytes = b""
                    original_preview_bytes = b""
                    original_previews = []
                    redacted_previews = []

                st.session_state["results"].append(
                    {
                        "source_pdf": original_pdf_name,
                        "original_pdf_bytes": original_pdf_bytes,
                        "original_pdf_for_embed": original_preview_bytes,
                        "original_txt_bytes": original_text.encode("utf-8", errors="replace"),
                        "redacted_pdf_name": redacted_pdf_name,
                        "redacted_txt_name": redacted_txt_name,
                        "pdf_bytes": pdf_bytes,
                        "txt_bytes": txt_bytes,
                        "want_pdf": want_pdf,
                        "want_txt": want_txt,
                        "layout_preview_pdf_bytes": layout_preview_pdf_bytes,
                        "saved_path": str(disk_pdf_path) if want_pdf else "",
                        "saved_txt_path": str(disk_txt_path) if want_txt else "",
                        "original_page_previews": original_previews,
                        "redacted_page_previews": redacted_previews,
                    }
                )

            if st.session_state["results"]:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for result in st.session_state["results"]:
                        if result.get("want_pdf") and result.get("pdf_bytes"):
                            zipf.writestr(result["redacted_pdf_name"], result["pdf_bytes"])
                        if result.get("want_txt") and result.get("txt_bytes"):
                            zipf.writestr(result["redacted_txt_name"], result["txt_bytes"])
                st.session_state["zip_bytes"] = zip_buffer.getvalue()

    if st.session_state["results"]:
        st.success(f"Generated {len(st.session_state['results'])} redacted file(s).")
        any_pdf = any(r.get("want_pdf") for r in st.session_state["results"])
        any_txt = any(r.get("want_txt") for r in st.session_state["results"])
        if any_pdf:
            st.caption(f"Saved PDF output folder: {PERSISTENT_OUTPUT_DIR}")
        if any_txt:
            st.caption(f"Saved TXT output folder: {PERSISTENT_TXT_OUTPUT_DIR}")

        if st.session_state["zip_bytes"]:
            st.download_button(
                "Download all redacted files (zip)",
                data=st.session_state["zip_bytes"],
                file_name="redacted_outputs.zip",
                mime="application/zip",
            )

        st.subheader("Outputs")
        for result in st.session_state["results"]:
            st.markdown(f"**Source:** {result['source_pdf']}")
            if result.get("want_pdf") and result.get("saved_path"):
                st.caption(f"Saved PDF: {result['saved_path']}")
            if result.get("want_txt") and result.get("saved_txt_path"):
                st.caption(f"Saved TXT: {result['saved_txt_path']}")

            if result.get("want_pdf") and result.get("pdf_bytes"):
                st.download_button(
                    label=f"Download {result['redacted_pdf_name']}",
                    data=result["pdf_bytes"],
                    file_name=result["redacted_pdf_name"],
                    mime="application/pdf",
                    key=f"dl_pdf_{result['redacted_pdf_name']}",
                )
            if result.get("want_txt") and result.get("txt_bytes"):
                st.download_button(
                    label=f"Download {result['redacted_txt_name']}",
                    data=result["txt_bytes"],
                    file_name=result["redacted_txt_name"],
                    mime="text/plain",
                    key=f"dl_txt_{result['redacted_txt_name']}",
                )

            with st.expander("Show text (original vs redacted)"):
                left_col, right_col = st.columns(2)
                original_text = result.get("original_txt_bytes", b"").decode("utf-8", errors="replace")
                redacted_text = result.get("txt_bytes", b"").decode("utf-8", errors="replace")

                with left_col:
                    st.markdown("**Original text**")
                    if original_text:
                        st.text_area(
                            "Original",
                            value=original_text,
                            height=280,
                            key=f"orig_text_{result['source_pdf']}",
                        )
                    else:
                        st.caption("Original text unavailable for this file.")

                with right_col:
                    st.markdown("**Redacted text**")
                    st.text_area(
                        "Redacted",
                        value=redacted_text,
                        height=280,
                        key=f"redacted_text_{result['redacted_txt_name']}",
                    )

            if not result.get("want_pdf"):
                continue

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
                    original_pdf_for_embed = result.get("original_pdf_for_embed", b"")
                    embed_bytes = original_pdf_for_embed or original_pdf_bytes
                    if embed_bytes:
                        render_embedded_pdf(embed_bytes)
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

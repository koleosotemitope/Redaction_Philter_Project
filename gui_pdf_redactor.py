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

from generate_dataset.convert_docs_to_txt import ocr_pdf, read_pdf_text
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
    except Exception:
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
    except Exception:
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
    except Exception:
        return None

    if not original_pdf_bytes or not original_text or not redacted_text:
        return None

    max_len = min(len(original_text), len(redacted_text))
    starred_indices = {i for i in range(max_len) if redacted_text[i] == "*" and not original_text[i].isspace()}
    if not starred_indices:
        return None

    candidate_terms: set[str] = set()
    for match in re.finditer(r"\b[\w'-]{2,}\b", original_text):
        start, end = match.span()
        if any(idx in starred_indices for idx in range(start, end)):
            term = match.group(0).strip()
            if len(term) >= 2:
                candidate_terms.add(term)

    if not candidate_terms:
        return None

    terms_to_redact = sorted(candidate_terms, key=len, reverse=True)
    try:
        doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
        for page in doc:
            for term in terms_to_redact:
                for rect in page.search_for(term):
                    page.add_redact_annot(rect, fill=(0, 0, 0))
            page.apply_redactions()

        out_bytes = doc.tobytes()
        doc.close()
        return out_bytes
    except Exception:
        return None


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


def app() -> None:
    st.set_page_config(page_title="Philter PDF Redactor", layout="wide")
    st.title("Philter PDF Redactor")
    st.write("Upload PDF files, redact PHI, and download the output as PDF.")

    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
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

    if "results" not in st.session_state:
        st.session_state["results"] = []
    if "failed" not in st.session_state:
        st.session_state["failed"] = []
    if "zip_bytes" not in st.session_state:
        st.session_state["zip_bytes"] = None

    if st.button("Redact PDFs", type="primary"):
        if not uploaded_files:
            st.error("Please upload at least one PDF file.")
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

                text, status = read_pdf_text(pdf_path)
                if (not text) and use_ocr_fallback:
                    text, status = ocr_pdf(pdf_path)

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
                    run_philter_on_folder(ingested_txt_dir, redacted_txt_dir, filters_path)
                except Exception as exc:
                    st.error(f"Philter redaction failed: {exc}")
                    return
            else:
                st.warning("No files were successfully extracted to text, so no redaction was run.")
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

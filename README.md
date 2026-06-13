# Redaction Philter Project

A clinical text de-identification tool that removes Protected Health Information (PHI) from free-text clinical notes. Built on top of [Philter (UCSF)](https://github.com/UCSF-DSCOLAB/philter), extended with a Streamlit GUI, PDF export, UK-specific PHI patterns, and optional [pteredactyl](https://pypi.org/project/pteredactyl/) NER-based redaction.

> **Citation:** If you use this software for any publication, please cite:
> Norgeot, B., Muenzen, K., Peterson, T.A. et al. *Protected Health Information filter (Philter): accurately and securely de-identifying free-text clinical notes.* npj Digit. Med. 3, 57 (2020). https://doi.org/10.1038/s41746-020-0258-y

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start (Recommended)](#quick-start-recommended)
3. [Installing Philter (PyPI)](#installing-philter-pypi)
4. [Installing Requirements](#installing-requirements)
5. [GUI Document Redaction (Streamlit)](#gui-document-redaction-streamlit)
6. [Running Philter: Command-Line Guide](#running-philter-command-line-guide)
7. [Project Runbook (Windows)](#project-runbook-windows)
8. [Common Errors and Fixes](#common-errors-and-fixes)
9. [Git Quick Start](#git-quick-start)
10. [Teammate Setup Checklist](#teammate-setup-checklist)

---

## Overview

This project provides two ways to de-identify clinical notes:

| Method | Best for |
|---|---|
| **Streamlit GUI** (`gui_pdf_redactor.py`) | Interactive use — upload files, choose redaction mode, download redacted PDFs |
| **Command-line** (`main.py`) | Batch processing of large note collections |

**Supported input formats:** `PDF`, `DOC`, `DOCX`, `HTML/HTM`, `TXT`, `JPEG/JPG` (and other image formats via OCR)

**Redaction modes (GUI):**
- **Full Philter** — redacts all PHI everywhere in the document
- **Body-aware** — full Philter in the header, targeted PHI patterns in the body
- **Targeted-only** — whole document, preserves medications/common clinical words while redacting configured PHI patterns

---

## Quick Start (Recommended)

> **Prerequisites:** Python 3.11, [`uv`](https://github.com/astral-sh/uv) package manager

```powershell
# 1. Clone the repo
git clone https://github.com/koleosotemitope/Redaction_Philter_Project.git
cd Redaction_Philter_Project

# 2. Install all dependencies (including GUI + pteredactyl)
uv sync

# 3. Launch the Streamlit GUI
uv run streamlit run .\gui_pdf_redactor.py
```

Open your browser at: **http://localhost:8501**

---

## Installing Philter (PyPI)

To install the core Philter package from PyPI:

```bash
pip3 install philter-ucsf
```

Run Philter from the installed package:

```bash
python3 -m philter_ucsf [flags]
```

> We strongly recommend downloading the project source code and running all sample commands from the project root before using the installed package version.

---

## Installing Requirements

### Base requirements

```bash
pip3 install -r requirements.txt
```

### GUI requirements (Streamlit + pteredactyl)

```bash
pip3 install -r requirements_gui.txt
```

### OCR/PDF conversion requirements

```bash
pip3 install -r requirements_ocr.txt
```

> For image OCR, also install system [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and ensure `tesseract` is available on your `PATH`.

---

## GUI Document Redaction (Streamlit)

### Launch

**Windows (with `uv`):**

```powershell
uv sync
uv run streamlit run .\gui_pdf_redactor.py
```

**Windows (with venv):**

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_gui.txt
.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py
```

**Linux / macOS:**

```bash
pip3 install -r requirements_gui.txt
python3 -m streamlit run gui_pdf_redactor.py
```

### What the GUI does

- Upload one or more files: `PDF`, `DOC`, `DOCX`, `HTML/HTM`, `TXT`, `JPEG/JPG`
- Choose a redaction mode (Full Philter / Body-aware / Targeted-only)
- Optionally enable the `pteredactyl` extra pass for NER-based entity redaction
- Download individual redacted PDFs or a ZIP bundle
- Saves generated PDFs to `data/redacted_out_pdf/`

### Layered Redaction: Project Rules + pteredactyl

The GUI supports a two-pass layered redaction flow:

1. **Pass 1 — Project rules:** your existing Philter regex/filter rules run first
2. **Pass 2 — pteredactyl (optional):** full NER + regex entity pass runs second as an additional layer

Your existing rules are **preserved and not replaced**.

#### pteredactyl entities used

| Entity type | Placeholder |
|---|---|
| `<PERSON>` | `[NAME]` |
| `<LOCATION>` | `[ADDRESS]` |
| `<ORGANIZATION>` | `[ORG-NAME]` |
| `<AGE>` | `[AGE]` |
| `<PHONE_NUMBER>` | `[PHONE]` |
| `<DATE_TIME>` | `[DATE]` |
| `<DEVICE>` | `[SERIAL-NO]` |
| `<ZIP>` | `[ZIP]` |
| `<PROFESSION>` | `[OCCUPATION-ID]` |
| `<USERNAME>` | `[USERNAME]` |
| `<ID>` | `[MED-ID]` |
| `<NHS_NUMBER>` | `[NHS-NO]` |
| `<POSTCODE>` | `[POSTCODE]` |
| `<EMAIL_ADDRESS>` | `[EMAIL]` |

Enable or disable this pass from the GUI checkbox:
> `Use full pteredactyl entities (PERSON, LOCATION, ORG, IDs, dates, phones, regex)`

---

## Running Philter: Command-Line Guide

Philter is a command-line clinical text de-identification tool. It does not require ground-truth annotations to run, but can optionally use them for evaluation.

### Flags

| Flag | Description | Default |
|---|---|---|
| `-i` / `--input` | Path to input directory or file | `./data/i2b2_notes/` |
| `-a` / `--anno` | Path to annotation directory or file | `./data/i2b2_anno/` |
| `-o` / `--output` | Path to output directory | `./data/i2b2_results/` |
| `-f` / `--filters` | Path to config file | `./configs/philter_delta.json` |
| `-x` / `--xml` | Path to JSON file with XML data | `./data/phi_notes.json` |
| `-c` / `--coords` | Output path for coordinate map JSON | `./data/coordinates.json` |
| `-v` / `--verbose` | Emit progress messages | `True` |
| `-e` / `--run_eval` | Run eval script and emit results | `True` |
| `-t` / `--freq_table` | Output unigram/bigram frequency table | `False` |
| `-n` / `--initials` | Include initials PHI in recall/precision | `True` |
| `--eval_output` | Path for detailed eval output files | `./data/phi/` |
| `--outputformat` | Output format: `asterisk` or `i2b2` | `i2b2` |
| `--ucsfformat` | Adjust eval for UCSF XML format | `False` |
| `--prod` | Production mode (no eval, i2b2 XML output) | `False` |
| `--cachepos` | Directory to store/load POS cache | memory |
| `--pdf_output` | Create PDF copies of redacted `.txt` outputs | `False` |

---

### Step 0 — Curate I2B2 XML Files (optional)

Remove non-HIPAA PHI annotations from I2B2 XML files:

```bash
python improve_i2b2_notes.py -i data/i2b2_xml/ -o data/i2b2_xml_updated/
```

---

### Step 1 — Run Philter WITHOUT evaluation

**a.** Ensure input files are in plain text format and stored in a single directory.

**b.** Create an output directory.

**c.** Optionally create a custom config file.

**d.** Run Philter:

```bash
# XML output (PHI tags, not redacted text)
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True

# Asterisk output (PHI replaced with ***)
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True --outputformat "asterisk"
```

> **Note:** XML-formatted output contains the original note text with PHI tags — it does **not** contain redacted text.

#### Optional: Convert PDF/HTML/Images to Plain Text First

```bash
pip3 install -r requirements_ocr.txt
python3 ./generate_dataset/convert_docs_to_txt.py -i ./data/raw_docs/ -o ./data/ingested_txt/
```

Then run Philter on the converted text:

```bash
python3 main.py -i ./data/ingested_txt/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True --outputformat "asterisk"
```

**Conversion notes:**
- For image OCR: install system Tesseract OCR and ensure it is on `PATH`
- For PDFs: native text extraction is tried first; OCR is used as fallback
- For HTML/HTM: tags are stripped and readable text is extracted

#### Running multiple jobs in parallel

Each job must use a separate input directory to avoid cross-contamination:

```bash
nohup python3 main.py -i ./data/batch1/ -o ./data/results1/ -f ./configs/philter_delta.json --prod=True > ./data/batch1/out.txt 2>&1 &
nohup python3 main.py -i ./data/batch2/ -o ./data/results2/ -f ./configs/philter_delta.json --prod=True > ./data/batch2/out.txt 2>&1 &
```

---

### Step 2 — Run Philter WITH evaluation

**a.** Generate Philter-compatible annotation files from I2B2 XML:

```bash
python3 ./generate_dataset/main_ucsf_updated.py \
  -x ./data/i2b2_xml/ \
  -o ./data/phi_notes_i2b2.json \
  -n ./data/i2b2_notes/ \
  -a ./data/i2b2_anno/
```

> If this produces an `ElementTree.ParseError`, remove `.DS_Store` from `./data/i2b2_xml/`.

**b–c.** See Step 1b–c above.

**d.** Run Philter in evaluation mode:

```bash
python3 main.py \
  -i ./data/i2b2_notes/ \
  -a ./data/i2b2_anno/ \
  -o ./data/i2b2_results/ \
  -x ./data/phi_notes_i2b2.json \
  -f ./configs/philter_delta.json \
  --outputformat "asterisk"
```

---

## Project Runbook (Windows)

End-to-end workflow from raw files to redacted output on Windows.

### A. One-time setup

1. Create and activate a Python 3.11 virtual environment:

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
```

2. Install base runtime dependencies:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
```

3. Install OCR/PDF conversion dependencies:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_ocr.txt
```

4. Download required NLTK model (one-time):

```powershell
.\.venv311\Scripts\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger')"
```

> Use `.\.venv311\Scripts\python.exe` for **all** commands below to avoid interpreter mismatch.

---

### B. Input is already plain text (`.txt`)

1. Place text files in `./data/ingested_txt/`

2. Create the output directory:

```powershell
New-Item -ItemType Directory -Force .\data\redacted_out | Out-Null
```

3. Run redaction:

```powershell
.\.venv311\Scripts\python.exe .\main.py `
  -i .\data\ingested_txt\ `
  -o .\data\redacted_out\ `
  -f .\configs\philter_delta.json `
  --prod=True `
  --outputformat asterisk
```

---

### C. Input is PDF, HTML, or image

1. Place source files in `./data/raw_docs/`

2. Convert to text:

```powershell
.\.venv311\Scripts\python.exe .\generate_dataset\convert_docs_to_txt.py `
  -i .\data\raw_docs\ `
  -o .\data\ingested_txt\
```

3. Run the same redaction command from section B.

---

### D. Verify results

1. Open a redacted output file, e.g. `./data/redacted_out/sample_clinical_notes_sensitive.txt`

2. Optional — search for residual UK patterns (NI numbers, sort codes, postcodes):

```powershell
Select-String -Path .\data\redacted_out\*.txt `
  -Pattern 'QQ\s\d{2}\s\d{2}\s\d{2}\s[A-Z]|\b\d{2}-\d{2}-\d{2}\b|\b[A-PR-UWYZ][A-HK-Y]?\d[\dA-HJKSTUW]?\s?\d[ABD-HJLNP-UW-Z]{2}\b'
```

Expected result: no matches.

---

### E. Linux / macOS equivalents

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements_ocr.txt

# Convert PDFs/images to text
python3 ./generate_dataset/convert_docs_to_txt.py -i ./data/raw_docs/ -o ./data/ingested_txt/

# Create output folder
mkdir -p ./data/redacted_out/

# Run redaction
python3 ./main.py -i ./data/ingested_txt/ -o ./data/redacted_out/ -f ./configs/philter_delta.json --prod=True --outputformat asterisk

# Optional pattern verification
grep -En 'QQ[[:space:]][0-9]{2}[[:space:]][0-9]{2}[[:space:]][0-9]{2}[[:space:]][A-Z]|[0-9]{2}-[0-9]{2}-[0-9]{2}|[A-PR-UWYZ][A-HK-Y]?[0-9][0-9A-HJKSTUW]?[[:space:]]?[0-9][ABD-HJLNP-UW-Z]{2}' ./data/redacted_out/*.txt
```

---

## Common Errors and Fixes

### `missing pdf2image/pytesseract`

```text
FAIL ... (missing pdf2image/pytesseract)
```

**Fix:**

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_ocr.txt
.\.venv311\Scripts\python.exe .\generate_dataset\convert_docs_to_txt.py ...
```

---

### `Filepath does not exist for output directory`

```text
Exception: ('Filepath does not exist', '.\\data\\redacted_out\\')
```

**Fix:**

```powershell
New-Item -ItemType Directory -Force .\data\redacted_out | Out-Null
```

---

### `Resource averaged_perceptron_tagger not found`

```text
LookupError: Resource averaged_perceptron_tagger not found
```

**Fix:**

```powershell
.\.venv311\Scripts\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger')"
```

---

### `re.error: global flags not at the start of the expression` (Python 3.11+)

**Cause:** Some legacy regex filter files include inline `(?i)` markers in the middle of expressions, which is not allowed in Python 3.11+.

**Fix in this repo:** `philter.py` and `philter_ucsf/philter.py` now normalize inline `(?i)` markers before compiling regex patterns. No action needed.

---

### Last postcode characters still visible after redaction

**Symptom:**

```text
Address: ** ****** ********, ********, West Yorkshire *** 8JT
```

**Cause:** Existing US ZIP-focused address rules can miss UK inward code fragments.

**Fix:**

1. Add a UK postcode regex file at `filters/regex/addresses/uk_postcode_transformed.txt`:

```text
\b(?i)(GIR\s?0AA|[A-PR-UWYZ][A-HK-Y]?\d[\dA-HJKSTUW]?\s?\d[ABD-HJLNP-UW-Z]{2})\b
```

2. Register the rule in both config files (`configs/philter_delta.json` and `philter_ucsf/configs/philter_delta.json`):

```json
{
    "title": "uk postcode",
    "type": "regex",
    "exclude": true,
    "filepath": "filters/regex/addresses/uk_postcode_transformed.txt",
    "notes": "This should remove UK postcodes such as BD5 8JT or LS11 4RF"
}
```

3. Re-run redaction and verify:

```powershell
.\.venv311\Scripts\python.exe .\main.py -i .\data\ingested_txt\ -o .\data\redacted_out\ -f .\configs\philter_delta.json --prod=True --outputformat asterisk

Select-String -Path .\data\redacted_out\sample_clinical_notes_sensitive.txt -Pattern '8JT|4RF|6PL|BD5|LS11|M14'
```

Expected result: no matches.

---

### pteredactyl notes

- `requirements_gui.txt` includes `pteredactyl`
- On first use, `pteredactyl` may download `en_core_web_sm` for spaCy
- If CUDA is not installed (or incompatible with your torch build), `pteredactyl` runs on CPU
- If model loading fails at runtime, the GUI automatically falls back to regex-only pteredactyl entities so processing still completes
- You can disable the pteredactyl extra pass in the GUI and still keep all project-native rules

---

## Git Quick Start

```powershell
cd C:\Users\<USER>\...\Redaction_Philter_Project
git status
git add .
git commit -m "Update redaction GUI, patterns, and README"
git push
```

Useful checks:

```powershell
git rev-parse --show-toplevel
git log --oneline -n 5
```

First-time identity setup:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## Teammate Setup Checklist

Use this section when another user clones the repo and wants the same behaviour.

### A. Clone and enter project folder

```powershell
git clone https://github.com/koleosotemitope/Redaction_Philter_Project.git
cd Redaction_Philter_Project
```

### B. Create Python 3.11 virtual environment

```powershell
py -3.11 -m venv .venv311
```

### C. Install dependencies

```powershell
.\.venv311\Scripts\python.exe -m pip install --upgrade pip
.\.venv311\Scripts\python.exe -m pip install -r requirements_gui.txt
```

### D. Download required NLTK model (one-time)

```powershell
.\.venv311\Scripts\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger')"
```

### E. Optional: OCR prerequisite (for scanned PDFs/images)

Install system [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and ensure `tesseract` is available on `PATH`.

### F. Run the Streamlit app

```powershell
.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py
```

Open: **http://localhost:8501**

### G. Supported input formats

| Format | Notes |
|---|---|
| PDF | Native text extraction + OCR fallback |
| DOC / DOCX | Microsoft Word documents |
| HTML / HTM | Tags stripped, text extracted |
| TXT | Plain text |
| JPEG / JPG | OCR via Tesseract |

### H. Available redaction modes

| Mode | Description |
|---|---|
| Full Philter | Redacts all PHI everywhere in the document |
| Body-aware | Full Philter in header; targeted patterns in body |
| Targeted-only | Whole document; preserves medications/common words |

### I. Quick sanity test after setup

Upload a small sample containing:

- `Hazel Daniels`
- `February 1st, 2024`
- `Shirley Road, Southampton SO14 7AA`
- A medication phrase such as `Metformin 1000mg daily`

**Expected output in targeted-only mode:**
- Name → redacted
- Date → redacted
- Full address and postcode → redacted
- Medication phrase → **preserved**

### J. Common run mistakes

| Wrong | Correct |
|---|---|
| `..venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py` | `.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py` |
| Running from parent directory | Run from `Redaction_Philter_Project` root |

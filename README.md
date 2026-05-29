
If you use this software for any publication, please cite:
Norgeot, B., Muenzen, K., Peterson, T.A. et al. Protected Health Information filter (Philter): accurately and securely de-identifying free-text clinical notes. npj Digit. Med. 3, 57 (2020). https://doi.org/10.1038/s41746-020-0258-y

# Installing Philter

To install Philter from PyPi, run the following command:

```bash
pip3 install philter-ucsf
```

The main philter code will be executed by running:

```bash
python3 -m philter_ucsf [flags, see below]
```

However, we strongly suggest that you download the project source code and run all sample commands below from the home directory before running the install version of Philter.

# Installing Requirements

To install the Python requirements, run the following command:

```bash
pip3 install -r requirements.txt
```

## GUI Document Redaction (Streamlit)

Run a local Streamlit GUI to upload documents, redact PHI, and download PDF outputs.

Install GUI dependencies:

```bash
pip3 install -r requirements_gui.txt
```

Windows (recommended):

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_gui.txt
.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py
```

The app lets you:
- Upload one or more files in these formats: `PDF`, `DOC`, `DOCX`, `HTML/HTM`, `TXT`, `JPEG/JPG`.
- Choose redaction mode:
	- Full Philter (all PHI everywhere)
	- Body-aware (full in header + targeted in body)
	- Targeted-only (whole document, preserves medications/common words)
- Run PHI redaction using your filter config.
- Download individual redacted PDFs or a ZIP bundle.
- Save generated PDFs to `data/redacted_out_pdf/`.

# Running Philter: A Step-by-Step Guide

Philter is a command-line based clinical text de-identification software that removes protected health information (PHI) from any plain text file. Although the software has built-in evaluation capabilities and can compare Philter PHI-reduced notes with a corresponding set of ground truth annotations, annotations are not required to run Philter. The following steps may be used to 1) run Philter in the command line without ground truth annotations, or 2) generate Philter-compatible annotations and run Philter in evaluation mode using ground truth annotations. Although any set of notes and corresponding annotations may be used with Philter, the examples provided here will correspond to the I2B2 dataset, which Philter uses in its default configuration. 

Before running Philter either with or without evaluation, make sure to familiarize yourself with the various options that may be used for any given Philter run:

### Flags:
**-i (input):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory or the file that contains the clinical note(s), the default is ./data/i2b2_notes/<br/>
**-a (anno):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory or the file that contains the PHI annotation(s), the default is ./data/i2b2_anno/<br/>
**-o (output):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory to save the PHI-reduced notes in, the default is ./data/i2b2_results/<br/>
**-f (filters):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the config file, the default is ./configs/philter_delta.json<br/>
**-x (xml):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the json file that contains all xml data, the default is ./data/phi_notes.json<br/>
**-c (coords):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Output path to the json file that will contain the coordinate map data, the default is ./data/coordinates.json<br/>
**-v (verbose):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When verbose is true, will emit messages about script progress. The default is True<br/>
**-e (run_eval):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When run_eval is true, will run our eval script and emit summarized results to terminal<br/>
**-t (freq_table):**&nbsp;&nbsp;&nbsp;&nbsp;When freqtable is true, will output a unigram/bigram frequency table of all note words and their PHI/non-PHI counts. Default is False<br/>
**-n (initials):**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When initials is true, will include annotated initials PHI in recall/precision calculations. The default is True<br/>
**--eval_output:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to the directory that the detailed eval files will be outputted to, the default is ./data/phi/<br/>
**--outputformat:**&nbsp;&nbsp;Define format of annotation, allowed values are \"asterisk\", \"i2b2\". Default is \"asterisk\"<br/>
**--ucsfformat:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When ucsfformat is true, will adjust eval script for slightly different xml format. The default is False<br/>
**--prod:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;When prod is true, this will run the script with output in i2b2 xml format without running the eval script. The default is False<br/>
**--cachepos:**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Path to a directoy to store/load the pos data for all notes. If no path is specified then memory caching will be used<br/>

## 0. Curating I2B2 XML Files
To remove non-HIPAA PHI annotations from the I2B2 XML files, run the following command:

**-i** Path to the directory that contains the original I2B2 xml files<br/>
**-o** Path to the directory where the curated files will be written<br/>

```bash
python improve_i2b2_notes.py -i data/i2b2_xml/ -o data/i2b2_xml_updated/
```

## 1. Running Philter WITHOUT evaluation (no ground-truth annotations required)

**a.** Make sure the input file(s) are in plain text format. If you are using the I2B2 dataset (or any other dataset in XML or other formats), the note text must be extracted from each original file and be saved in individual text files. Examples of properly formatted input files can be found in ./data/i2b2_notes/.

**b.** Store all input file(s) in the same directory, and create an output directory (if you want the PHI-reduced notes to be stored somewhere other than the default location).

**c.** Create a configuration file with specified filters (if you do not want to use the default configuration file).

**d.** Run Philter in the command line using either default or custom parameters.

Use the following command to run a single job and output files in XML format:
```bash
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True
```
IMPORTANT NOTE: XML-formatted files do NOT have PHI-reduced text. Instead, they contain the original note text with the PHI tags identified by Philter. 

### Optional: Convert PDF/HTML/Images to Plain Text First

Philter processes plain text notes. If your source files are PDF/HTML/JPEG/PNG/TIFF/BMP, convert them to `.txt` first:

```bash
pip3 install -r requirements_ocr.txt
python3 ./generate_dataset/convert_docs_to_txt.py -i ./data/raw_docs/ -o ./data/ingested_txt/
```

Then run Philter using the generated text directory:

```bash
python3 main.py -i ./data/ingested_txt/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True --outputformat "asterisk"
```

Notes:
- For image OCR, install system Tesseract OCR and ensure it is available on PATH.
- For PDFs, the converter first tries native text extraction and falls back to OCR when needed.
- For HTML/HTM, tags are stripped and readable text is extracted.

If you'd like to output ONLY the PHI-reduced text with asterisks obscuring Philter-identified PHI, simply add the -outputformat "asterisk" option:
```bash
python3 main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -f ./configs/philter_delta.json --prod=True --outputformat "asterisk"
```

To run multiple jobs simultaneously, all input notes handled by a single job must be located in separate directories to avoid cross-contamination between output files. For example, if you wanted to run Philter on 1000 notes simultaneously on two processes, the two input directories might look like:

1. ./data/batch1/500_input_notes_batch1/
2. ./data/batch2/500_input_notes_batch2/

In this example, the following two commands would be used to start running each job in the background:
```bash
nohup python3 main.py -i ./data/batch1/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/philter_delta.json --prod=True > ./data/batch1/batch1_terminal_out.txt 2>&1 &

```
```bash
nohup python3 main.py -i ./data/batch2/500_input_notes_batch2/ -o ./data/i2b2_results_test/ -f ./configs/philter_delta.json --prod=True > ./data/batch2/batch2_terminal_out.txt 2>&1 &

```

## 2. Running Philter WITH evaluation (ground truth annotations required)

**a.** Create Philter-compatible annotation files using the transformation script located in ./generate_dataset/. This script expects notes in xml format, and transforms each input file into two plain text files: 1) the original note text, and 2) the note text with asterisks obscuring PHI. A properly formatted xml input can be found in ./data/i2b2_xml, and examples of the two outputs can be found in ./data/i2b2_notes and ./data/i2b2_anno, respectively. Additionally, this script creates a .json file that contains the original text from each note, followed by the PHI annotations in json format. An example of this output file can be found at ./data/phi_notes_i2b2.json. This is the file that will be used as the -x default option. 

### Flags:

**-x** Path to the directory file that contains the note xml files<br/>
**-o** Path to the json file that will contain a summary of the phi in the xml files<br/>
**-n** Path to the directory where you would like to store the plain text notes<br/>
**-a** Path to the directory where you would like to store the plain text annotations<br/>

Use the following command to create these input files from notes in XML format:

```bash
python3 ./generate_dataset/main_ucsf_updated.py -x ./data/i2b2_xml/ -o ./data/phi_notes_i2b2.json -n ./data/i2b2_notes/ -a ./data/i2b2_anno/
```
Note: If this command produces an ElementTree.ParseError, you may need to remove .DS_Store from ./data/i2b2_xml.

**b-c.** See Step 1b-c above

**d.** Run Philter in evaluation mode using the following command:

```bash
python3 main.py -i ./data/i2b2_notes/ -a ./data/i2b2_anno/ -o ./data/i2b2_results/ -x ./data/phi_notes_i2b2.json -f=./configs/philter_delta.json --outputformat "asterisk"
```

By defult, this will output PHI-reduced notes (.txt format) in the specified output directory. If this command is used with the --outputformat i2b2 flag (or with no --outputformat specified, since i2b2 format is the default option), the evaluation script will not be run and the script will output notes with the original text and the Philter PHI tags (.xml format) in the specified output directory.

## 3. Project Runbook (Windows: Step-by-Step Commands + What They Do)

This is the fastest end-to-end workflow for this repo, from raw files to redacted output.

### A. One-time setup

1. Create and activate your virtual environment.

2. Install base runtime dependencies:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements.txt
```

What this does: installs core Philter packages used by `main.py`.

3. Install OCR/PDF conversion dependencies:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_ocr.txt
```

What this does: installs `pytesseract`, `pdf2image`, and related packages used by `generate_dataset/convert_docs_to_txt.py`.

Important: use `.\.venv311\Scripts\python.exe` for all commands below to avoid interpreter mismatch.

### B. If your input is already text (`.txt`)

1. Make sure your text files are in:

```text
./data/ingested_txt/
```

2. Create output directory if missing:

```powershell
New-Item -ItemType Directory -Force .\data\redacted_out | Out-Null
```

What this does: ensures the output path exists (Philter expects it to exist).

3. Run redaction:

```powershell
.\.venv311\Scripts\python.exe .\main.py -i .\data\ingested_txt\ -o .\data\redacted_out\ -f .\configs\philter_delta.json --prod=True --outputformat asterisk
```

What this does:
- `-i`: input folder of notes
- `-o`: output folder for redacted notes
- `-f`: active regex/filter config
- `--prod=True`: production redaction run
- `--outputformat asterisk`: masks detected sensitive text with `*`

### C. If your input is PDF/HTML/image

1. Put source files in:

```text
./data/raw_docs/
```

2. Convert to text:

```powershell
.\.venv311\Scripts\python.exe .\generate_dataset\convert_docs_to_txt.py -i .\data\raw_docs\ -o .\data\ingested_txt\
```

What this does: extracts text from PDFs/images and writes `.txt` files to `./data/ingested_txt/`.

3. Run the same redaction command from section B:

```powershell
.\.venv311\Scripts\python.exe .\main.py -i .\data\ingested_txt\ -o .\data\redacted_out\ -f .\configs\philter_delta.json --prod=True --outputformat asterisk
```

### D. Verify results quickly

1. Open a redacted output file, for example:

```text
./data/redacted_out/sample_clinical_notes_sensitive.txt
```

2. Optional keyword checks:

```powershell
Select-String -Path .\data\redacted_out\*.txt -Pattern 'QQ\s\d{2}\s\d{2}\s\d{2}\s[A-Z]|\b\d{2}-\d{2}-\d{2}\b|\b[A-PR-UWYZ][A-HK-Y]?\d[\dA-HJKSTUW]?\s?\d[ABD-HJLNP-UW-Z]{2}\b'
```

What this does: searches output files for patterns that resemble UK NI numbers, sort codes, and UK postcodes.

### E. Linux/macOS command equivalents

Use this if you are not on Windows.

1. Create and activate venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements_ocr.txt
```

3. Convert PDFs/images to text:

```bash
python3 ./generate_dataset/convert_docs_to_txt.py -i ./data/raw_docs/ -o ./data/ingested_txt/
```

4. Create output folder:

```bash
mkdir -p ./data/redacted_out/
```

5. Run redaction:

```bash
python3 ./main.py -i ./data/ingested_txt/ -o ./data/redacted_out/ -f ./configs/philter_delta.json --prod=True --outputformat asterisk
```

6. Optional pattern verification:

```bash
grep -En 'QQ[[:space:]][0-9]{2}[[:space:]][0-9]{2}[[:space:]][0-9]{2}[[:space:]][A-Z]|[0-9]{2}-[0-9]{2}-[0-9]{2}|[A-PR-UWYZ][A-HK-Y]?[0-9][0-9A-HJKSTUW]?[[:space:]]?[0-9][ABD-HJLNP-UW-Z]{2}' ./data/redacted_out/*.txt
```

---

## 4. Common Errors and Fixes

### Error: missing pdf2image/pytesseract

Symptom:

```text
FAIL ... (missing pdf2image/pytesseract)
```

Fix:

```powershell
.\.venv311\Scripts\python.exe -m pip install -r requirements_ocr.txt
```

Also ensure you run the correct script path:

```powershell
.\.venv311\Scripts\python.exe .\generate_dataset\convert_docs_to_txt.py ...
```

### Error: Filepath does not exist for output directory

Symptom:

```text
Exception: ('Filepath does not exist', '.\\data\\redacted_out\\')
```

Fix:

```powershell
New-Item -ItemType Directory -Force .\data\redacted_out | Out-Null
```

### Error: Resource averaged_perceptron_tagger not found

Symptom:

```text
LookupError: Resource averaged_perceptron_tagger not found
```

Fix:

```powershell
.\.venv311\Scripts\python.exe -c "import nltk; nltk.download('averaged_perceptron_tagger')"
```

### Error: re.error global flags not at the start of the expression

Symptom on Python 3.11+:

```text
re.error: global flags not at the start of the expression
```

Cause:
- Some legacy regex files include inline case-insensitive markers like `(?i)` in the middle of expressions.

Fix in this repo:
- `philter.py` and `philter_ucsf/philter.py` now normalize inline `(?i)` markers before compiling regex patterns.

### Issue: Last postcode characters are still visible after redaction

Symptom:

```text
Address: ** ****** ********, ********, West Yorkshire *** 8JT
```

Cause:
- Existing US ZIP-focused address rules can miss UK inward code fragments.

Process to fix:

1. Add a UK postcode regex file:

```text
filters/regex/addresses/uk_postcode_transformed.txt
```

with this pattern:

```text
\b(?i)(GIR\s?0AA|[A-PR-UWYZ][A-HK-Y]?\d[\dA-HJKSTUW]?\s?\d[ABD-HJLNP-UW-Z]{2})\b
```

2. Register the rule in config files:

- `configs/philter_delta.json`
- `philter_ucsf/configs/philter_delta.json`

Use a regex rule entry like:

```json
{
	"title": "uk postcode",
	"type": "regex",
	"exclude": true,
	"filepath": "filters/regex/addresses/uk_postcode_transformed.txt",
	"notes": "This should remove UK postcodes such as BD5 8JT or LS11 4RF"
}
```

3. Re-run redaction:

```powershell
.\.venv311\Scripts\python.exe .\main.py -i .\data\ingested_txt\ -o .\data\redacted_out\ -f .\configs\philter_delta.json --prod=True --outputformat asterisk
```

4. Verify postcodes are fully masked:

```powershell
Select-String -Path .\data\redacted_out\sample_clinical_notes_sensitive.txt -Pattern '8JT|4RF|6PL|BD5|LS11|M14'
```

Expected result: no matches.

### OCR notes

- For scanned PDFs/images, install system Tesseract OCR and ensure `tesseract` is available on PATH.
- For text-native PDFs, conversion often succeeds without OCR fallback.

---

## 5. Git Quick Start (This Repo)

Use these commands to save all your work to Git from the repository root:

```powershell
cd C:\Users\koleot\Downloads\redaction_phil\Redaction_Philter_Project
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

If Git asks for your identity on first commit:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## 6. Teammate Setup and Run Checklist (Copy/Paste)

Use this section when another user clones the repo and wants the same behavior.

### A. Clone and enter project folder

```powershell
git clone <YOUR_REPO_URL>
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

### E. Optional OCR prerequisite (for scanned PDFs/images)

Install system Tesseract OCR and ensure `tesseract` is available on PATH.

### F. Run the Streamlit app

```powershell
cd C:\Users\<USER>\...\Redaction_Philter_Project
.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py
```

Open: `http://localhost:8501`

### G. Supported input formats in GUI

- PDF
- DOC / DOCX
- HTML / HTM
- TXT
- JPEG / JPG (and other image OCR formats already supported in converter)

### H. Available redaction modes

- Full Philter (all PHI everywhere)
- Body-aware (full in header, targeted in body)
- Targeted only (whole document; preserves medications/common words while redacting configured PHI patterns)

### I. Quick sanity test after setup

Create/upload a small sample containing:

- `Hazel Daniels`
- `February 1st, 2024`
- `Shirley Road, Southampton SO14 7AA`
- a medication phrase such as `Metformin 1000mg daily`

Expected in targeted-only mode:

- name redacted
- date redacted
- full address/postcode redacted
- medication phrase preserved

### J. Common run mistakes

- Wrong: `..venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py`
- Correct: `.\.venv311\Scripts\python.exe -m streamlit run gui_pdf_redactor.py`

- Wrong folder: running from parent directory without project path
- Correct: run from `Redaction_Philter_Project` root (or provide full relative paths)
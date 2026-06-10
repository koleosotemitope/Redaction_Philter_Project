# Seminar Demo Script: Automated PHI Redaction for Clinical Documents

## Preparation (Before the Seminar)

### 1. Set Up the Environment
```powershell
cd C:\Users\koleot\Downloads\redaction_phil
uv sync
```

### 2. Prepare Sample Documents
Create a sample clinical note with obvious PHI for the demo:

**Create `demo_sample_note.txt`:**
```
Patient Name: John A. Smith
Date of Birth: March 15, 1965
Address: 1234 Oak Street, Suite 200, Los Angeles, CA 90001
Phone: (310) 555-7890
Email: john.smith@email.com

Medical Record Number: MRN-2024-45678

Clinical Note - Date: January 10, 2025

Chief Complaint:
The patient presents with persistent cough and shortness of breath for the past two weeks.

History of Present Illness:
Mr. Smith is a 59-year-old male who presents to the clinic at UCLA Medical Center 
for evaluation of respiratory symptoms. He reports a dry cough that has been present 
for approximately 14 days. He also complains of mild shortness of breath when 
climbing stairs.

Past Medical History:
- Hypertension (diagnosed 2018)
- Type 2 Diabetes Mellitus
- Asthma

Current Medications:
- Lisinopril 10mg daily
- Metformin 500mg twice daily
- Albuterol inhaler as needed

Physical Examination:
Blood Pressure: 138/88 mmHg
Heart Rate: 78 bpm
Temperature: 98.6°F
Respiratory Rate: 18 breaths per minute
Oxygen Saturation: 96% on room air

Assessment and Plan:
1. Upper respiratory infection - likely viral etiology
2. Continue current medications
3. Follow up in 2 weeks
4. Recommend chest X-ray if symptoms persist

Provider: Dr. Sarah Johnson, MD
Department of Internal Medicine
UCLA Medical Center
Phone: (310) 555-1234
```

---

## Demo 1: Streamlit GUI (Primary Demo) — 10 minutes

### Step 1: Launch the GUI
```powershell
uv run streamlit run gui_pdf_redactor.py
```
This opens a browser window at `http://localhost:8501`

### Step 2: Walk Through the Interface
**Say:** *"This is our web-based interface for redacting PHI from clinical documents. Let me show you how it works."*

1. **Point out the upload area** — "You can upload PDF, DOC, DOCX, HTML, TXT, or image files"
2. **Show the three redaction modes:**
   - **Full Philter** — "Aggressive redaction of ALL PHI everywhere"
   - **Body-aware** — "Full redaction in headers, targeted in body text"
   - **Targeted-only** — "Only redacts specific PHI types, preserves medications"
3. **Show the pteredactyl checkbox** — "We also have an optional deep learning NER pass as a safety net"

### Step 3: Upload the Sample Document
1. Click **Upload Files**
2. Select your `demo_sample_note.txt` (or convert it to PDF first)
3. **Say:** *"Here you can see the original document with all the sensitive information highlighted"*

### Step 4: Run Redaction
1. Select **Full Philter** mode
2. Click **Redact**
3. **Say:** *"Watch as the system automatically identifies and redacts all PHI..."*

### Step 5: Show Before/After
1. Show the original document
2. Show the redacted output
3. **Point out each redacted element:**
   - `[NAME]` — John A. Smith, Dr. Sarah Johnson
   - `[DATE]` — March 15, 1965, January 10, 2025, 2018, 14 days, 2 weeks
   - `[ADDRESS]` — 1234 Oak Street, Suite 200, Los Angeles, CA 90001
   - `[PHONE]` — (310) 555-7890, (310) 555-1234
   - `[EMAIL]` — john.smith@email.com
   - `[MED-ID]` — MRN-2024-45678
   - `[AGE]` — 59-year-old
   - `[ORG-NAME]` — UCLA Medical Center

**Say:** *"Every single piece of protected health information has been replaced with a placeholder. The clinical content remains intact for research purposes."*

### Step 6: Download the Redacted File
1. Click **Download**
2. **Say:** *"The redacted file is ready for sharing with researchers or for publication."*

---

## Demo 2: Command Line Interface — 5 minutes

### Step 1: Run Philter on Text Files
```powershell
uv run python main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -e false
```

**Say:** *"For batch processing, we also have a command-line interface that can process entire directories of clinical notes."*

### Step 2: Show the Output
```powershell
Get-Content ./data/i2b2_results/110-01.txt -Head 20
```

**Say:** *"Here you can see the redacted output. All PHI has been replaced with placeholders while maintaining the document structure."*

### Step 3: Run Evaluation (Optional)
```powershell
uv run python eval_scrubber_ucsf.py -p ./data/i2b2_results/ -a ./data/i2b2_anno/ -o ./data/i2b2_eval/
```

**Say:** *"We can also evaluate the accuracy of our redaction by comparing against ground truth annotations. This gives us precision and recall scores."*

---

## Demo 3: Show the Architecture — 5 minutes

### Open the Code Structure
```powershell
code .
```

**Walk through the key files:**

1. **`philter.py`** — "This is the core engine. It loads filter configurations and applies regex patterns, blacklists, and whitelists to detect PHI."

2. **`coordinate_map.py`** — "This tracks the exact character positions of every PHI match, which is essential for accurate redaction."

3. **`configs/philter_delta.json`** — "This configuration file defines all the detection rules. You can see we have rules for names, addresses, dates, phone numbers, and more."

4. **`filters/regex/`** — "We have over 100 regex rule files organized by category. Each file contains patterns for a specific type of PHI."

5. **`gui_pdf_redactor.py`** — "This is the Streamlit GUI that makes the tool accessible to non-technical users."

---

## Demo 4: Show Evaluation Results — 5 minutes

### Run the Evaluation Script
```powershell
uv run python eval_scrubber_ucsf.py -p ./data/i2b2_results/ -a ./data/i2b2_anno/ -o ./data/i2b2_eval/
```

### Show the Results
```powershell
Get-Content ./data/phi/summary.txt
```

**Say:** *"The evaluation script compares our redacted output against manually annotated ground truth. It calculates:"*
- **Precision**: What percentage of redacted items were actually PHI? (Higher is better — fewer false positives)
- **Recall**: What percentage of actual PHI was caught? (Higher is better — fewer false negatives)

**Explain the metrics:**
- **True Positive (TP)**: Correctly redacted PHI
- **False Positive (FP)**: Non-PHI that was incorrectly redacted (e.g., a legitimate word like "heart" in "heart rate")
- **False Negative (FN)**: Actual PHI that was missed (dangerous — privacy breach)

---

## Closing Remarks

### Key Takeaways
1. **Automated PHI redaction** is essential for clinical research and data sharing
2. **Multi-layer approach** (regex + NER) achieves high accuracy
3. **Open-source and extensible** — you can add your own rules
4. **Handles multiple formats** — PDF, DOC, DOCX, HTML, TXT, images with OCR
5. **Provides evaluation** — you can measure precision and recall

### Citation
```
Norgeot, B., Muenzen, K., Peterson, T.A. et al. Protected Health Information filter 
(Philter): accurately and securely de-identifying free-text clinical notes. 
npj Digit. Med. 3, 57 (2020). https://doi.org/10.1038/s41746-020-0258-y
```

### Q&A Preparation
Be ready to answer:
- **How accurate is it?** — Show precision/recall scores from evaluation
- **What formats does it support?** — PDF, DOC, DOCX, HTML, TXT, images
- **Can it handle scanned documents?** — Yes, with OCR
- **Is it HIPAA compliant?** — It helps achieve compliance by removing PHI, but you need to validate for your specific use case
- **How do I add custom rules?** — Add a new file in `filters/regex/` and update `configs/philter_delta.json`
- **What's the difference between Philter and pteredactyl?** — Philter uses regex/rules, pteredactyl uses deep learning NER. We combine both for best results.

---

## Quick Reference Commands

```powershell
# Launch GUI
uv run streamlit run gui_pdf_redactor.py

# Run CLI on text files
uv run python main.py -i ./data/i2b2_notes/ -o ./data/i2b2_results/ -e false

# Run evaluation
uv run python eval_scrubber_ucsf.py -p ./data/i2b2_results/ -a ./data/i2b2_anno/ -o ./data/i2b2_eval/

# View redacted output
Get-Content ./data/i2b2_results/110-01.txt

# View evaluation results
Get-Content ./data/phi/summary.txt
```

from philter import Philter
import json

# Load config
with open('configs/philter_delta.json') as f:
    config = json.load(f)

# Initialize Philter with the config
p = Philter(config)

# Test the problematic text
test_text = """Medication Administration & Sensitive Data Sheet
Medication
Dose
Frequency
Prescriber
Morphine Sulfate
10mg
Every * *** ***
*** - Helen Morris
Warfarin
5mg
Once daily
Dr. Alan Price
Levothyroxine
75mcg
Morning
Dr. Rachel Singh
Pregabalin
150mg
Twice daily
Dr. Omar Patel
Clonazepam
1mg
Nightly
Dr. Imran Siddiqui
Oxycodone
20mg
Twice daily"""

redacted = p.redact(test_text)
print("REDACTED OUTPUT:")
print(redacted)
print("\n\nCHECKS:")
print(f"Helen Morris removed: {'Helen Morris' not in redacted and 'helen morris' not in redacted.lower()}")
print(f"Alan Price removed: {'Alan Price' not in redacted and 'alan price' not in redacted.lower()}")
print(f"Rachel Singh removed: {'Rachel Singh' not in redacted and 'rachel singh' not in redacted.lower()}")
print(f"Omar Patel removed: {'Omar Patel' not in redacted and 'omar patel' not in redacted.lower()}")
print(f"Imran Siddiqui removed: {'Imran Siddiqui' not in redacted and 'imran siddiqui' not in redacted.lower()}")
print(f"Morphine Sulfate preserved: {'Morphine' in redacted or 'morphine' in redacted.lower()}")
print(f"Warfarin preserved: {'Warfarin' in redacted or 'warfarin' in redacted.lower()}")

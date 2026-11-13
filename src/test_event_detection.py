
from pathlib import Path
import pandas as pd
from event_extractor import EVENT_PATTERNS

from event_extractor import detect_event_types

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "processed_clinical_notes.csv"
)

notes = pd.read_csv(INPUT_PATH)

# Find the detailed abdominal pain assessment.
sample = notes[
    notes["clean_note_text"].astype(str).str.contains(
        "macrogol",
        case=False,
        na=False
    )
]

print("Notes containing macrogol:", len(sample))

for _, row in sample.head(3).iterrows():

    text = str(row["clean_note_text"])

    print("\n" + "=" * 60)
    print("NOTE ID:", row["clinical_note_id"])

    print("\nDETECTED EVENT TYPES:")

    detected = detect_event_types(text)

    for event_type in detected:
        print("-", event_type)

    print("\nKEYWORDS CHECK:")

    for category, keywords in EVENT_PATTERNS.items():
        pass

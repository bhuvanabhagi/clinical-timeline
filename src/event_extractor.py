from pathlib import Path
import pandas as pd
import re


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "processed_clinical_notes.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clinical_events.csv"
)


# ---------------------------------------------------------
# EVENT KEYWORDS
# ---------------------------------------------------------

EVENT_PATTERNS = {
    "Symptom": [
        "headache",
        "pain",
        "nausea",
        "vomiting",
        "fever",
        "dizziness",
        "weakness",
        "shortness of breath",
    ],

    "Investigation": [
        "ct scan",
        "ct head",
        "mri",
        "mra",
        "x-ray",
        "blood test",
        "blood tests",
        "fbc",
        "renal panel",
        "lft",
        "investigation",
        "scan",
    ],

    "Diagnosis": [
        "diagnosis",
        "diagnosed",
        "impression",
        "rcvs",
        "infection",
        "pneumonia",
        "stroke",
    ],

    "Treatment": [
        "started",
        "start",
        "treatment",
        "medication",
        "prescribed",
        "nimodipine",
        "paracetamol",
        "antibiotic",
    ],

    "Monitoring": [
        "monitor",
        "monitoring",
        "observed",
        "observation",
        "bp monitoring",
        "follow-up monitoring",
    ],

    "Discharge": [
        "discharge",
        "discharged",
        "discharge planning",
    ],

    "Follow-up": [
        "follow-up",
        "follow up",
        "gp follow-up",
        "review",
    ],
}


# ---------------------------------------------------------
# FIND EVENT TYPE
# ---------------------------------------------------------

def detect_event_types(text):
    """
    Detect all matching clinical event categories.
    """

    if pd.isna(text):
        return ["Other"]

    text_lower = str(text).lower()

    detected_events = []

    for event_type, keywords in EVENT_PATTERNS.items():

        for keyword in keywords:

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword)
                + r"(?!\w)"
            )

            if re.search(pattern, text_lower):
                detected_events.append(event_type)
                break

    if not detected_events:
        return ["Other"]

    return detected_events


# ---------------------------------------------------------
# EXTRACT EVIDENCE
# ---------------------------------------------------------

def extract_evidence(text, event_type):
    """
    Return a sentence containing evidence for the event.
    """

    sentences = re.split(r"(?<=[.!?])\s+", text)

    keywords = EVENT_PATTERNS.get(event_type, [])

    for sentence in sentences:

        sentence_lower = sentence.lower()

        for keyword in keywords:

            if keyword in sentence_lower:
                return sentence.strip()

    return text[:300].strip()


# ---------------------------------------------------------
# MAIN EVENT EXTRACTION
# ---------------------------------------------------------


def extract_events():

    print("Loading processed clinical notes...")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    notes = pd.read_csv(INPUT_PATH)

    print("Total notes:", len(notes))

    events = []

    for _, row in notes.iterrows():

        text = row["clean_note_text"]

        # Detect multiple event categories.
        event_types = detect_event_types(text)

        for event_type in event_types:

            evidence = extract_evidence(
                text,
                event_type
            )

            event = {
                "person_id": row["person_id"],
                "admission_id": row["admission_id"],
                "clinical_note_id": row["clinical_note_id"],
                "event_date": row["creation_timestamp"],
                "event_type": event_type,
                "event_text": evidence,
                "full_note_text": text,
                "note_subject": row["note_subject"],
                "note_type": row["note_type"],
            }

            events.append(event)

    events_df = pd.DataFrame(events)

    events_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n========================================")
    print("MULTI-CATEGORY EVENT EXTRACTION COMPLETED")
    print("========================================")

    print("Original notes:", len(notes))
    print("Extracted event categories:", len(events_df))

    print("\nEvent type distribution:")

    print(events_df["event_type"].value_counts())

    print("\nSaved to:")
    print(OUTPUT_PATH)



if __name__ == "__main__":
    extract_events()
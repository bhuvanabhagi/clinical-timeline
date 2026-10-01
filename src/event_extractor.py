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

def detect_event_type(text):
    """
    Identify the first matching clinical event category.
    """

    text_lower = text.lower()

    for event_type, keywords in EVENT_PATTERNS.items():

        for keyword in keywords:

            if keyword in text_lower:
                return event_type

    return "Other"


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

    notes = pd.read_csv(INPUT_PATH)

    print("Total notes:", len(notes))

    events = []

    for _, row in notes.iterrows():

        text = str(row["clean_note_text"])

        event_type = detect_event_type(text)

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
            "note_subject": row["note_subject"],
            "note_type": row["note_type"],
        }

        events.append(event)

    events_df = pd.DataFrame(events)

    events_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("========================================")
    print("EVENT EXTRACTION COMPLETED")
    print("========================================")

    print("Total events:", len(events_df))

    print()
    print("Event type distribution:")

    print(
        events_df["event_type"]
        .value_counts()
    )

    print()
    print("Saved to:")

    print(OUTPUT_PATH)


if __name__ == "__main__":
    extract_events()
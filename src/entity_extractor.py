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
    / "clinical_events.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clinical_entities.csv"
)


# ---------------------------------------------------------
# ENTITY KEYWORDS
# ---------------------------------------------------------

ENTITY_PATTERNS = {

    "SYMPTOM": [
        "severe headache",
        "headache",
        "pain",
        "nausea",
        "vomiting",
        "fever",
        "dizziness",
        "weakness",
        "shortness of breath",
    ],

    "DIAGNOSIS": [
        "rcvs",
        "pneumonia",
        "stroke",
        "infection",
        "diagnosis",
        "hypertension",
    ],

    "MEDICATION": [
        "nimodipine",
        "paracetamol",
        "antibiotic",
        "medication",
        "aspirin",
        "ibuprofen",
    ],

    "PROCEDURE_TEST": [
        "ct head",
        "ct scan",
        "mri",
        "mra",
        "x-ray",
        "blood test",
        "blood tests",
        "fbc",
        "renal panel",
        "lft",
    ],

    "BODY_PART": [
        "head",
        "brain",
        "chest",
        "abdomen",
        "heart",
        "lung",
    ],
}


# ---------------------------------------------------------
# ENTITY EXTRACTION
# ---------------------------------------------------------

def extract_entities(text):

    text_lower = text.lower()

    found_entities = []

    for entity_type, keywords in ENTITY_PATTERNS.items():

        for keyword in keywords:

            if keyword in text_lower:

                found_entities.append({
                    "entity_type": entity_type,
                    "entity_text": keyword
                })

    return found_entities


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def extract_all_entities():

    print("Loading clinical events...")

    events = pd.read_csv(INPUT_PATH)

    print("Total events:", len(events))

    extracted = []

    for _, row in events.iterrows():

        text = str(row["event_text"])

        entities = extract_entities(text)

        for entity in entities:

            extracted.append({
                "person_id": row["person_id"],
                "admission_id": row["admission_id"],
                "clinical_note_id": row["clinical_note_id"],
                "event_date": row["event_date"],
                "event_type": row["event_type"],
                "entity_type": entity["entity_type"],
                "entity_text": entity["entity_text"],
                "evidence": text,
            })


    entities_df = pd.DataFrame(extracted)

    entities_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("========================================")
    print("ENTITY EXTRACTION COMPLETED")
    print("========================================")

    print("Total entities:", len(entities_df))

    print()
    print("Entity distribution:")

    print(
        entities_df["entity_type"]
        .value_counts()
    )

    print()
    print("Sample entities:")

    print(
        entities_df[
            [
                "entity_type",
                "entity_text",
                "event_type"
            ]
        ].head(20)
    )

    print()
    print("Saved to:")

    print(OUTPUT_PATH)


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    extract_all_entities()
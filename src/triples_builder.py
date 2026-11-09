
from pathlib import Path
import pandas as pd
import re

# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

EVENTS_PATH = PROCESSED_DIR / "clinical_events.csv"
ENTITIES_PATH = PROCESSED_DIR / "clinical_entities.csv"
OUTPUT_PATH = PROCESSED_DIR / "clinical_triples.csv"


# --------------------------------------------------
# RELATIONSHIPS
# --------------------------------------------------

RELATION_MAP = {
    "SYMPTOM": "HAS_SYMPTOM",
    "DIAGNOSIS": "HAS_DIAGNOSIS",
    "MEDICATION": "MENTIONS_MEDICATION",
    "PROCEDURE_TEST": "MENTIONS_TEST",
    "BODY_PART": "MENTIONS_BODY_PART",
}

# Simple negation patterns for a first prototype.
# This is not a complete clinical negation detector.
NEGATION_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bwithout\b",
    r"\bnegative for\b",
    r"\bno evidence of\b",
]


def is_negated(entity_text, evidence):
    """Check for a simple negation near an entity mention."""

    text = str(evidence).lower()
    entity = str(entity_text).lower()

    for match in re.finditer(re.escape(entity), text):
        start = max(0, match.start() - 60)
        context = text[start:match.start()]

        if any(
            re.search(pattern, context)
            for pattern in NEGATION_PATTERNS
        ):
            return True

    return False


def build_triples():
    print("Loading events and entities...")

    events = pd.read_csv(EVENTS_PATH).fillna("")
    entities = pd.read_csv(ENTITIES_PATH).fillna("")

    triples = []

    # --------------------------------------------------
    # 1. EVENT TRIPLES
    # --------------------------------------------------

    for _, row in events.iterrows():
        patient_id = str(row["person_id"]).strip()
        event_text = str(row["event_text"]).strip()
        event_type = str(row["event_type"]).strip()
        event_date = row["event_date"]

        if not patient_id or not event_text:
            continue

        triples.append({
            "subject": f"Patient:{patient_id}",
            "predicate": "HAS_CLINICAL_EVENT",
            "object": f"Event:{event_type}",
            "event_date": event_date,
            "event_type": event_type,
            "patient_id": patient_id,
            "admission_id": row.get("admission_id", ""),
            "clinical_note_id": row.get("clinical_note_id", ""),
            "evidence": event_text,
            "assertion": "RECORDED",
        })

    # --------------------------------------------------
    # 2. ENTITY TRIPLES
    # --------------------------------------------------

    for _, row in entities.iterrows():
        patient_id = str(row["person_id"]).strip()
        entity_type = str(row["entity_type"]).strip().upper()
        entity_text = str(row["entity_text"]).strip()
        evidence = str(row["evidence"]).strip()

        if not patient_id or not entity_text:
            continue

        predicate = RELATION_MAP.get(entity_type)

        if predicate is None:
            continue

        # Only symptom negation is handled in this prototype.
        assertion = "MENTIONED"

        if entity_type == "SYMPTOM":
            if is_negated(entity_text, evidence):
                predicate = "ABSENT_SYMPTOM"
                assertion = "NEGATED"
            else:
                assertion = "PRESENT_OR_MENTIONED"

        triples.append({
            "subject": f"Patient:{patient_id}",
            "predicate": predicate,
            "object": f"{entity_type}:{entity_text}",
            "event_date": row.get("event_date", ""),
            "event_type": row.get("event_type", ""),
            "patient_id": patient_id,
            "admission_id": row.get("admission_id", ""),
            "clinical_note_id": row.get("clinical_note_id", ""),
            "evidence": evidence,
            "assertion": assertion,
        })

    # --------------------------------------------------
    # 3. SAVE
    # --------------------------------------------------

    result = pd.DataFrame(triples)

    if result.empty:
        print("No triples generated.")
        return

    result = result.drop_duplicates(
        subset=[
            "subject",
            "predicate",
            "object",
            "event_date",
            "clinical_note_id",
            "evidence",
        ]
    )

    result.to_csv(OUTPUT_PATH, index=False)

    print("\nTRIPLES GENERATED")
    print("-----------------")
    print("Total triples:", len(result))
    print("Patients:", result["patient_id"].nunique())

    print("\nRelationship distribution:")
    print(result["predicate"].value_counts().to_string())

    print("\nSample triples:")
    print(
        result[
            ["subject", "predicate", "object", "assertion"]
        ].head(10).to_string(index=False)
    )

    print("\nSaved to:", OUTPUT_PATH)


if __name__ == "__main__":
    build_triples()

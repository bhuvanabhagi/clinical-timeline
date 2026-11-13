
from pathlib import Path
import pandas as pd
import re


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRIPLES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clinical_triples.csv"
)


# --------------------------------------------------
# 2. LOAD CLINICAL TRIPLES
# --------------------------------------------------

def load_triples():

    print("Loading clinical triples...")

    if not TRIPLES_PATH.exists():
        raise FileNotFoundError(
            f"Clinical triples file not found: {TRIPLES_PATH}"
        )

    triples = pd.read_csv(TRIPLES_PATH)

    required_columns = [
        "patient_id",
        "admission_id",
        "clinical_note_id",
        "event_date",
        "event_type",
        "predicate",
        "object",
        "evidence",
        "assertion"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in triples.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print("Total triples:", len(triples))
    print("Patients:", triples["patient_id"].nunique())
    print("Clinical notes:", triples["clinical_note_id"].nunique())

    return triples


# --------------------------------------------------
# 3. PARSE EVENT DATES
# --------------------------------------------------

def parse_event_date(value):

    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    if not value:
        return pd.NaT

    if len(value) >= 10 and value[4] == "-" and value[7] == "-":

        return pd.to_datetime(
            value,
            errors="coerce",
            yearfirst=True
        )

    return pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True
    )


# --------------------------------------------------
# 4. CLEAN EVIDENCE TEXT
# --------------------------------------------------

def clean_evidence(value):

    if pd.isna(value):
        return None

    text = str(value).strip()

    # Remove repeated leading bullet characters.
    text = re.sub(
        r"^(?:\s*[-•]\s*)+",
        "",
        text
    )

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    if not text:
        return None

    return text


# --------------------------------------------------
# 5. GET UNIQUE EVIDENCE
# --------------------------------------------------

def get_unique_evidence(values):

    evidence_list = []
    seen = set()

    for value in values:

        text = clean_evidence(value)

        if text is None:
            continue

        # Case-insensitive duplicate removal.
        key = text.casefold()

        if key not in seen:
            seen.add(key)
            evidence_list.append(text)

    return evidence_list


# --------------------------------------------------
# 6. BUILD CONSOLIDATED CONCEPTS
# --------------------------------------------------

def build_concepts(note_data):

    relationship_mapping = {

        "HAS_SYMPTOM": "Symptoms",

        "ABSENT_SYMPTOM": "Absent symptoms",

        "HAS_DIAGNOSIS": "Diagnoses",

        "MENTIONS_MEDICATION": "Medications",

        "MENTIONS_TEST": "Investigations and tests",

        "MENTIONS_BODY_PART": "Body parts mentioned"

    }

    concepts = {
        category: {}
        for category in relationship_mapping.values()
    }

    entity_rows = note_data[
        note_data["predicate"].isin(
            relationship_mapping.keys()
        )
    ]

    for _, row in entity_rows.iterrows():

        predicate = str(row["predicate"])

        category = relationship_mapping[predicate]

        object_value = str(row["object"])

        assertion = str(row["assertion"]).upper().strip()

        # Extract the readable concept name.
        if ":" in object_value:
            concept_name = object_value.split(":", 1)[1]
        else:
            concept_name = object_value

        # Body parts are mentions, not confirmed findings.
        if predicate == "MENTIONS_BODY_PART":
            assertion = "MENTIONED"

        if assertion not in [
            "PRESENT",
            "ABSENT",
            "MENTIONED"
        ]:
            assertion = "UNSPECIFIED"

        # Group by concept and assertion.
        key = (concept_name, assertion)

        if key not in concepts[category]:

            concepts[category][key] = {
                "concept": concept_name,
                "assertion": assertion,
                "evidence": []
            }

        evidence = clean_evidence(row["evidence"])

        if evidence:

            if evidence not in concepts[category][key]["evidence"]:
                concepts[category][key]["evidence"].append(
                    evidence
                )

    # Convert grouped dictionaries into lists.
    final_concepts = {}

    for category, records in concepts.items():

        final_concepts[category] = list(
            records.values()
        )

    return final_concepts


# --------------------------------------------------
# 7. BUILD ONE CLINICAL NOTE
# --------------------------------------------------

def build_note_record(note_id, note_data):

    first_row = note_data.iloc[0]

    event_date = parse_event_date(
        first_row["event_date"]
    )

    # Event categories.
    category_rows = note_data[
        note_data["predicate"] == "HAS_EVENT_CATEGORY"
    ]

    event_categories = get_unique_evidence(
        category_rows["event_type"]
    )

    # Clinical concepts.
    clinical_concepts = build_concepts(note_data)

    # Supporting category evidence.
    category_evidence = get_unique_evidence(
        category_rows["evidence"]
    )

    return {

        "note_id": note_id,

        "admission_id": first_row["admission_id"],

        "event_date": event_date,

        "event_categories": event_categories,

        "clinical_concepts": clinical_concepts,

        "category_evidence": category_evidence

    }


# --------------------------------------------------
# 8. GET PATIENT TIMELINE
# --------------------------------------------------

def get_patient_timeline(patient_id, triples):

    patient_data = triples[
        triples["patient_id"].astype(str) == str(patient_id)
    ].copy()

    if patient_data.empty:
        return []

    note_links = patient_data[
        patient_data["predicate"] == "HAS_CLINICAL_NOTE"
    ]

    note_ids = get_unique_evidence(
        note_links["clinical_note_id"]
    )

    events = []

    for note_id in note_ids:

        note_data = patient_data[
            patient_data["clinical_note_id"].astype(str)
            == note_id
        ]

        if note_data.empty:
            continue

        event = build_note_record(
            note_id,
            note_data
        )

        events.append(event)

    # Chronological ordering.
    events.sort(
        key=lambda event: (
            pd.isna(event["event_date"]),
            event["event_date"]
            if pd.notna(event["event_date"])
            else pd.Timestamp.max
        )
    )

    return events


# --------------------------------------------------
# 9. DISPLAY CLINICAL CONCEPTS
# --------------------------------------------------

def display_concepts(clinical_concepts):

    for category, records in clinical_concepts.items():

        print(f"\n{category}:")

        if not records:
            print("  No extracted concepts.")
            continue

        for record in records:

            print(
                f"\n  Concept: {record['concept']}"
            )

            print(
                f"  Assertion: {record['assertion']}"
            )

            print("  Supporting evidence:")

            if record["evidence"]:

                for evidence in record["evidence"]:
                    print(f"    - {evidence}")

            else:
                print("    - Evidence unavailable")


# --------------------------------------------------
# 10. DISPLAY PATIENT TIMELINE
# --------------------------------------------------

def display_patient_timeline(patient_id, triples):

    events = get_patient_timeline(
        patient_id,
        triples
    )

    print("\n" + "=" * 85)
    print("PATIENT CLINICAL JOURNEY")
    print("=" * 85)

    print("Patient ID:", patient_id)

    if not events:
        print("No clinical notes found.")
        return

    print("Total clinical notes:", len(events))

    for index, event in enumerate(events, start=1):

        print("\n" + "-" * 85)

        print(f"CLINICAL NOTE {index}")

        print("Note ID:", event["note_id"])

        print("Admission ID:", event["admission_id"])

        event_date = event["event_date"]

        if pd.notna(event_date):

            print(
                "Date:",
                event_date.strftime("%d %b %Y, %H:%M")
            )

        else:
            print("Date: Unavailable")

        # Event categories.
        print("\nEvent categories:")

        if event["event_categories"]:

            for category in event["event_categories"]:
                print("  -", category)

        else:
            print("  No categories found.")

        # Consolidated clinical concepts.
        display_concepts(
            event["clinical_concepts"]
        )

        # Additional category evidence.
        print("\nAdditional category evidence:")

        if event["category_evidence"]:

            for evidence in event["category_evidence"]:
                print("  -", evidence)

        else:
            print("  No category evidence available.")

    print("\n" + "=" * 85)
    print("END OF PATIENT JOURNEY")
    print("=" * 85)


# --------------------------------------------------
# 11. MAIN PROGRAM
# --------------------------------------------------

def main():

    try:
        triples = load_triples()

    except (
        FileNotFoundError,
        ValueError,
        pd.errors.ParserError
    ) as error:

        print("Error:", error)
        return

    patient_ids = sorted(
        triples.loc[
            triples["predicate"] == "HAS_CLINICAL_NOTE",
            "patient_id"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    if not patient_ids:
        print("No patients found.")
        return

    print("\nCLINICAL TIMELINE EXPLORER")
    print("=" * 45)

    print("Patients available:", len(patient_ids))

    for index, patient_id in enumerate(patient_ids, start=1):

        print(f"{index}. {patient_id}")

    while True:

        choice = input(
            "\nEnter patient number (or Q to quit): "
        ).strip()

        if choice.lower() == "q":

            print("Exiting timeline explorer.")
            break

        if not choice.isdigit():

            print("Please enter a valid number.")
            continue

        patient_number = int(choice)

        if not 1 <= patient_number <= len(patient_ids):

            print("Invalid patient number. Try again.")
            continue

        selected_patient = patient_ids[
            patient_number - 1
        ]

        display_patient_timeline(
            selected_patient,
            triples
        )


# --------------------------------------------------
# 12. RUN
# --------------------------------------------------

if __name__ == "__main__":
    main()


import pandas as pd
from pathlib import Path


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "processed"

EVENTS_FILE = DATA_DIR / "clinical_events.csv"
ENTITIES_FILE = DATA_DIR / "clinical_entities.csv"
OUTPUT_FILE = DATA_DIR / "clinical_triples.csv"


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

def load_data():

    print("Loading clinical events and entities...")

    if not EVENTS_FILE.exists():
        raise FileNotFoundError(EVENTS_FILE)

    if not ENTITIES_FILE.exists():
        raise FileNotFoundError(ENTITIES_FILE)

    events = pd.read_csv(EVENTS_FILE)
    entities = pd.read_csv(ENTITIES_FILE)

    print("Clinical event records:", len(events))
    print("Clinical entity records:", len(entities))

    return events, entities


# --------------------------------------------------
# 3. VALIDATE COLUMNS
# --------------------------------------------------

def validate_data(events, entities):

    required_event_columns = [
        "person_id",
        "admission_id",
        "clinical_note_id",
        "event_date",
        "event_type",
        "event_text"
    ]

    required_entity_columns = [
        "person_id",
        "admission_id",
        "clinical_note_id",
        "entity_type",
        "entity_text",
        "evidence",
        "assertion"
    ]

    for column in required_event_columns:
        if column not in events.columns:
            raise ValueError(
                f"Missing event column: {column}"
            )

    for column in required_entity_columns:
        if column not in entities.columns:
            raise ValueError(
                f"Missing entity column: {column}"
            )


# --------------------------------------------------
# 4. INITIALIZE TRIPLES
# --------------------------------------------------

triples = []


def add_triple(
    subject,
    predicate,
    object_value,
    event_date=None,
    event_type=None,
    patient_id=None,
    admission_id=None,
    clinical_note_id=None,
    evidence=None,
    assertion="PRESENT"
):

    triples.append({

        "subject": subject,
        "predicate": predicate,
        "object": object_value,

        "event_date": event_date,
        "event_type": event_type,

        "patient_id": patient_id,
        "admission_id": admission_id,
        "clinical_note_id": clinical_note_id,

        "evidence": evidence,
        "assertion": assertion

    })


# --------------------------------------------------
# 5. PATIENT -> CLINICAL NOTE
# --------------------------------------------------

def create_patient_note_relationships(events):

    print("\nCreating patient-to-note relationships...")

    unique_notes = events.drop_duplicates(
        subset=[
            "person_id",
            "clinical_note_id"
        ]
    )

    for _, row in unique_notes.iterrows():

        patient_id = str(row["person_id"])
        note_id = str(row["clinical_note_id"])

        add_triple(

            subject=f"PATIENT:{patient_id}",

            predicate="HAS_CLINICAL_NOTE",

            object_value=f"NOTE:{note_id}",

            event_date=row["event_date"],

            patient_id=patient_id,

            admission_id=row["admission_id"],

            clinical_note_id=note_id,

            evidence=None

        )


# --------------------------------------------------
# 6. NOTE -> EVENT CATEGORY
# --------------------------------------------------

def create_event_category_relationships(events):

    print("Creating note-to-event-category relationships...")

    unique_categories = events.drop_duplicates(
        subset=[
            "person_id",
            "clinical_note_id",
            "event_type"
        ]
    )

    for _, row in unique_categories.iterrows():

        patient_id = str(row["person_id"])
        note_id = str(row["clinical_note_id"])
        event_type = str(row["event_type"])

        add_triple(

            subject=f"NOTE:{note_id}",

            predicate="HAS_EVENT_CATEGORY",

            object_value=f"EVENT:{event_type.upper()}",

            event_date=row["event_date"],

            event_type=event_type,

            patient_id=patient_id,

            admission_id=row["admission_id"],

            clinical_note_id=note_id,

            evidence=row["event_text"]

        )


# --------------------------------------------------
# 7. NOTE -> CLINICAL ENTITY
# --------------------------------------------------

def create_entity_relationships(entities):

    print("Creating note-to-entity relationships...")

    relationship_mapping = {

        "SYMPTOM": "HAS_SYMPTOM",

        "DIAGNOSIS": "HAS_DIAGNOSIS",

        "MEDICATION": "MENTIONS_MEDICATION",

        "PROCEDURE_TEST": "MENTIONS_TEST",

        "BODY_PART": "MENTIONS_BODY_PART"

    }

    for _, row in entities.iterrows():

        patient_id = str(row["person_id"])

        note_id = str(row["clinical_note_id"])

        entity_type = str(row["entity_type"]).upper()

        entity_text = str(row["entity_text"])

        evidence = row["evidence"]

        assertion = str(row["assertion"]).upper().strip()

        # ------------------------------------------
        # MAP ENTITY TO RELATIONSHIP
        # ------------------------------------------

        predicate = relationship_mapping.get(entity_type)

        if predicate is None:
            continue

        # ------------------------------------------
        # USE ASSERTION FROM ENTITY EXTRACTOR
        # ------------------------------------------

        if assertion not in ["PRESENT", "ABSENT"]:
            assertion = "PRESENT"

        # Only symptoms receive an absent relationship.
        if entity_type == "SYMPTOM" and assertion == "ABSENT":

            predicate = "ABSENT_SYMPTOM"

        elif assertion == "ABSENT":

            # Do not incorrectly mark a diagnosis,
            # medication, test or body part as absent.
            # Preserve the mention as a regular relationship.
            assertion = "PRESENT"

        # ------------------------------------------
        # CREATE TRIPLE
        # ------------------------------------------

        add_triple(

            subject=f"NOTE:{note_id}",

            predicate=predicate,

            object_value=f"{entity_type}:{entity_text.upper()}",

            patient_id=patient_id,

            admission_id=row["admission_id"],

            clinical_note_id=note_id,

            evidence=evidence,

            assertion=assertion

        )


# --------------------------------------------------
# 8. BUILD KNOWLEDGE GRAPH
# --------------------------------------------------

def build_triples(events, entities):

    global triples

    triples = []

    create_patient_note_relationships(events)

    create_event_category_relationships(events)

    create_entity_relationships(entities)

    triples_df = pd.DataFrame(triples)

    # Remove exact duplicate relationships only.
    triples_df = triples_df.drop_duplicates()

    return triples_df


# --------------------------------------------------
# 9. DISPLAY RESULTS
# --------------------------------------------------

def display_results(triples_df):

    print("\n======================================")
    print("KNOWLEDGE GRAPH TRIPLES GENERATED")
    print("======================================")

    print("\nTotal triples:", len(triples_df))

    print(
        "Unique patients:",
        triples_df["patient_id"].nunique()
    )

    print(
        "Unique clinical notes:",
        triples_df["clinical_note_id"].nunique()
    )

    print("\nRelationship distribution:")

    print(
        triples_df["predicate"].value_counts()
    )

    print("\nAssertion distribution:")

    print(
        triples_df["assertion"].value_counts()
    )

    print("\nSample triples:")

    print(
        triples_df[
            [
                "subject",
                "predicate",
                "object",
                "assertion",
                "evidence"
            ]
        ].head(10).to_string(index=False)
    )


# --------------------------------------------------
# 10. MAIN
# --------------------------------------------------

def main():

    events, entities = load_data()

    validate_data(events, entities)

    triples_df = build_triples(
        events,
        entities
    )

    triples_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    display_results(triples_df)

    print("\nOutput saved to:")
    print(OUTPUT_FILE)

    print("\nTRIPLES BUILDING COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()

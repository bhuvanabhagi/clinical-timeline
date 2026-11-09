
from pathlib import Path
import pandas as pd
import networkx as nx

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "clinical_triples.csv"


def clean_value(value):
    """Convert CSV values into safe strings."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_triples():
    print("Loading clinical triples...")

    triples = pd.read_csv(INPUT_PATH)

    required_columns = {
        "subject", "predicate", "object", "event_date",
        "event_type", "patient_id", "admission_id",
        "clinical_note_id", "evidence", "assertion"
    }

    missing = required_columns - set(triples.columns)

    if missing:
        raise ValueError(
            f"Missing columns in clinical_triples.csv: {sorted(missing)}"
        )

    print("Total triples loaded:", len(triples))
    return triples


def build_knowledge_graph(person_id):
    triples = load_triples()

    # Keep only this patient's records
    patient_triples = triples[
        triples["patient_id"].astype(str) == str(person_id)
    ].copy()

    if patient_triples.empty:
        print("No records found for this patient.")
        return

    graph = nx.MultiDiGraph()

    patient_node = f"Patient:{person_id}"
    graph.add_node(
        patient_node,
        label=f"Patient: {person_id}",
        node_type="Patient"
    )

    # Map each clinical note to its event node
    note_to_event = {}

    # Pass 1: create individual event nodes
    for index, row in patient_triples.iterrows():
        predicate = clean_value(row["predicate"])
        obj = clean_value(row["object"])

        # These rows describe a clinical event
        if predicate != "HAS_CLINICAL_EVENT":
            continue

        if not obj.startswith("Event:"):
            continue

        note_id = clean_value(row["clinical_note_id"])

        # Use note ID to distinguish events from different notes
        event_id = (
            f"EventNode:{note_id}"
            if note_id
            else f"EventNode:{index}"
        )

        event_type = clean_value(row["event_type"]) or "Other"
        event_date = clean_value(row["event_date"])
        evidence = clean_value(row["evidence"])
        assertion = clean_value(row["assertion"])
        admission_id = clean_value(row["admission_id"])

        # Short label for displaying in Gephi
        short_evidence = evidence.replace("\n", " ").strip()
        if len(short_evidence) > 65:
            short_evidence = short_evidence[:62] + "..."

        label = f"{event_type} | {event_date}"
        if short_evidence:
            label += f" | {short_evidence}"

        graph.add_node(
            event_id,
            label=label,
            node_type="Clinical Event",
            event_type=event_type,
            event_date=event_date,
            evidence=evidence,
            assertion=assertion,
            clinical_note_id=note_id,
            admission_id=admission_id
        )

        graph.add_edge(
            patient_node,
            event_id,
            label="HAS_CLINICAL_EVENT",
            relationship="HAS_CLINICAL_EVENT",
            event_date=event_date
        )

        if note_id:
            note_to_event[note_id] = event_id

    # Pass 2: add extracted clinical relationships
    for index, row in patient_triples.iterrows():
        subject = clean_value(row["subject"])
        predicate = clean_value(row["predicate"])
        obj = clean_value(row["object"])

        if not subject or not predicate or not obj:
            continue

        if predicate == "HAS_CLINICAL_EVENT":
            continue

        if subject.lower() in {"nan", "none"}:
            continue

        if obj.lower() in {"nan", "none"}:
            continue

        # Preserve the original subject and object
        graph.add_node(subject, label=subject)
        graph.add_node(obj, label=obj)

        graph.add_edge(
            subject,
            obj,
            label=predicate,
            relationship=predicate,
            event_date=clean_value(row["event_date"]),
            assertion=clean_value(row["assertion"]),
            clinical_note_id=clean_value(row["clinical_note_id"])
        )

        # Link the event to concepts extracted from the same note.
        # This means "mentioned in the note", not causation.
        note_id = clean_value(row["clinical_note_id"])

        if note_id in note_to_event:
            event_node = note_to_event[note_id]

            graph.add_edge(
                event_node,
                obj,
                label="MENTIONS_IN_NOTE",
                relationship="MENTIONS_IN_NOTE"
            )

    # Save one graph per patient
    patient_output = (
        PROCESSED_DIR / f"knowledge_graph_patient_{person_id}.gexf"
    )

    nx.write_gexf(graph, patient_output)

    print("\n" + "=" * 45)
    print("PATIENT KNOWLEDGE GRAPH CREATED")
    print("=" * 45)
    print("Patient ID:", person_id)
    print("Source rows:", len(patient_triples))
    print("Total nodes:", graph.number_of_nodes())
    print("Total relationships:", graph.number_of_edges())
    print("Saved to:", patient_output)


def main():
    triples = load_triples()

    patients = sorted(
        triples["patient_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    print("\nPATIENT KNOWLEDGE GRAPH EXPLORER")
    print("=" * 40)

    for number, patient_id in enumerate(patients, start=1):
        print(f"{number}. {patient_id}")

    while True:
        choice = input(
            "\nEnter patient number (or Q to quit): "
        ).strip()

        if choice.lower() == "q":
            print("Exiting explorer.")
            break

        if not choice.isdigit():
            print("Enter a valid number.")
            continue

        number = int(choice)

        if number < 1 or number > len(patients):
            print("Number out of range.")
            continue

        build_knowledge_graph(patients[number - 1])


if __name__ == "__main__":
    main()
